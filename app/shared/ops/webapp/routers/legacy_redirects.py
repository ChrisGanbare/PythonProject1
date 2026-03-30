"""旧版路径重定向至 Studio 控制面。"""

from __future__ import annotations

from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse

router = APIRouter(tags=["legacy redirects"])


def _with_query(base: str, request: Request) -> str:
    q = request.url.query
    return f"{base}?{q}" if q else base


@router.get("/api/agent/catalog")
def legacy_redirect_agent_catalog():
    return RedirectResponse(url="/api/studio/v1/agent/catalog", status_code=307)


@router.get("/api/agent/schema")
def legacy_redirect_agent_schema():
    return RedirectResponse(url="/api/studio/v1/agent/schema", status_code=307)


@router.post("/api/agent/compile")
def legacy_redirect_agent_compile():
    return RedirectResponse(url="/api/studio/v1/agent/compile", status_code=307)


@router.post("/api/agent/validate")
def legacy_redirect_agent_validate():
    return RedirectResponse(url="/api/studio/v1/agent/validate", status_code=307)


@router.get("/api/jobs")
def legacy_redirect_jobs_list(request: Request):
    return RedirectResponse(
        url=_with_query("/api/studio/v1/jobs", request),
        status_code=307,
    )


@router.post("/api/jobs")
def legacy_redirect_jobs_create():
    return RedirectResponse(url="/api/studio/v1/jobs", status_code=307)


@router.get("/api/jobs/{job_id}")
def legacy_redirect_job(job_id: str):
    return RedirectResponse(url=f"/api/studio/v1/jobs/{job_id}", status_code=307)


@router.get("/api/jobs/{job_id}/scene-schedule")
def legacy_redirect_scene_schedule(job_id: str):
    return RedirectResponse(
        url=f"/api/studio/v1/jobs/{job_id}/scene-schedule",
        status_code=307,
    )
