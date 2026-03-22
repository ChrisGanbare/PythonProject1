"""任务结果规范化（与控制台 / 持久化共用）。"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def normalize_scene_schedule_payload(payload: Any) -> dict[str, Any] | None:
    if not isinstance(payload, dict):
        return None

    normalized = dict(payload)
    normalized["phases"] = list(normalized.get("phases") or [])
    normalized["scenes"] = list(normalized.get("scenes") or [])
    normalized["log_lines"] = list(normalized.get("log_lines") or [])
    normalized["total_seconds"] = float(normalized.get("total_seconds") or 0.0)
    normalized["total_frames"] = int(normalized.get("total_frames") or 0)
    return normalized


def resolve_scene_schedule_path(repo_root: Path, value: str | Path | None) -> Path | None:
    if not value:
        return None
    candidate = Path(value)
    if not candidate.is_absolute():
        candidate = (repo_root / candidate).resolve()
    return candidate


def normalize_job_result(result: Any, *, repo_root: Path, job_id: str | None) -> Any:
    if not isinstance(result, dict):
        return result

    normalized_result = dict(result)
    jid = normalized_result.get("job_id") or job_id
    schedule_path_value = normalized_result.get("scene_schedule_path")
    if normalized_result.get("scene_schedule"):
        normalized_schedule = normalize_scene_schedule_payload(normalized_result.get("scene_schedule"))
        if normalized_schedule is not None:
            normalized_result["scene_schedule"] = normalized_schedule
        if jid:
            normalized_result["scene_schedule_download_url"] = f"/api/jobs/{jid}/scene-schedule"
        return normalized_result

    if not schedule_path_value:
        return normalized_result

    schedule_path = resolve_scene_schedule_path(repo_root, schedule_path_value)
    if schedule_path is None:
        return normalized_result

    if not schedule_path.exists():
        return normalized_result

    try:
        hydrated = dict(normalized_result)
        hydrated["scene_schedule_path"] = str(schedule_path)
        if jid:
            hydrated["scene_schedule_download_url"] = f"/api/jobs/{jid}/scene-schedule"
        hydrated["scene_schedule"] = normalize_scene_schedule_payload(
            json.loads(schedule_path.read_text(encoding="utf-8"))
        )
        return hydrated
    except Exception:
        return normalized_result
