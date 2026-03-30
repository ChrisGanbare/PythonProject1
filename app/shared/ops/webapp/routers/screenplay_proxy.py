"""剧本工作流代理（转发到各子项目 api）。"""

from __future__ import annotations

import importlib
import logging
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from shared.ops.webapp.state import registry

logger = logging.getLogger("dashboard")

router = APIRouter()


class ScreenplayProxyRequest(BaseModel):
    payload: dict[str, Any]


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
        raise HTTPException(
            status_code=400,
            detail=f"Project '{project_name}' does not support screenplay workflow yet",
        )
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


@router.get("/api/screenplay/{project_name}/providers")
async def get_screenplay_providers(project_name: str):
    try:
        targets = _load_screenplay_proxy_targets(project_name)
        return await targets["list_providers"]()
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Screenplay provider proxy failed: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/api/screenplay/{project_name}/preview")
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


@router.patch("/api/screenplay/{project_name}/preview")
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
