"""Validate StandardVideoJobRequest against the live ProjectRegistry."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from orchestrator.registry import ProjectRegistry

from shared.ai.agent.catalog import _load_manifest_dict
from shared.ai.agent.schemas import AgentValidateResponse, StandardVideoJobRequest


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

    # 清理未声明的 kwargs 并填入默认值
    _clean_undeclared_kwargs(project.manifest_path, req.task, req.kwargs, warnings)

    return AgentValidateResponse(valid=len(errors) == 0, errors=errors, warnings=warnings)


def _clean_undeclared_kwargs(
    manifest_path: Path,
    task_name: str,
    kwargs: dict[str, Any],
    warnings: list[str],
) -> None:
    """Manifest 中声明了 parameters 时，移除未声明的 key，并填入缺失参数的默认值。"""
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
    declared = {str(p.get("name")): p for p in params if isinstance(p, dict) and p.get("name")}
    if not declared:
        return
    
    # 填入缺失参数的默认值
    for param_name, param_info in declared.items():
        if param_name not in kwargs and "default" in param_info:
            kwargs[param_name] = param_info["default"]
    
    # 移除未声明的参数
    unknown = [k for k in list(kwargs.keys()) if k not in declared]
    for k in unknown:
        del kwargs[k]
    
    if unknown:
        warnings.append(
            f"已清理未声明的参数（{manifest_path.parent.name}:{task_name}）: "
            + ", ".join(unknown)
        )
