"""控制面 REST API v1：任务、意图会话、Agent 编译（与 /api/* 并存，本组为产品级规范路径）。"""

from __future__ import annotations

from typing import Annotated, Any, Callable

from fastapi import APIRouter, BackgroundTasks, HTTPException, Query
from pydantic import BaseModel, Field

from orchestrator.registry import ProjectRegistry
from shared.agent.catalog import build_agent_catalog
from shared.agent.schemas import (
    AgentCompileRequest,
    AgentCompileResponse,
    AgentValidateResponse,
    StandardVideoJobRequest,
)
from shared.agent.service import compile_request_body, validate_body
from shared.studio.services import intent_sessions as intent_svc
from shared.studio.services.job_lifecycle import (
    get_job_public_dict,
    list_jobs_public,
    run_render_job_task,
    schedule_render_job,
)


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
        return {"status": "ok", "component": "video-studio-control-plane", "api": "v1"}

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

    # --- Agent (canonical under v1) ---
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
