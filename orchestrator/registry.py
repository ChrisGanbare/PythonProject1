"""Project discovery and registry for subprojects."""

from __future__ import annotations

import importlib.util
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class TaskDefinition:
    name: str
    callable_path: str
    description: str = ""


@dataclass(frozen=True)
class ProjectDefinition:
    name: str
    description: str
    default_task: str
    manifest_path: Path
    tasks: dict[str, TaskDefinition]


class ProjectRegistry:
    """Discover and provide access to subprojects."""

    def __init__(self, repo_root: Path, search_roots: tuple[str, ...] = ("src", "projects")):
        self.repo_root = repo_root
        self.search_roots = search_roots
        self._projects: dict[str, ProjectDefinition] = {}
        self.load_errors: list[str] = []

    def discover(self) -> dict[str, ProjectDefinition]:
        self._projects = {}
        self.load_errors = []

        for root_name in self.search_roots:
            base = self.repo_root / root_name
            if not base.exists():
                continue

            for manifest_path in base.glob("*/project_manifest.py"):
                definition = self._load_manifest(manifest_path)
                if definition is None:
                    continue

                if definition.name in self._projects:
                    self.load_errors.append(
                        f"duplicate project name '{definition.name}' ({manifest_path})"
                    )
                    continue

                self._projects[definition.name] = definition

        return dict(self._projects)

    def list_projects(self) -> list[ProjectDefinition]:
        return [self._projects[name] for name in sorted(self._projects)]

    def get_project(self, name: str) -> ProjectDefinition | None:
        return self._projects.get(name)

    def _load_manifest(self, manifest_path: Path) -> ProjectDefinition | None:
        try:
            module_name = f"_project_manifest_{manifest_path.parent.name}"
            spec = importlib.util.spec_from_file_location(module_name, manifest_path)
            if spec is None or spec.loader is None:
                raise ValueError("cannot create import spec")

            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            raw_manifest = getattr(module, "PROJECT_MANIFEST", None)
            if raw_manifest is None:
                raise ValueError("missing PROJECT_MANIFEST")

            return self._parse_manifest(raw_manifest, manifest_path)
        except Exception as exc:
            self.load_errors.append(f"failed to load {manifest_path}: {exc}")
            return None

    def _parse_manifest(self, raw: dict[str, Any], manifest_path: Path) -> ProjectDefinition:
        name = str(raw.get("name", "")).strip()
        if not name:
            raise ValueError("manifest name is required")

        description = str(raw.get("description", "")).strip()
        default_task = str(raw.get("default_task", "")).strip()
        raw_tasks = raw.get("tasks", {})

        if not isinstance(raw_tasks, dict) or not raw_tasks:
            raise ValueError("manifest tasks must be a non-empty dict")

        parsed_tasks: dict[str, TaskDefinition] = {}
        for task_name, task_raw in raw_tasks.items():
            if not isinstance(task_raw, dict):
                raise ValueError(f"task '{task_name}' must be a dict")

            callable_path = str(task_raw.get("callable", "")).strip()
            if not callable_path:
                raise ValueError(f"task '{task_name}' missing callable")

            parsed_tasks[task_name] = TaskDefinition(
                name=task_name,
                callable_path=callable_path,
                description=str(task_raw.get("description", "")).strip(),
            )

        if not default_task:
            default_task = next(iter(parsed_tasks))

        if default_task not in parsed_tasks:
            raise ValueError(f"default_task '{default_task}' not found in tasks")

        return ProjectDefinition(
            name=name,
            description=description,
            default_task=default_task,
            manifest_path=manifest_path,
            tasks=parsed_tasks,
        )
