"""Validate StandardVideoJobRequest against the live ProjectRegistry."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from orchestrator.registry import ProjectRegistry

from shared.agent.catalog import _load_manifest_dict
from shared.agent.schemas import AgentValidateResponse, StandardVideoJobRequest


def validate_standard_request(
    req: StandardVideoJobRequest,
    registry: ProjectRegistry,
) -> AgentValidateResponse:
    errors: list[str] = []
    warnings: list[str] = []

    project = registry.get_project(req.project)
    if project is None:
        known = ", ".join(sorted(p.name for p in registry.list_projects()))
        errors.append(f"未知项目 '{req.project}'。已知: {known or '(无)'}")
        return AgentValidateResponse(valid=False, errors=errors, warnings=warnings)

    if req.task not in project.tasks:
        known = ", ".join(sorted(project.tasks))
        errors.append(f"项目 '{req.project}' 下无任务 '{req.task}'。可选: {known}")
        return AgentValidateResponse(valid=False, errors=errors, warnings=warnings)

    _warn_unknown_kwargs(project.manifest_path, req.task, req.kwargs, warnings)

    return AgentValidateResponse(valid=len(errors) == 0, errors=errors, warnings=warnings)


def _warn_unknown_kwargs(
    manifest_path: Path,
    task_name: str,
    kwargs: dict[str, Any],
    warnings: list[str],
) -> None:
    """Manifest 中声明了 parameters 时，对未声明的 key 给出警告（不视为错误）。"""
    if not manifest_path.exists():
        return
    raw = _load_manifest_dict(manifest_path)
    tasks = raw.get("tasks") if isinstance(raw.get("tasks"), dict) else {}
    tr = tasks.get(task_name) if isinstance(tasks, dict) else None
    if not isinstance(tr, dict):
        return
    params = tr.get("parameters")
    if not isinstance(params, list):
        return
    declared = {str(p.get("name")) for p in params if isinstance(p, dict) and p.get("name")}
    if not declared:
        return
    unknown = [k for k in kwargs if k not in declared]
    if unknown:
        warnings.append(
            f"以下参数未在 manifest 的 parameters 中声明（{manifest_path.parent.name}:{task_name}）: "
            + ", ".join(unknown)
            + "；仍可能被子任务接受。"
        )
