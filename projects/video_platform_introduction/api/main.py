"""FastAPI app for video_platform_introduction."""

from __future__ import annotations

from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
import uvicorn

from shared.content.ai_planner import ai_planner
from shared.content.schemas import ContentPlan
from shared.utils.logger import setup_logger
from shared.config.settings import settings
from shared.utils.time import utc_now
from video_platform_introduction.content.planner import build_video_platform_introduction_content_plan
from video_platform_introduction.content.screenplay_adapter import (
    LOCAL_SCREENPLAY_PROVIDER_DESCRIPTION,
    LOCAL_SCREENPLAY_PROVIDER_NAME,
    build_video_platform_screenplay,
    build_video_platform_screenplay_context,
    build_video_platform_screenplay_topic,
    revise_video_platform_screenplay,
)
from video_platform_introduction.models.schemas import (
    GenerateVideoRequest,
    HealthCheckResponse,
    ProviderDescriptorResponse,
    ScreenplayEditRequest,
    ScreenplayEditResponse,
    ScreenplayPreviewRequest,
    ScreenplayPreviewResponse,
)

logger = setup_logger(
    name="video_platform_introduction_api",
    log_dir=settings.log.log_dir,
    log_level=settings.log.log_level,
    log_to_file=settings.log.log_to_file,
    log_to_console=settings.log.log_to_console,
)


@asynccontextmanager
async def lifespan(_: FastAPI):
    logger.info("video_platform_introduction API startup")
    try:
        yield
    finally:
        logger.info("video_platform_introduction API shutdown")


app = FastAPI(title="当前项目的新手教程视频", version="1.0.0", lifespan=lifespan)


@app.get("/health", response_model=HealthCheckResponse)
async def health_check() -> HealthCheckResponse:
    return HealthCheckResponse(status="OK", timestamp=utc_now(), version="1.0.0", message="service is running")


@app.post("/api/content/preview", response_model=ContentPlan)
async def preview_content_plan(request: GenerateVideoRequest) -> ContentPlan:
    return build_video_platform_introduction_content_plan(request)


@app.get("/api/screenplay/providers", response_model=list[ProviderDescriptorResponse])
async def list_screenplay_providers() -> list[ProviderDescriptorResponse]:
    global_default = settings.api.screenplay_provider_default
    is_local_default = (global_default == "mock")

    provider_items = [
        ProviderDescriptorResponse(
            name=LOCAL_SCREENPLAY_PROVIDER_NAME,
            description=LOCAL_SCREENPLAY_PROVIDER_DESCRIPTION,
            supports_remote=False,
            enabled=True,
            is_default=is_local_default,
            is_fallback=False,
        )
    ]
    
    available = ai_planner.list_available_providers()
    for item in available:
        if item["name"] == LOCAL_SCREENPLAY_PROVIDER_NAME:
            continue
        
        # If the global default is something else (e.g. openai_compatible), mark it as default
        # But we only mark it if it's NOT the local one we just added (which handles the 'mock' case)
        is_default = (item["name"] == global_default)
        
        provider_items.append(
            ProviderDescriptorResponse(
                name=item["name"],
                description=str(item["description"]),
                supports_remote=bool(item["supports_remote"]),
                enabled=bool(item["enabled"]),
                is_default=is_default,
                is_fallback=bool(item["is_fallback"]),
            )
        )

    return provider_items


@app.post("/api/screenplay/preview", response_model=ScreenplayPreviewResponse)
async def preview_screenplay(request: ScreenplayPreviewRequest) -> ScreenplayPreviewResponse:
    try:
        topic = build_video_platform_screenplay_topic(request.topic)
        plan = build_video_platform_introduction_content_plan(request)
        context = build_video_platform_screenplay_context(request, plan)
        
        # Resolve provider
        provider_name = request.screenplay_provider
        if not provider_name:
            # Fallback to settings
            default_name = settings.api.screenplay_provider_default
            if default_name == "mock":
                 provider_name = LOCAL_SCREENPLAY_PROVIDER_NAME
            else:
                 provider_name = default_name

        if provider_name == LOCAL_SCREENPLAY_PROVIDER_NAME:
            screenplay = build_video_platform_screenplay(
                topic=topic,
                target_audience=request.target_audience,
                plan=plan,
                context=context,
            )
            return ScreenplayPreviewResponse(
                screenplay=screenplay,
                provider_used=LOCAL_SCREENPLAY_PROVIDER_NAME,
                requested_provider=request.screenplay_provider,
                fallback_used=False,
            )

        result = ai_planner.preview_screenplay(
            topic=topic,
            style=request.style.value,
            target_audience=request.target_audience,
            platform=request.platform.value,
            provider_name=request.screenplay_provider,
            context=context,
        )
        return ScreenplayPreviewResponse(
            screenplay=result.screenplay,
            provider_used=result.provider_used,
            requested_provider=result.requested_provider,
            fallback_used=result.fallback_used,
        )
    except Exception as exc:
        logger.error("intro screenplay preview failed: %s", exc, exc_info=True)
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.patch("/api/screenplay/preview", response_model=ScreenplayEditResponse)
async def edit_screenplay(request: ScreenplayEditRequest) -> ScreenplayEditResponse:
    try:
        provider_name = request.screenplay_provider or request.screenplay.metadata.get("provider") or LOCAL_SCREENPLAY_PROVIDER_NAME
        if provider_name == LOCAL_SCREENPLAY_PROVIDER_NAME:
            screenplay = revise_video_platform_screenplay(
                request.screenplay,
                title=request.title,
                logline=request.logline,
                edit_instruction=request.edit_instruction,
                scene_narration_overrides=request.scene_narration_overrides,
            )
            return ScreenplayEditResponse(
                screenplay=screenplay,
                provider_used=LOCAL_SCREENPLAY_PROVIDER_NAME,
                requested_provider=request.screenplay_provider,
                fallback_used=False,
                changed_scene_ids=list(request.scene_narration_overrides),
            )

        result = ai_planner.revise_screenplay(
            screenplay=request.screenplay,
            provider_name=request.screenplay_provider,
            edit_instruction=request.edit_instruction,
            title=request.title,
            logline=request.logline,
            scene_narration_overrides=request.scene_narration_overrides,
        )
        return ScreenplayEditResponse(
            screenplay=result.screenplay,
            provider_used=result.provider_used,
            requested_provider=result.requested_provider,
            fallback_used=result.fallback_used,
            changed_scene_ids=list(request.scene_narration_overrides),
        )
    except Exception as exc:
        logger.error("intro screenplay edit failed: %s", exc, exc_info=True)
        raise HTTPException(status_code=400, detail=str(exc)) from exc


def start_api_server(host: str = "0.0.0.0", port: int = 8010) -> None:
    uvicorn.run(app, host=host, port=port)
