"""项目注册表、脚手架、任务检查与后台运行 API。"""

from __future__ import annotations

import logging
import shutil
from typing import Any

from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel

from orchestrator.inspector import inspect_callable
from orchestrator.registry import ProjectDefinition
from orchestrator.scaffold import (
    REFERENCE_PROJECT_NAMES,
    delete_project_scaffold,
    generate_project_scaffold,
    sanitize_project_name,
)
from shared.ops.studio.services.job_lifecycle import (
    run_render_job_task,
    schedule_render_job,
)
from shared.ops.webapp.state import REPO_ROOT, registry

logger = logging.getLogger("dashboard")

router = APIRouter()


class RunTaskRequest(BaseModel):
    kwargs: dict[str, Any] = {}


class CreateProjectRequest(BaseModel):
    name: str
    description: str | None = None


class DeleteProjectRequest(BaseModel):
    """Body for ``POST /api/projects/delete`` (same semantics as ``DELETE /api/projects/{name}``)."""

    name: str


def _resolve_registered_project(key: str) -> ProjectDefinition | None:
    """Match registry entry by exact id, sanitized id, or case-insensitive name (Windows-friendly)."""
    key = (key or "").strip()
    if not key:
        return None
    registry.discover()
    project = registry.get_project(key)
    if project is not None:
        return project
    try:
        alt = sanitize_project_name(key)
        if alt != key:
            project = registry.get_project(alt)
            if project is not None:
                return project
    except ValueError:
        pass
    kf = key.casefold()
    for proj in registry.list_projects():
        if proj.name.casefold() == kf:
            return proj
    return None


def _perform_project_delete(raw_key: str) -> dict[str, Any]:
    """Remove ``projects/<id>/`` for a non-reference project. Raises ``HTTPException`` on failure."""
    key = (raw_key or "").strip()
    if not key:
        raise HTTPException(status_code=400, detail="empty project name")

    project = _resolve_registered_project(key)
    if project is not None:
        if project.name in REFERENCE_PROJECT_NAMES:
            raise HTTPException(
                status_code=403,
                detail="内置参考项目不可通过控制台删除；若确需移除请手动删除目录或使用 git 还原",
            )
        project_root = project.manifest_path.parent.resolve()
        projects_root = (REPO_ROOT / "app" / "projects").resolve()
        if not str(project_root).startswith(str(projects_root)) or project_root == projects_root:
            raise HTTPException(status_code=400, detail="invalid project path")
        if not project_root.exists():
            target_cf = project_root.name.casefold()
            for child in projects_root.iterdir():
                if child.is_dir() and child.name.casefold() == target_cf:
                    project_root = child.resolve()
                    break
            else:
                raise HTTPException(
                    status_code=404,
                    detail=(
                        f"项目目录不存在: {project.manifest_path.parent}（请确认磁盘上仍有该文件夹，"
                        f"或重启控制台进程后重试）"
                    ),
                )
        shutil.rmtree(project_root)
        registry.discover()
        return {
            "status": "success",
            "message": f"Project '{project.name}' removed",
            "path": str(project_root),
        }

    try:
        deleted_path = delete_project_scaffold(REPO_ROOT / "app", key)
    except FileNotFoundError:
        raise HTTPException(
            status_code=404,
            detail=(
                f"未找到项目「{key}」。若控制台刚更新过代码，请**重启** `python dashboard.py` 后再删；"
                f"若刚创建，请先点「刷新列表」。"
            ),
        ) from None
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e)) from e
    registry.discover()
    return {
        "status": "success",
        "message": f"Project '{key}' removed",
        "path": str(deleted_path),
    }


@router.get("/api/registry")
async def get_registry():
    """List all discovered projects and their tasks."""
    registry.discover()
    projects = []
    for project in registry.list_projects():
        tasks = []
        for task_name, task_def in project.tasks.items():
            tasks.append({
                "name": task_name,
                "description": task_def.description,
                "callable": task_def.callable_path,
            })

        projects.append({
            "name": project.name,
            "description": project.description,
            "default_task": project.default_task,
            "tasks": tasks,
            "capabilities": project.capabilities,
            "deletable": project.name not in REFERENCE_PROJECT_NAMES,
        })
    return {
        "projects": projects,
        "errors": registry.load_errors,
        "reference_project_names": sorted(REFERENCE_PROJECT_NAMES),
    }


@router.post("/api/projects")
async def create_project(request: CreateProjectRequest):
    """Create a new project scaffold."""
    try:
        project_path = generate_project_scaffold(REPO_ROOT / "app", request.name, request.description)
        registry.discover()
        resolved_name = project_path.name
        return {
            "status": "success",
            "message": f"Project '{resolved_name}' created successfully",
            "name": resolved_name,
            "path": str(project_path),
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except FileExistsError as e:
        raise HTTPException(status_code=409, detail=str(e)) from e
    except Exception as e:
        logger.error("Failed to create project: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}") from e


@router.delete("/api/projects/{project_name}")
async def delete_project(project_name: str):
    """Remove a user-created project directory under ``projects/``. Reference projects are protected."""
    try:
        return _perform_project_delete(project_name)
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to delete project: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/api/projects/delete")
async def delete_project_post(request: DeleteProjectRequest):
    """Same as ``DELETE /api/projects/{name}`` — use when DELETE is blocked or returns 404 (stale server)."""
    try:
        return _perform_project_delete(request.name)
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to delete project: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/api/inspect/{project_name}/{task_name}")
async def inspect_task(project_name: str, task_name: str):
    """Get parameters for a specific project task."""
    registry.discover()
    project = registry.get_project(project_name)
    if not project:
        raise HTTPException(status_code=404, detail=f"Project '{project_name}' not found")

    task_def = project.tasks.get(task_name)
    if not task_def:
        raise HTTPException(status_code=404, detail=f"Task '{task_name}' not found in project")

    try:
        info = inspect_callable(task_def.callable_path)
        info["task_description"] = task_def.description
        return info
    except Exception as e:
        logger.error("Inspection failed: %s", e)
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/api/run/{project_name}/{task_name}")
async def run_task(
    project_name: str,
    task_name: str,
    request: RunTaskRequest,
    background_tasks: BackgroundTasks,
):
    """Run a task in the background."""
    registry.discover()
    project = registry.get_project(project_name)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    if task_name not in project.tasks:
        raise HTTPException(status_code=404, detail="Task not found")

    job_id = schedule_render_job(
        project=project_name,
        task=task_name,
        kwargs=request.kwargs,
        intent_summary=None,
        template_snapshot=None,
        session_id=None,
    )
    background_tasks.add_task(run_render_job_task, job_id, project, task_name, request.kwargs)

    return {"status": "accepted", "job_id": job_id, "message": f"Task started via job {job_id}"}
