"""Task execution for discovered subprojects."""

from __future__ import annotations

import asyncio
import importlib
import inspect
import json
from typing import Any

from orchestrator.registry import ProjectDefinition


def _load_callable(callable_path: str):
    if ":" not in callable_path:
        raise ValueError(f"invalid callable path: {callable_path}")

    module_name, attr_name = callable_path.split(":", 1)
    module = importlib.import_module(module_name)
    target = getattr(module, attr_name, None)

    if target is None:
        raise ValueError(f"callable not found: {callable_path}")
    if not callable(target):
        raise ValueError(f"target is not callable: {callable_path}")

    return target


def parse_params(raw_params: list[str]) -> dict[str, Any]:
    parsed: dict[str, Any] = {}
    for item in raw_params:
        if "=" not in item:
            raise ValueError(f"invalid --param '{item}', expected key=value")

        key, raw_value = item.split("=", 1)
        key = key.strip()
        if not key:
            raise ValueError(f"invalid --param '{item}', empty key")

        value = raw_value.strip()
        try:
            parsed[key] = json.loads(value)
        except json.JSONDecodeError:
            lowered = value.lower()
            if lowered in {"true", "false"}:
                parsed[key] = lowered == "true"
            else:
                parsed[key] = value

    return parsed


def run_project_task(
    project: ProjectDefinition,
    task_name: str | None = None,
    task_kwargs: dict[str, Any] | None = None,
) -> Any:
    task_name = task_name or project.default_task
    task_kwargs = task_kwargs or {}

    task = project.tasks.get(task_name)
    if task is None:
        available = ", ".join(sorted(project.tasks))
        raise ValueError(
            f"task '{task_name}' not found in project '{project.name}'. Available: {available}"
        )

    target = _load_callable(task.callable_path)
    signature = inspect.signature(target)
    accepts_kwargs = any(
        param.kind == inspect.Parameter.VAR_KEYWORD
        for param in signature.parameters.values()
    )

    call_kwargs = task_kwargs if accepts_kwargs else {
        key: value for key, value in task_kwargs.items() if key in signature.parameters
    }

    result = target(**call_kwargs)
    if inspect.isawaitable(result):
        return asyncio.run(result)

    return result
