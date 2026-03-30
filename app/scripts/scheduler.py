"""Root dispatcher for all subprojects."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from orchestrator.scaffold import generate_project_scaffold
from orchestrator.registry import ProjectRegistry
from orchestrator.runner import parse_params, run_project_task


REPO_ROOT = Path(__file__).resolve().parent.parent.parent  # app/scripts/ → app/ → root
_APP_DIR = REPO_ROOT / "app"
PROJECTS_ROOT = _APP_DIR / "projects"
for _root in [str(PROJECTS_ROOT), str(_APP_DIR)]:
    if _root not in sys.path:
        sys.path.insert(0, _root)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Root scheduler for managing all video subprojects.",
    )
    subparsers = parser.add_subparsers(dest="command")

    subparsers.add_parser("list", help="List discovered subprojects and tasks")

    subparsers.add_parser("backends", help="List registered visualization backends and capabilities")

    run_parser = subparsers.add_parser("run", help="Run one task from one subproject")
    run_parser.add_argument("--project", required=True, help="Project name, e.g. PythonProject1")
    run_parser.add_argument("--task", help="Task name. Defaults to project's default_task")
    run_parser.add_argument(
        "--param",
        action="append",
        default=[],
        help="Task parameter as key=value. Repeat this flag for multiple params.",
    )

    run_all_parser = subparsers.add_parser("run-all", help="Run default task for all subprojects")
    run_all_parser.add_argument(
        "--stop-on-error",
        action="store_true",
        help="Stop immediately when one subproject fails",
    )

    scaffold_parser = subparsers.add_parser("scaffold", help="Generate a minimal new subproject scaffold")
    scaffold_parser.add_argument("--name", required=True, help="New project name")
    scaffold_parser.add_argument("--description", help="Optional project description")
    scaffold_parser.add_argument("--port", type=int, default=8010, help="Default FastAPI port for the scaffold")

    return parser


def print_projects(registry: ProjectRegistry) -> None:
    projects = registry.list_projects()
    if not projects:
        print("No subprojects discovered.")
        return

    print("Discovered subprojects:")
    for project in projects:
        print(f"- {project.name}: {project.description}")
        print(f"  default task: {project.default_task}")
        backends = project.capabilities.get("viz_backends", [])
        if backends:
            print(f"  viz backends: {', '.join(backends)}")
        for task_name, task in sorted(project.tasks.items()):
            desc = f" - {task.description}" if task.description else ""
            print(f"  * {task_name}: {task.callable_path}{desc}")

    if registry.load_errors:
        print("\nManifest load warnings:")
        for error in registry.load_errors:
            print(f"- {error}")


def print_backends() -> None:
    from shared.render.visualization.registry import list_backends

    backends = list_backends()
    if not backends:
        print("No visualization backends registered.")
        return

    print("Registered visualization backends:")
    for b in backends:
        name = b["name"]
        caps = b.get("capabilities", {})
        recommended = caps.get("recommended_for", [])
        print(f"\n  [{name}]")
        for key, val in caps.items():
            if key == "recommended_for":
                continue
            print(f"    {key}: {val}")
        if recommended:
            print(f"    recommended for: {', '.join(recommended)}")

    print("\nSelf-Correction feedback loop: enabled")
    from shared.render.core.self_correction import ErrorCategory

    auto = [c.value for c in ErrorCategory if c.value not in ("missing_dependency", "file_not_found", "invalid_parameter", "unknown", "manim_scene_error")]
    print(f"  auto-correctable categories: {', '.join(auto)}")


def run_single(registry: ProjectRegistry, project_name: str, task_name: str | None, raw_params: list[str]) -> int:
    project = registry.get_project(project_name)
    if project is None:
        print(f"Project '{project_name}' not found.")
        return 1

    kwargs = parse_params(raw_params)
    selected_task = task_name or project.default_task
    print(f"Running {project.name}:{selected_task} ...")
    run_project_task(project, selected_task, kwargs)
    print("Task finished.")
    return 0


def run_all(registry: ProjectRegistry, stop_on_error: bool) -> int:
    exit_code = 0

    for project in registry.list_projects():
        task_name = project.default_task
        print(f"Running {project.name}:{task_name} ...")

        try:
            run_project_task(project, task_name)
            print("Task finished.")
        except Exception as exc:
            exit_code = 1
            print(f"Task failed: {exc}")
            if stop_on_error:
                return exit_code

    return exit_code


def scaffold_project(project_name: str, description: str | None, port: int = 8010) -> int:
    project_root = generate_project_scaffold(_APP_DIR, project_name=project_name, description=description)
    print(f"Project scaffold created: {project_root}")
    return 0


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    registry = ProjectRegistry(REPO_ROOT / "app")
    registry.discover()

    command = args.command or "list"

    if command == "list":
        print_projects(registry)
        return 0
    if command == "backends":
        print_backends()
        return 0
    if command == "run":
        return run_single(registry, args.project, args.task, args.param)
    if command == "run-all":
        return run_all(registry, args.stop_on_error)
    if command == "scaffold":
        return scaffold_project(args.name, args.description, args.port)

    parser.print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
