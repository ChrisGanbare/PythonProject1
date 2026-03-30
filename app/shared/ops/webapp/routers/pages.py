"""Dashboard HTML 页面路由。"""

from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import FileResponse, JSONResponse

from shared.ops.webapp.state import REPO_ROOT

STATIC_DIR = REPO_ROOT / "web"
STATIC_DIR.mkdir(parents=True, exist_ok=True)

router = APIRouter()


@router.get("/")
async def read_index():
    """根路径 - 显示实用版 Dashboard；v2.2 展示页面可通过 /v2 访问。"""
    index_path = STATIC_DIR / "index.html"
    if not index_path.exists():
        return JSONResponse({"error": "Frontend not found"}, status_code=404)
    return FileResponse(index_path)


@router.get("/v2")
async def read_v2_index():
    """访问 v2.2 展示页面"""
    v2_path = STATIC_DIR / "v2.html"
    if not v2_path.exists():
        return JSONResponse({"error": "v2 page not found"}, status_code=404)
    return FileResponse(v2_path)


@router.get("/ai_compile.html")
async def read_ai_compile():
    """访问 AI 意图编译页面"""
    path = STATIC_DIR / "ai_compile.html"
    if not path.exists():
        return JSONResponse({"error": "Page not found"}, status_code=404)
    return FileResponse(path)


@router.get("/projects.html")
async def read_projects():
    """访问项目管理页面"""
    path = STATIC_DIR / "projects.html"
    if not path.exists():
        return JSONResponse({"error": "Page not found"}, status_code=404)
    return FileResponse(path)


@router.get("/settings-modal.html")
async def read_settings_modal():
    """访问设置模态框页面"""
    path = STATIC_DIR / "settings-modal.html"
    if not path.exists():
        return JSONResponse({"error": "Page not found"}, status_code=404)
    return FileResponse(path)


@router.get("/classic")
async def read_classic():
    """访问旧版 Dashboard"""
    path = STATIC_DIR / "index_old.html"
    if not path.exists():
        path = STATIC_DIR / "index.html"
    if not path.exists():
        return JSONResponse({"error": "Frontend not found"}, status_code=404)
    return FileResponse(path)
