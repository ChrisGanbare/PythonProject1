"""渲染任务：持久化 + 后台执行（替代内存 JOBS）。"""

from __future__ import annotations

import json
import logging
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from sqlalchemy import func, select

from orchestrator.registry import ProjectDefinition
from orchestrator.runner import run_project_task

from shared.ai.agent.schemas import StandardVideoJobRequest
from shared.render.core.self_correction import (
    CorrectionReport,
    SelfCorrectingRunner,
    classify_error,
)
from shared.ops.studio.db.base import SessionLocal, get_engine
from shared.ops.studio.db.models import RenderJob
from shared.ops.studio.job_result import normalize_job_result

logger = logging.getLogger(__name__)


def _repo_root() -> Path:
    # app/shared/ops/studio/services/job_lifecycle.py → parents[5] = workspace root
    return Path(__file__).resolve().parents[5]


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
    if job.finished_at:
        out["finished_at"] = job.finished_at.isoformat()
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
    """供 FastAPI BackgroundTasks 调用：同步执行子项目任务并写回数据库。

    启用 Self-Correction 反馈环：渲染失败时自动分类错误并对可自愈类型
    重试（字体回退、分辨率降级、超时延长等），最终将修正审计记录写入
    job result 供前端展示。
    """
    repo_root = _repo_root()
    t0 = time.monotonic()
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

    # Self-Correction runner wraps the actual task execution
    log_dir = repo_root / "runtime" / "logs"
    runner = SelfCorrectingRunner(max_retries=2, backoff_base=2.0, log_dir=log_dir)
    correction_report: CorrectionReport | None = None

    def _on_retry(attempt: int, diagnosis) -> None:
        with SessionLocal(bind=get_engine()) as session:
            job = session.get(RenderJob, job_id)
            if job:
                job.append_log(
                    f"Self-Correction: attempt {attempt} failed [{diagnosis.category.value}]. "
                    f"Auto-fix: {diagnosis.suggested_fix}"
                )
                session.commit()

    try:
        result, correction_report = runner.run(
            fn=run_project_task,
            kwargs={"project": project, "task_name": task_name, "task_kwargs": kwargs},
            error_extractor=lambda exc: str(exc),
            on_retry=_on_retry,
        )
        if isinstance(result, dict):
            result = dict(result)
            result["job_id"] = job_id
        result = normalize_job_result(result, repo_root=repo_root, job_id=job_id)

        # Attach correction report to result if retries happened
        if correction_report and correction_report.total_attempts > 0:
            result["self_correction"] = correction_report.to_dict()

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
            if correction_report and correction_report.total_attempts > 0:
                job.append_log(
                    f"Task completed with {correction_report.total_attempts} self-correction attempt(s)."
                )
            else:
                job.append_log("Task completed successfully.")
            session.commit()
        elapsed = time.monotonic() - t0
        logger.info(
            "TASK FINISHED: %s:%s. Job: %s elapsed_s=%.2f",
            project.name,
            task_name,
            job_id,
            elapsed,
        )
    except Exception as exc:
        elapsed = time.monotonic() - t0
        logger.error(
            "TASK FAILED: %s:%s. Job: %s elapsed_s=%.2f Error: %s",
            project.name,
            task_name,
            job_id,
            elapsed,
            exc,
            exc_info=True,
        )

        # Classify the final error for the user
        diagnosis = classify_error(str(exc), exc)
        error_detail = str(exc)
        correction_info: dict[str, Any] = {
            "error_category": diagnosis.category.value,
            "suggested_fix": diagnosis.suggested_fix,
            "auto_correctable": diagnosis.auto_correctable,
        }
        if correction_report and correction_report.total_attempts > 0:
            correction_info["correction_report"] = correction_report.to_dict()

        with SessionLocal(bind=get_engine()) as session:
            job = session.get(RenderJob, job_id)
            if job is None:
                return
            job.status = "failed"
            job.finished_at = datetime.now(timezone.utc)
            job.error_text = error_detail
            # Store correction info as part of result for frontend consumption
            try:
                job.result_json = json.dumps(
                    {"self_correction": correction_info}, ensure_ascii=False
                )
            except (TypeError, ValueError):
                pass
            job.append_log(f"Error: {exc!s}")
            if diagnosis.suggested_fix:
                job.append_log(f"Self-Correction diagnosis: [{diagnosis.category.value}] {diagnosis.suggested_fix}")
            session.commit()
