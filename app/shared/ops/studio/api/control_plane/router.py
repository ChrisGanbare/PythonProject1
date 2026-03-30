"""Studio 控制面 HTTP 路由工厂；挂载前缀 ``/api/studio/v1``（由主应用 ``include_router`` 指定）。

本包名 ``control_plane`` 表示「控制面」，避免与已废弃的根级 Video v1 语义混淆。
"""

from __future__ import annotations

from pathlib import Path
from typing import Annotated, Any, Callable

from fastapi import APIRouter, BackgroundTasks, HTTPException, Query
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, Field

from orchestrator.registry import ProjectRegistry
from shared.ai.agent.catalog import build_agent_catalog
from shared.ai.agent.schemas import (
    AgentCompileRequest,
    AgentCompileResponse,
    AgentValidateResponse,
    StandardVideoJobRequest,
)
from shared.ai.agent.service import compile_request_body, validate_body
from shared.ops.studio.services import intent_sessions as intent_svc
from shared.ops.studio.job_result import (
    normalize_scene_schedule_payload,
    resolve_scene_schedule_path,
)
from shared.ops.studio.services.job_lifecycle import (
    get_job_public_dict,
    list_jobs_public,
    run_render_job_task,
    schedule_render_job,
)

_REPO_ROOT = Path(__file__).resolve().parents[6]


class IntentSessionCreate(BaseModel):
    title: str | None = None
    meta: dict[str, Any] | None = None


class IntentSessionUpdate(BaseModel):
    title: str | None = None


class JobFromTemplateRequest(BaseModel):
    """使用标准模板提交异步渲染。"""

    template: StandardVideoJobRequest
    session_id: str | None = Field(default=None, description="可选，关联意图会话")


def create_v1_router(get_registry: Callable[[], ProjectRegistry]) -> APIRouter:
    router = APIRouter()

    @router.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok", "component": "video-studio-control-plane", "api": "studio-v1"}

    # --- Jobs ---
    @router.get("/jobs")
    def api_list_jobs(
        limit: Annotated[int, Query(ge=1, le=200)] = 50,
        offset: Annotated[int, Query(ge=0)] = 0,
    ) -> dict[str, Any]:
        return list_jobs_public(limit=limit, offset=offset)

    @router.get("/jobs/{job_id}")
    def api_get_job(job_id: str) -> dict[str, Any]:
        job = get_job_public_dict(job_id)
        if job is None:
            raise HTTPException(status_code=404, detail="Job not found")
        return job

    @router.get("/jobs/{job_id}/scene-schedule")
    def api_get_job_scene_schedule(job_id: str):
        job = get_job_public_dict(job_id)
        if job is None:
            raise HTTPException(status_code=404, detail="Job not found")

        result = job.get("result")
        if not isinstance(result, dict):
            raise HTTPException(status_code=404, detail="Scene schedule not available")

        schedule_path = resolve_scene_schedule_path(_REPO_ROOT, result.get("scene_schedule_path"))
        if schedule_path is not None and schedule_path.exists():
            return FileResponse(
                path=schedule_path,
                media_type="application/json",
                filename=schedule_path.name,
            )

        schedule_payload = normalize_scene_schedule_payload(result.get("scene_schedule"))
        if schedule_payload is None:
            raise HTTPException(status_code=404, detail="Scene schedule file not found")

        return JSONResponse(schedule_payload)

    @router.post("/jobs")
    def api_submit_job(
        body: JobFromTemplateRequest,
        background_tasks: BackgroundTasks,
    ) -> dict[str, Any]:
        reg = get_registry()
        reg.discover()
        v = validate_body(body.template, reg)
        if not v.valid:
            raise HTTPException(status_code=422, detail={"errors": v.errors, "warnings": v.warnings})
        project = reg.get_project(body.template.project)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        if body.template.task not in project.tasks:
            raise HTTPException(status_code=404, detail="Task not found")

        job_id = schedule_render_job(
            project=body.template.project,
            task=body.template.task,
            kwargs=body.template.kwargs,
            intent_summary=body.template.intent_summary,
            template_snapshot=body.template,
            session_id=body.session_id,
        )
        background_tasks.add_task(
            run_render_job_task,
            job_id,
            project,
            body.template.task,
            body.template.kwargs,
        )
        return {
            "status": "accepted",
            "job_id": job_id,
            "warnings": v.warnings,
            "message": f"Task started via job {job_id}",
        }

    # --- Intent sessions (NL multi-turn) ---
    @router.get("/sessions")
    def api_list_sessions(limit: int = 30) -> dict[str, Any]:
        return intent_svc.list_intent_sessions(limit=limit)

    @router.post("/sessions")
    def api_create_session(body: IntentSessionCreate) -> dict[str, str]:
        sid = intent_svc.create_intent_session(title=body.title, meta=body.meta)
        return {"session_id": sid}

    @router.get("/sessions/{session_id}")
    def api_get_session(session_id: str) -> dict[str, Any]:
        detail = intent_svc.get_intent_session_detail(session_id)
        if detail is None:
            raise HTTPException(status_code=404, detail="Session not found")
        return detail

    @router.patch("/sessions/{session_id}")
    def api_update_session(session_id: str, body: IntentSessionUpdate) -> dict[str, Any]:
        success = intent_svc.update_intent_session_title(session_id, body.title)
        if not success:
            raise HTTPException(status_code=404, detail="Session not found")
        detail = intent_svc.get_intent_session_detail(session_id)
        return detail or {}

    @router.delete("/sessions/{session_id}")
    def api_delete_session(session_id: str) -> dict[str, str]:
        success = intent_svc.delete_intent_session(session_id)
        if not success:
            # Check if session exists but is in-progress
            detail = intent_svc.get_intent_session_detail(session_id)
            if detail is not None and not detail.get("is_completed"):
                raise HTTPException(
                    status_code=409,  # Conflict
                    detail="Can only delete completed sessions; this session is still in progress"
                )
            raise HTTPException(status_code=404, detail="Session not found")
        return {"message": "Session deleted"}

    @router.post("/sessions/{session_id}/complete")
    def api_complete_session(session_id: str) -> dict[str, Any]:
        """标记会话为已完成。"""
        success = intent_svc.mark_intent_session_completed(session_id)
        if not success:
            raise HTTPException(status_code=404, detail="Session not found")
        detail = intent_svc.get_intent_session_detail(session_id)
        return detail or {}

    # --- Agent（Studio 控制面） ---
    @router.get("/agent/catalog")
    def api_agent_catalog() -> dict[str, Any]:
        reg = get_registry()
        reg.discover()
        return build_agent_catalog(reg)

    @router.get("/agent/schema")
    def api_agent_schema() -> dict[str, Any]:
        return StandardVideoJobRequest.model_json_schema()

    @router.post("/agent/compile", response_model=AgentCompileResponse)
    def api_agent_compile(body: AgentCompileRequest) -> AgentCompileResponse:
        reg = get_registry()
        reg.discover()
        return compile_request_body(body, reg)

    @router.post("/agent/validate", response_model=AgentValidateResponse)
    def api_agent_validate(req: StandardVideoJobRequest) -> AgentValidateResponse:
        reg = get_registry()
        reg.discover()
        return validate_body(req, reg)

    return router
