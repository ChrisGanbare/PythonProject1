from __future__ import annotations

import asyncio
import atexit
import errno
import importlib
import json
import logging
import os
import signal
import sys
import time
import uuid
import datetime
from contextlib import asynccontextmanager, suppress as contextlib_suppress
from pathlib import Path
from typing import Any

import uvicorn
from fastapi import BackgroundTasks, FastAPI, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from orchestrator.registry import ProjectDefinition, ProjectRegistry
from orchestrator.inspector import inspect_callable
import shutil

from orchestrator.scaffold import (
    REFERENCE_PROJECT_NAMES,
    delete_project_scaffold,
    generate_project_scaffold,
    sanitize_project_name,
)
from shared.agent.catalog import build_agent_catalog
from shared.agent.schemas import (
    AgentCompileRequest,
    AgentCompileResponse,
    AgentValidateResponse,
    StandardVideoJobRequest,
)
from shared.agent.service import compile_request_body, validate_body
from shared.code_studio import schemas as cs_schemas
from shared.code_studio import service as cs_svc
from shared.code_studio.compiler import compile_code_request
from shared.studio.api.v1.router import create_v1_router
from shared.studio.db.init import init_db
from shared.studio.job_result import (
    normalize_scene_schedule_payload,
    resolve_scene_schedule_path,
)
from shared.studio.services.job_lifecycle import (
    get_job_public_dict,
    run_render_job_task,
    schedule_render_job,
)

try:
    import openai
    import httpx
except ImportError:
    openai = None
    httpx = None

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("dashboard")

REPO_ROOT = Path(__file__).resolve().parent

# Ensure projects directory is in python path
sys.path.append(str(REPO_ROOT / "projects"))

# Global registry
registry = ProjectRegistry(REPO_ROOT)


class SettingsResponse(BaseModel):
    """Secure settings model for frontend consumption."""
    
    # Video Defaults
    video_width: int
    video_height: int
    video_fps: int
    video_total_duration: int
    
    # API Configuration (Masked to sk-****)
    openai_api_key: str | None = None
    openai_base_url: str | None = None
    openai_model: str
    pexels_api_key: str | None = None
    
    screenplay_provider_default: str


class SettingsUpdateRequest(BaseModel):
    """Payload for updating settings."""
    
    video_width: int | None = None
    video_height: int | None = None
    video_fps: int | None = None
    video_total_duration: int | None = None
    
    openai_api_key: str | None = None
    openai_base_url: str | None = None
    openai_model: str | None = None
    pexels_api_key: str | None = None
    
    screenplay_provider_default: str | None = None

class ValidateOpenAIRequest(BaseModel):
    api_key: str
    base_url: str | None = None
    model_hint: str | None = None


def _mask_secret(value: str | None) -> str | None:
    if not value or len(value) < 8:
        return None  # Do not return short secrets at all or return empty? Let's return None for unset.
    return f"{value[:3]}...{value[-4:]}"


def _update_env_file(updates: dict[str, Any]) -> None:
    """Update .env file preserving comments and structure.

    Uses an atomic write (temp-file + os.replace) to prevent data loss if the
    process crashes mid-write.
    """
    env_path = REPO_ROOT / ".env"
    lines = env_path.read_text(encoding="utf-8").splitlines() if env_path.exists() else []

    # Canonical mapping: our internal field name → .env variable name
    key_map = {
        "video_width":                 "VIDEO__WIDTH",
        "video_height":                "VIDEO__HEIGHT",
        "video_fps":                   "VIDEO__FPS",
        "video_total_duration":        "VIDEO__TOTAL_DURATION",
        "openai_api_key":              "API__OPENAI_COMPATIBLE_API_KEY",
        "openai_base_url":             "API__OPENAI_COMPATIBLE_BASE_URL",
        "openai_model":                "API__OPENAI_COMPATIBLE_MODEL",
        "pexels_api_key":              "API__PEXELS_API_KEY",
        "screenplay_provider_default": "API__SCREENPLAY_PROVIDER_DEFAULT",
    }

    new_lines: list[str] = []
    seen_keys: set[str] = set()

    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            new_lines.append(line)
            continue

        if "=" in stripped:
            key, _ = stripped.split("=", 1)
            key = key.strip()
            field = next((f for f, k in key_map.items() if k == key), None)
            if field and field in updates and updates[field] is not None:
                new_lines.append(f"{key}={updates[field]}")
                seen_keys.add(key)
            else:
                new_lines.append(line)
        else:
            new_lines.append(line)

    # Append keys not already present in the file
    for field, value in updates.items():
        env_key = key_map.get(field)
        if env_key and env_key not in seen_keys and value is not None:
            new_lines.append(f"{env_key}={value}")

    # Atomic write: write to a sibling temp file then rename into place
    import tempfile
    tmp_fd, tmp_path = tempfile.mkstemp(dir=env_path.parent, prefix=".env.tmp.")
    try:
        with os.fdopen(tmp_fd, "w", encoding="utf-8") as f:
            f.write("\n".join(new_lines))
        os.replace(tmp_path, env_path)
    except Exception:
        with contextlib_suppress(OSError):
            os.unlink(tmp_path)
        raise


def _env_truthy(name: str) -> bool:
    return os.environ.get(name, "").strip().lower() in ("1", "true", "yes", "on")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Discover projects
    logger.info("Discovering projects...")
    registry.discover()
    init_db()
    logger.info("Studio control plane database ready.")
    # 在应用完成启动流程后再打开浏览器，避免 bat/sh 里「先开页后起服务」的竞态
    if _env_truthy("DASHBOARD_OPEN_BROWSER"):
        import webbrowser

        host = os.environ.get("DASHBOARD_HOST", "127.0.0.1")
        port = int(os.environ.get("DASHBOARD_PORT", "8090"))
        url = f"http://{host}:{port}/"

        async def _open_browser_after_ready() -> None:
            await asyncio.sleep(1.0)
            try:
                webbrowser.open(url)
            except Exception as exc:  # noqa: BLE001 — 浏览器不可用时不影响服务
                logger.warning("Could not open browser (%s): %s", url, exc)

        asyncio.create_task(_open_browser_after_ready())
    yield
    # Shutdown


app = FastAPI(title="Video Project Control Center", lifespan=lifespan)

# Static dir (mounted after all API routes so /api/* is never shadowed)
STATIC_DIR = REPO_ROOT / "static"
STATIC_DIR.mkdir(parents=True, exist_ok=True)

app.include_router(create_v1_router(lambda: registry), prefix="/api/v1")


# --- API Models ---
class RunTaskRequest(BaseModel):
    kwargs: dict[str, Any] = {}


class CreateProjectRequest(BaseModel):
    name: str
    description: str | None = None


class DeleteProjectRequest(BaseModel):
    """Body for ``POST /api/projects/delete`` (same semantics as ``DELETE /api/projects/{name}``)."""

    name: str


class ScreenplayProxyRequest(BaseModel):
    payload: dict[str, Any]


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
        projects_root = (REPO_ROOT / "projects").resolve()
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
        deleted_path = delete_project_scaffold(REPO_ROOT, key)
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


def _normalize_screenplay_style(value: str | None) -> str:
    if not value:
        return "tech"
    normalized = str(value).strip().lower()
    mapping = {
        "cinematic": "tech",
        "dramatic": "news",
        "upbeat": "trendy",
        "minimal": "minimal",
        "minimalist": "minimal",
        "tech": "tech",
        "news": "news",
        "trendy": "trendy",
    }
    return mapping.get(normalized, normalized if normalized in {"minimal", "tech", "news", "trendy"} else "tech")


def _get_project_definition(project_name: str):
    registry.discover()
    project = registry.get_project(project_name)
    if project is None:
        raise HTTPException(status_code=404, detail=f"Project '{project_name}' not found")
    return project


def _ensure_screenplay_project(project_name: str):
    project = _get_project_definition(project_name)
    if not project.capabilities.get("screenplay_workflow"):
        raise HTTPException(status_code=400, detail=f"Project '{project_name}' does not support screenplay workflow yet")
    return project


def _load_screenplay_proxy_targets(project_name: str) -> dict[str, Any]:
    _ensure_screenplay_project(project_name)
    try:
        api_module = importlib.import_module(f"{project_name}.api.main")
        schemas_module = importlib.import_module(f"{project_name}.models.schemas")
        return {
            "list_providers": getattr(api_module, "list_screenplay_providers"),
            "preview": getattr(api_module, "preview_screenplay"),
            "edit": getattr(api_module, "edit_screenplay"),
            "preview_request_model": getattr(schemas_module, "ScreenplayPreviewRequest"),
            "edit_request_model": getattr(schemas_module, "ScreenplayEditRequest"),
        }
    except (ImportError, AttributeError) as exc:
        logger.error("Screenplay proxy target load failed for %s: %s", project_name, exc, exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Project '{project_name}' is marked as screenplay-capable but is missing screenplay API components",
        ) from exc


# --- API Endpoints ---
@app.get("/")
async def read_index():
    index_path = STATIC_DIR / "index.html"
    if not index_path.exists():
        return JSONResponse({"error": "Frontend not found. Please create static/index.html"}, status_code=404)
    return FileResponse(index_path)


@app.get("/api/registry")
async def get_registry():
    """List all discovered projects and their tasks."""
    # Force a refresh to ensure we see newly added projects
    registry.discover()
    projects = []
    for project in registry.list_projects():
        tasks = []
        for task_name, task_def in project.tasks.items():
            tasks.append({
                "name": task_name,
                "description": task_def.description,
                "callable": task_def.callable_path
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


@app.get("/api/agent/catalog")
async def agent_catalog():
    """供外部 Agent（如 Claude Code）读取：子项目、任务与 manifest 参数提示。"""
    registry.discover()
    return build_agent_catalog(registry)


@app.get("/api/agent/schema")
async def agent_schema():
    """StandardVideoJobRequest 的 JSON Schema（稳定契约）。"""
    return StandardVideoJobRequest.model_json_schema()


@app.post("/api/agent/compile", response_model=AgentCompileResponse)
async def agent_compile(body: AgentCompileRequest):
    """自然语言（及可选上一版模板）→ 标准任务模板；需配置 OpenAI 兼容 API。"""
    registry.discover()
    return compile_request_body(body, registry)


@app.post("/api/agent/validate", response_model=AgentValidateResponse)
async def agent_validate(req: StandardVideoJobRequest):
    """校验标准模板是否可被当前注册表执行。"""
    registry.discover()
    return validate_body(req, registry)


@app.post("/api/agent/run")
async def agent_run_standard(body: StandardVideoJobRequest, background_tasks: BackgroundTasks):
    """使用标准模板异步触发渲染（等价于 ``POST /api/run/{project}/{task}`` + kwargs）。"""
    registry.discover()
    v = validate_body(body, registry)
    if not v.valid:
        raise HTTPException(status_code=422, detail={"errors": v.errors, "warnings": v.warnings})
    project = registry.get_project(body.project)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    if body.task not in project.tasks:
        raise HTTPException(status_code=404, detail="Task not found")

    job_id = schedule_render_job(
        project=body.project,
        task=body.task,
        kwargs=body.kwargs,
        intent_summary=body.intent_summary,
        template_snapshot=body,
        session_id=None,
    )
    background_tasks.add_task(run_render_job_task, job_id, project, body.task, body.kwargs)
    return {
        "status": "accepted",
        "job_id": job_id,
        "warnings": v.warnings,
        "message": f"Task started via job {job_id}",
    }


@app.get("/api/settings", response_model=SettingsResponse)
async def get_settings():
    """Get global settings with masked secrets."""
    from shared.config.settings import settings
    
    # Decide which OpenAI key to show. Prefer compatible key if set, else standard.
    # Actually, let's just expose the one we recommend using: openai_compatible_api_key
    
    return SettingsResponse(
        video_width=settings.video.width,
        video_height=settings.video.height,
        video_fps=settings.video.fps,
        video_total_duration=settings.video.total_duration,
        
        openai_api_key=_mask_secret(settings.api.openai_compatible_api_key),
        # Do not mask base_url, it is not a secret and masking causes issues with validation/client instantiation
        openai_base_url=settings.api.openai_compatible_base_url,
        openai_model=settings.api.openai_compatible_model,
        pexels_api_key=_mask_secret(settings.api.pexels_api_key),
        
        screenplay_provider_default=settings.api.screenplay_provider_default,
    )


@app.get("/api/settings/reveal-keys")
async def reveal_keys():
    """Return unmasked API keys for local display. Localhost-only tool."""
    from shared.config.settings import settings
    return {
        "openai_api_key": settings.api.openai_compatible_api_key or "",
        "pexels_api_key": settings.api.pexels_api_key or "",
    }


@app.put("/api/settings")
async def update_settings(request: SettingsUpdateRequest):
    """Update global settings and persist to .env."""
    from shared.config.settings import settings
    
    updates = {}
    
    # Video
    if request.video_width is not None:
        settings.video.width = request.video_width
        updates["video_width"] = request.video_width
    if request.video_height is not None:
        settings.video.height = request.video_height
        updates["video_height"] = request.video_height
    if request.video_fps is not None:
        settings.video.fps = request.video_fps
        updates["video_fps"] = request.video_fps
    if request.video_total_duration is not None:
        settings.video.total_duration = request.video_total_duration
        updates["video_total_duration"] = request.video_total_duration

    # API
    # Only update secrets if they don't look like masks (e.g. sk-***)
    if request.openai_api_key and "..." not in request.openai_api_key:
        settings.api.openai_compatible_api_key = request.openai_api_key
        updates["openai_api_key"] = request.openai_api_key
        
    if request.openai_base_url and "..." not in request.openai_base_url:
        settings.api.openai_compatible_base_url = request.openai_base_url
        updates["openai_base_url"] = request.openai_base_url
        
    if request.openai_model:
        settings.api.openai_compatible_model = request.openai_model
        updates["openai_model"] = request.openai_model
        
    if request.pexels_api_key and "..." not in request.pexels_api_key:
        settings.api.pexels_api_key = request.pexels_api_key
        updates["pexels_api_key"] = request.pexels_api_key

    if request.screenplay_provider_default:
        settings.api.screenplay_provider_default = request.screenplay_provider_default
        updates["screenplay_provider_default"] = request.screenplay_provider_default

    try:
        _update_env_file(updates)
    except Exception as e:
        logger.error(f"Failed to persist settings to .env: {e}")
        from fastapi import HTTPException
        raise HTTPException(status_code=500, detail=f"配置已更新至内存，但写入 .env 文件失败：{e}")

    return {"status": "success", "message": "Settings updated", "updated_keys": list(updates.keys())}


@app.post("/api/settings/validate-openai")
async def validate_openai(request: ValidateOpenAIRequest):
    """Validate OpenAI API Key and list available models."""
    if not openai:
        return {
            "valid": False,
            "error": "OpenAI library not installed on server"
        }

    api_key = request.api_key
    base_url = request.base_url
    
    # Clean up base_url if provided
    if base_url:
        base_url = base_url.strip()
        # Warn if trailing slash might be an issue (OpenAI client handles it, but good to normalize)
        if base_url.endswith("/"):
            base_url = base_url[:-1]

    # If the user is sending a masked key (starts with sk-...), we might need to use the one from settings
    # But usually validation is done on the input value.
    # If input value is masked "sk-...", we can't validate it unless we assume it's the stored one.
    # Let's assume the user sends the actual key or we check if it matches the mask pattern and use stored.
    
    try:
        from shared.config.settings import settings
        stored_key = settings.api.openai_compatible_api_key
        
        if api_key.startswith("sk-") and "..." in api_key and stored_key:
            # It's likely a mask, and if it matches the mask of stored key, use stored key.
            # _mask_secret implementation: first 3, last 4.
            if len(api_key) > 7 and stored_key.startswith(api_key[:3]) and stored_key.endswith(api_key[-4:]):
                api_key = stored_key

        # Same for base_url? Base URL usually isn't masked, but our code masks it if it's a secret? 
        # SettingsResponse masks base_url.
        stored_url = settings.api.openai_compatible_base_url
        if base_url and "..." in base_url and stored_url:
            # weak check
            if len(base_url) > 7 and stored_url.startswith(base_url[:3]) and stored_url.endswith(base_url[-4:]):
                base_url = stored_url
        
        logger.info(f"Validating OpenAI connection. Base URL: {base_url or 'Default (Official)'}")

        # Create client with timeout to fail faster
        client_kwargs = {"api_key": api_key, "timeout": 10.0}
        if base_url:
            client_kwargs["base_url"] = base_url
            
        client = openai.OpenAI(**client_kwargs)
        
        models = []
        try:
            # List models
            logger.info("Attempting to list models...")
            response = client.models.list()
            # Sort models, maybe prioritize gpt-4, gpt-3.5
            models = sorted([m.id for m in response.data])
            logger.info(f"Successfully listed models: {len(models)} found")
        except Exception as list_err:
            err_str = str(list_err)
            is_404 = "404" in err_str or (
                hasattr(list_err, "status_code") and list_err.status_code == 404
            )
            logger.warning(f"Failed to list models: {list_err}")

            # 404 means provider doesn't support /models endpoint (normal for many providers)
            # Try verifying with the user-supplied model name instead
            test_model = (request.model_hint or "").strip()
            if test_model:
                try:
                    client.chat.completions.create(
                        model=test_model,
                        messages=[{"role": "user", "content": "hi"}],
                        max_tokens=1
                    )
                    logger.info(f"Fallback generation successful with model '{test_model}'")
                    models = [test_model]
                except Exception as gen_err:
                    logger.error(f"Fallback generation also failed: {gen_err}")
                    gen_str = str(gen_err)
                    is_model_404 = "404" in gen_str or (
                        hasattr(gen_err, "status_code") and gen_err.status_code == 404
                    )
                    if is_model_404:
                        friendly = (
                            f"模型 '{test_model}' 不存在或名称有误，请在模型名称字段填写正确的 Model ID 后重试。"
                            f"（如使用 DashScope，可填写 qwen-turbo / qwen-plus / qwen-max 等）"
                        )
                    else:
                        friendly = f"接口验证失败：{gen_str}"
                    return {
                        "valid": False,
                        "error": friendly,
                        "details": f"List Models: {list_err}; Generation Check: {gen_err}"
                    }
            else:
                if is_404:
                    # Provider doesn't expose /models but credentials may still be OK.
                    # Return valid=True with empty list so user can type model ID manually.
                    logger.info("Provider returned 404 on /models; returning valid=True with empty list.")
                    models = []
                else:
                    return {
                        "valid": False,
                        "error": f"获取模型列表失败：{err_str}（请填写模型名称后再试）",
                        "details": err_str
                    }

        return {
            "valid": True,
            "message": "Connection successful",
            "models": models
        }
    except Exception as e:
        logger.warning(f"OpenAI validation failed: {str(e)}")
        msg = str(e)
        # 优先给出人性化提示
        if "404" in msg:
            model_hint = (request.model_hint or "").strip()
            if model_hint:
                return {
                    "valid": False,
                    "error": (
                        f"模型 '{model_hint}' 不存在或名称有误，请在模型名称字段填写正确的 Model ID 后重试。"
                        "（如使用 DashScope，可填写 qwen-turbo / qwen-plus / qwen-max 等）"
                    )
                }
            else:
                return {"valid": False, "error": "接口地址不支持该操作（404），请检查 Base URL 是否正确。"}
        if "timeout" in msg.lower() and (not request.base_url or not request.base_url.strip()):
             msg = "请求超时——是否忘记填写 Base URL？"
        elif "connection" in msg.lower() or "connect" in msg.lower():
             msg = f"无法连接至 {request.base_url}，请检查地址和网络。"
        return {
            "valid": False,
            "error": msg
        }

@app.post("/api/projects")
async def create_project(request: CreateProjectRequest):
    """Create a new project scaffold."""
    try:
        project_path = generate_project_scaffold(REPO_ROOT, request.name, request.description)
        # Refresh registry to pick up the new project
        registry.discover()
        resolved_name = project_path.name
        return {
            "status": "success",
            "message": f"Project '{resolved_name}' created successfully",
            "name": resolved_name,
            "path": str(project_path),
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except FileExistsError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to create project: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")


@app.delete("/api/projects/{project_name}")
async def delete_project(project_name: str):
    """Remove a user-created project directory under ``projects/``. Reference projects are protected."""
    try:
        return _perform_project_delete(project_name)
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to delete project: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.post("/api/projects/delete")
async def delete_project_post(request: DeleteProjectRequest):
    """Same as ``DELETE /api/projects/{name}`` — use when DELETE is blocked or returns 404 (stale server)."""
    try:
        return _perform_project_delete(request.name)
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to delete project: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.get("/api/inspect/{project_name}/{task_name}")
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
        # Introspect the callable
        info = inspect_callable(task_def.callable_path)
        # Add tasks metadata
        info["task_description"] = task_def.description
        return info
    except Exception as e:
        logger.error(f"Inspection failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/screenplay/{project_name}/providers")
async def get_screenplay_providers(project_name: str):
    try:
        targets = _load_screenplay_proxy_targets(project_name)
        return await targets["list_providers"]()
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Screenplay provider proxy failed: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/api/screenplay/{project_name}/preview")
async def preview_screenplay_proxy(project_name: str, request: ScreenplayProxyRequest):
    try:
        targets = _load_screenplay_proxy_targets(project_name)

        payload = dict(request.payload)
        payload["style"] = _normalize_screenplay_style(payload.get("style"))
        if "video_duration" not in payload and payload.get("duration") is not None:
            payload["video_duration"] = payload["duration"]
        model = targets["preview_request_model"].model_validate(payload)
        return await targets["preview"](model)
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Screenplay preview proxy failed: %s", exc, exc_info=True)
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.patch("/api/screenplay/{project_name}/preview")
async def edit_screenplay_proxy(project_name: str, request: ScreenplayProxyRequest):
    try:
        targets = _load_screenplay_proxy_targets(project_name)
        model = targets["edit_request_model"].model_validate(request.payload)
        return await targets["edit"](model)
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Screenplay edit proxy failed: %s", exc, exc_info=True)
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/api/jobs/{job_id}")
async def get_job_status(job_id: str):
    """Get the status of a background job."""
    job = get_job_public_dict(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@app.get("/api/jobs/{job_id}/scene-schedule")
async def download_job_scene_schedule(job_id: str):
    job = get_job_public_dict(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")

    result = job.get("result")
    if not isinstance(result, dict):
        raise HTTPException(status_code=404, detail="Scene schedule not available")

    schedule_path = resolve_scene_schedule_path(REPO_ROOT, result.get("scene_schedule_path"))
    if schedule_path is not None and schedule_path.exists():
        return FileResponse(
            path=schedule_path,
            media_type="application/json",
            filename=schedule_path.name,
        )

    schedule_payload = normalize_scene_schedule_payload(result.get("scene_schedule"))
    if schedule_payload is None:
        raise HTTPException(status_code=404, detail="Scene schedule file not found")

    return JSONResponse(schedule_payload)


@app.post("/api/run/{project_name}/{task_name}")
async def run_task(project_name: str, task_name: str, request: RunTaskRequest, background_tasks: BackgroundTasks):
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


# ---------------------------------------------------------------------------
# Code Studio API
# ---------------------------------------------------------------------------


@app.post("/api/code-studio/sessions")
def cs_create_session(body: cs_schemas.CreateCodeSessionRequest):
    """创建代码工坊会话。"""
    # 校验项目存在
    registry.discover()
    if not registry.get_project(body.project_name):
        raise HTTPException(status_code=404, detail=f"Project '{body.project_name}' not found")
    session_id = cs_svc.create_code_session(
        project_name=body.project_name,
        task_name=body.task_name,
        title=body.title,
    )
    return {"session_id": session_id}


@app.get("/api/code-studio/sessions")
def cs_list_sessions(
    project_name: str | None = None,
    task_name: str | None = None,
    limit: int = 30,
):
    """列举代码工坊会话，可按 project_name / task_name 过滤。"""
    return cs_svc.list_code_sessions(
        project_name=project_name,
        task_name=task_name,
        limit=limit,
    )


@app.get("/api/code-studio/sessions/{session_id}")
def cs_get_session(session_id: str):
    """获取会话详情（含所有轮次）。"""
    detail = cs_svc.get_code_session_detail(session_id)
    if detail is None:
        raise HTTPException(status_code=404, detail="Code session not found")
    return detail


@app.delete("/api/code-studio/sessions/{session_id}")
def cs_delete_session(session_id: str):
    """删除会话及其所有轮次。"""
    ok = cs_svc.delete_code_session(session_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Code session not found")
    return {"deleted": session_id}


@app.post("/api/code-studio/sessions/{session_id}/compile", response_model=cs_schemas.CodeCompileResponse)
def cs_compile(session_id: str, body: cs_schemas.CodeCompileRequest):
    """自然语言 → 代码补丁（不写入磁盘，只存 DB）。"""
    detail = cs_svc.get_code_session_detail(session_id)
    if detail is None:
        raise HTTPException(status_code=404, detail="Code session not found")

    project_name = detail["project_name"]
    project_root = REPO_ROOT / "projects" / project_name
    if not project_root.is_dir():
        raise HTTPException(status_code=404, detail=f"Project directory not found: {project_name}")

    # 持久化用户轮次
    cs_svc.append_user_turn(session_id, body.prompt)

    # 获取历史对话（最近 10 轮）
    history = cs_svc.get_recent_turns_for_context(session_id, n=10)

    # 调用 AI 编译
    result = compile_code_request(
        body.prompt,
        project_root,
        previous_turns=history,
        file_hint=body.file_hint,
    )

    if result.success and result.patch:
        patch = result.patch
        cs_svc.append_assistant_turn(
            session_id,
            explanation=patch.explanation,
            file_path=patch.file_path,
            code_patch=patch.new_content,
        )

    return result


@app.post("/api/code-studio/sessions/{session_id}/apply", response_model=cs_schemas.ApplyPatchResponse)
def cs_apply_patch(session_id: str, body: cs_schemas.ApplyPatchRequest):
    """将指定 turn 的代码补丁写入磁盘。"""
    if not body.confirm:
        raise HTTPException(status_code=400, detail="confirm 必须为 true 才会执行写入")

    detail = cs_svc.get_code_session_detail(session_id)
    if detail is None:
        raise HTTPException(status_code=404, detail="Code session not found")

    project_name = detail["project_name"]
    project_root = REPO_ROOT / "projects" / project_name
    if not project_root.is_dir():
        raise HTTPException(status_code=404, detail=f"Project directory not found: {project_name}")

    ok, msg = cs_svc.apply_patch(body.turn_id, project_root)
    if ok:
        return cs_schemas.ApplyPatchResponse(success=True, written_path=msg)
    return cs_schemas.ApplyPatchResponse(success=False, error=msg)


# Mount static assets after all API routes so `/api/...` is never captured by the static app.
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


def _is_address_in_use(exc: OSError) -> bool:
    if exc.errno == errno.EADDRINUSE:
        return True
    # Windows: 通常只有 winerror，errno 可能为 0
    return getattr(exc, "winerror", None) == 10048


# PID 文件：运行时目录，gitignore 已覆盖
_PID_FILE = REPO_ROOT / "runtime" / "dashboard.pid"


def _stop_previous_instance() -> None:
    """若 PID 文件存在且对应进程仍在运行，终止它并等待端口释放。"""
    if not _PID_FILE.exists():
        return
    try:
        old_pid = int(_PID_FILE.read_text(encoding="utf-8").strip())
    except (ValueError, OSError):
        with contextlib_suppress(OSError):
            _PID_FILE.unlink()
        return
    if old_pid == os.getpid():
        return
    try:
        os.kill(old_pid, 0)  # 探测：进程不存在时抛 OSError
    except (OSError, SystemError):
        return  # 进程已不存在，残留 PID 文件，直接忽略
    logger.info("Stopping previous dashboard instance (PID %d) ...", old_pid)
    try:
        os.kill(old_pid, signal.SIGTERM)  # Windows 等同于 TerminateProcess
        for _ in range(30):               # 最多等待 3 秒
            time.sleep(0.1)
            try:
                os.kill(old_pid, 0)
            except OSError:
                break  # 进程已退出
        else:
            logger.warning("Previous instance (PID %d) did not exit within 3 s.", old_pid)
    except OSError:
        pass


def _register_pid_file() -> None:
    """写入当前进程 PID，atexit 时自动删除。"""
    _PID_FILE.parent.mkdir(parents=True, exist_ok=True)
    _PID_FILE.write_text(str(os.getpid()), encoding="utf-8")
    atexit.register(lambda: _PID_FILE.unlink(missing_ok=True))


def run_dashboard() -> None:
    """Console entry (`video-dashboard` after `pip install -e .`)."""
    host = os.environ.get("DASHBOARD_HOST", "127.0.0.1")
    port = int(os.environ.get("DASHBOARD_PORT", "8090"))
    _stop_previous_instance()  # 自动停止上一个实例
    _register_pid_file()       # 记录本次 PID
    print(f"Starting Video Control Center on http://{host}:{port} ...")
    try:
        uvicorn.run(app, host=host, port=port)
    except OSError as exc:
        if _is_address_in_use(exc):
            print(
                f"端口 {port} 仍被占用（等待超时），请手动关闭后重试，"
                f"或设置环境变量 DASHBOARD_PORT 使用其他端口。",
                file=sys.stderr,
            )
        raise


if __name__ == "__main__":
    run_dashboard()
