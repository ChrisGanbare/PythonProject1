"""Machine-readable project/task catalog for Agent prompts and GET /api/agent/catalog."""

from __future__ import annotations

import importlib.util
from pathlib import Path
from typing import Any

from orchestrator.registry import ProjectDefinition, ProjectRegistry


def _load_manifest_dict(manifest_path: Path) -> dict[str, Any]:
    module_name = f"_agent_catalog_{manifest_path.parent.name}"
    spec = importlib.util.spec_from_file_location(module_name, manifest_path)
    if spec is None or spec.loader is None:
        return {}
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    raw = getattr(module, "PROJECT_MANIFEST", None)
    return raw if isinstance(raw, dict) else {}


def build_agent_catalog(registry: ProjectRegistry) -> dict[str, Any]:
    """供 LLM 与外部 Agent 使用的目录（项目、任务、参数提示）。"""
    registry.discover()
    projects_out: list[dict[str, Any]] = []
    for proj in registry.list_projects():
        raw = _load_manifest_dict(proj.manifest_path)
        raw_tasks = raw.get("tasks") if isinstance(raw.get("tasks"), dict) else {}
        tasks_out: list[dict[str, Any]] = []
        for task_name, task_def in sorted(proj.tasks.items()):
            entry: dict[str, Any] = {
                "name": task_name,
                "description": task_def.description,
                "callable": task_def.callable_path,
            }
            tr = raw_tasks.get(task_name) if isinstance(raw_tasks, dict) else None
            if isinstance(tr, dict) and "parameters" in tr:
                entry["parameters"] = tr["parameters"]
            tasks_out.append(entry)
        projects_out.append(
            {
                "name": proj.name,
                "description": proj.description,
                "default_task": proj.default_task,
                "capabilities": proj.capabilities,
                "tasks": tasks_out,
            }
        )
    return {
        "schema_version": "1.0",
        "projects": projects_out,
    }
