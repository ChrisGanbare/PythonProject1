"""渲染任务：持久化 + 后台执行（替代内存 JOBS）。"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from sqlalchemy import func, select

from orchestrator.registry import ProjectDefinition
from orchestrator.runner import run_project_task

from shared.agent.schemas import StandardVideoJobRequest
from shared.studio.db.base import SessionLocal, get_engine
from shared.studio.db.models import RenderJob
from shared.studio.job_result import normalize_job_result

logger = logging.getLogger(__name__)


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def schedule_render_job(
    *,
    project: str,
    task: str,
    kwargs: dict[str, Any],
    intent_summary: str | None = None,
    template_snapshot: StandardVideoJobRequest | None = None,
    session_id: str | None = None,
) -> str:
    """创建 pending 任务并返回 job_id。"""
    snap = None
    if template_snapshot is not None:
        snap = template_snapshot.model_dump_json()
    with SessionLocal(bind=get_engine()) as session:
        job = RenderJob(
            project=project,
            task=task,
            kwargs_json=json.dumps(kwargs, ensure_ascii=False),
            status="pending",
            intent_summary=intent_summary,
            template_snapshot_json=snap,
            session_id=session_id,
        )
        session.add(job)
        session.commit()
        job_id = job.id
    return job_id


def _job_to_public_dict(job: RenderJob) -> dict[str, Any]:
    out: dict[str, Any] = {
        "status": job.status,
        "project": job.project,
        "task": job.task,
        "created_at": job.created_at.isoformat() if job.created_at else None,
        "log": job.log_list(),
    }
    if job.intent_summary:
        out["intent_summary"] = job.intent_summary
    if job.result_json:
        try:
            out["result"] = json.loads(job.result_json)
        except json.JSONDecodeError:
            out["result"] = job.result_json
    if job.error_text:
        out["error"] = job.error_text
    return out


def get_job_public_dict(job_id: str) -> dict[str, Any] | None:
    with SessionLocal(bind=get_engine()) as session:
        job = session.get(RenderJob, job_id)
        if job is None:
            return None
        data = _job_to_public_dict(job)
        if "result" in data and isinstance(data["result"], dict):
            data["result"] = normalize_job_result(
                data["result"],
                repo_root=_repo_root(),
                job_id=job_id,
            )
            data["result"]["job_id"] = job_id
    return data


def list_jobs_public(*, limit: int = 50, offset: int = 0) -> dict[str, Any]:
    limit = max(1, min(limit, 200))
    offset = max(0, offset)
    with SessionLocal(bind=get_engine()) as session:
        total = session.scalar(select(func.count()).select_from(RenderJob)) or 0
        rows = session.scalars(
            select(RenderJob)
            .order_by(RenderJob.created_at.desc())
            .offset(offset)
            .limit(limit)
        ).all()
    items = []
    for job in rows:
        d = _job_to_public_dict(job)
        d["id"] = job.id
        if "result" in d and isinstance(d["result"], dict):
            d["result"] = normalize_job_result(d["result"], repo_root=_repo_root(), job_id=job.id)
        items.append(d)
    return {"total": total, "limit": limit, "offset": offset, "items": items}


def run_render_job_task(
    job_id: str,
    project: ProjectDefinition,
    task_name: str,
    kwargs: dict[str, Any],
) -> None:
    """供 FastAPI BackgroundTasks 调用：同步执行子项目任务并写回数据库。"""
    repo_root = _repo_root()
    logger.info("STARTING TASK: %s:%s (Job: %s)", project.name, task_name, job_id)

    with SessionLocal(bind=get_engine()) as session:
        job = session.get(RenderJob, job_id)
        if job is None:
            logger.error("Job %s not found in database", job_id)
            return
        job.status = "running"
        job.started_at = datetime.now(timezone.utc)
        job.append_log(f"Task started at {datetime.now(timezone.utc).isoformat()}")
        session.commit()

    try:
        result = run_project_task(project, task_name, kwargs)
        if isinstance(result, dict):
            result = dict(result)
            result["job_id"] = job_id
        result = normalize_job_result(result, repo_root=repo_root, job_id=job_id)

        with SessionLocal(bind=get_engine()) as session:
            job = session.get(RenderJob, job_id)
            if job is None:
                return
            job.status = "success"
            job.finished_at = datetime.now(timezone.utc)
            try:
                job.result_json = json.dumps(result, ensure_ascii=False, default=str)
            except (TypeError, ValueError):
                job.result_json = json.dumps(str(result), ensure_ascii=False)
            job.append_log("Task completed successfully.")
            session.commit()
        logger.info("TASK FINISHED: %s:%s. Job: %s", project.name, task_name, job_id)
    except Exception as exc:
        logger.error("TASK FAILED: %s:%s. Error: %s", project.name, task_name, exc, exc_info=True)
        with SessionLocal(bind=get_engine()) as session:
            job = session.get(RenderJob, job_id)
            if job is None:
                return
            job.status = "failed"
            job.finished_at = datetime.now(timezone.utc)
            job.error_text = str(exc)
            job.append_log(f"Error: {exc!s}")
            session.commit()
