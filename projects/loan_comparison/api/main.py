"""FastAPI app for loan_comparison project."""

from __future__ import annotations

import json
import sys
from contextlib import asynccontextmanager
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

# Allow direct execution: `python projects/loan_comparison/api/main.py`
if __package__ in (None, ""):
    _projects_root = Path(__file__).resolve().parents[2]   # projects/
    _workspace_root = Path(__file__).resolve().parents[3]  # video_project/
    for _p in [str(_projects_root), str(_workspace_root)]:
        if _p not in sys.path:
            sys.path.insert(0, _p)

from fastapi import BackgroundTasks, FastAPI, HTTPException, Query
from fastapi.responses import FileResponse
import uvicorn

from shared.assets.registry import asset_manager
from shared.config.settings import settings
from shared.content.ai_planner import ai_planner
from shared.content.render_mapping import build_render_expression
from shared.content.schemas import ContentPlan
from shared.content.screenplay_subtitles import screenplay_to_subtitle_items
from shared.content.screenplay_validate import ScreenplayValidationError, validate_screenplay_for_approval
from shared.core.task_manager import ProgressTracker, TaskManager
from shared.library.render_manifest import (
    build_render_manifest_payload,
    collect_asset_ids_from_screenplay,
    write_render_manifest,
)
from shared.library.screenplay_store import ScreenplayStore, ScriptVersionStatus
from shared.media.video_editor import VideoEditor
from shared.utils.logger import setup_logger
from shared.utils.time import utc_now
from shared.visualization.registry import default_backend_name

if __package__ in (None, ""):
    from loan_comparison.content.planner import build_loan_content_plan
    from loan_comparison.content.screenplay_adapter import build_loan_screenplay_context, build_loan_screenplay_topic
    from loan_comparison.models.loan import LoanData
    from loan_comparison.models.schemas import (
        AssetListItem,
        GenerateVideoRequest,
        HealthCheckResponse,
        LoanSummaryResponse,
        ProviderDescriptorResponse,
        ScreenplayEditRequest,
        ScreenplayEditResponse,
        ScreenplayPreviewRequest,
        ScreenplayPreviewResponse,
        ScriptCreateRequest,
        ScriptCreateResponse,
        ScriptRefineRequest,
        ScriptVersionCreateRequest,
        VideoProgressResponse,
        VideoResultResponse,
        VideoTaskResponse,
        TaskStatus,
    )
    from loan_comparison.renderer.animation import ContentEngine, resolve_scene_schedule_sidecar_path
else:
    from ..content.planner import build_loan_content_plan
    from ..content.screenplay_adapter import build_loan_screenplay_context, build_loan_screenplay_topic
    from ..models.loan import LoanData
    from ..models.schemas import (
        AssetListItem,
        GenerateVideoRequest,
        HealthCheckResponse,
        LoanSummaryResponse,
        ProviderDescriptorResponse,
        ScreenplayEditRequest,
        ScreenplayEditResponse,
        ScreenplayPreviewRequest,
        ScreenplayPreviewResponse,
        ScriptCreateRequest,
        ScriptCreateResponse,
        ScriptRefineRequest,
        ScriptVersionCreateRequest,
        VideoProgressResponse,
        VideoResultResponse,
        VideoTaskResponse,
        TaskStatus,
    )
    from ..renderer.animation import ContentEngine, resolve_scene_schedule_sidecar_path


logger = setup_logger(
    name="video_api",
    log_dir=settings.log.log_dir,
    log_level=settings.log.log_level,
    log_to_file=settings.log.log_to_file,
    log_to_console=settings.log.log_to_console,
)

task_manager = TaskManager()
try:
    video_editor = VideoEditor()
except Exception as exc:
    logger.warning("VideoEditor unavailable: %s", exc)
    video_editor = None

executor = ThreadPoolExecutor(max_workers=2)

screenplay_store = ScreenplayStore()


@asynccontextmanager
async def lifespan(_: FastAPI):
    logger.info("FastAPI startup")
    logger.info("output dir: %s", settings.video.output_dir)
    try:
        yield
    finally:
        logger.info("FastAPI shutdown")
        executor.shutdown(wait=True)


app = FastAPI(
    title="Video Generation Service",
    description="Loan comparison visualization API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)


def _build_output_paths(task_id: str, output_format: str) -> dict[str, Path]:
    base_dir = settings.video.output_dir
    return {
        "rendered": base_dir / f"loan_comparison_{task_id}.rendered.{output_format}",
        "final": base_dir / f"loan_comparison_{task_id}.{output_format}",
        "subtitle": base_dir / f"loan_comparison_{task_id}.srt",
        "styled_subtitle": base_dir / f"loan_comparison_{task_id}.ass",
        "cover": base_dir / f"loan_comparison_{task_id}.png",
    }


def _resolve_optional_bgm(background_music: str | None) -> Path | None:
    if not background_music:
        return None
    candidate = Path(background_music).expanduser()
    if not candidate.is_absolute():
        candidate = settings.project_root / candidate
    return candidate.resolve()


@app.get("/health", response_model=HealthCheckResponse)
async def health_check() -> HealthCheckResponse:
    return HealthCheckResponse(
        status="OK",
        timestamp=utc_now(),
        version="1.0.0",
        message="service is running",
    )


@app.post("/api/loan/summary", response_model=LoanSummaryResponse)
async def calculate_loan_summary(
    loan_amount: float = Query(default=1_000_000, ge=10_000, le=10_000_000),
    annual_rate: float = Query(default=0.045, ge=0.001, le=0.2),
    loan_years: int = Query(default=30, ge=1, le=40),
) -> LoanSummaryResponse:
    try:
        summary = LoanData(
            loan_amount=loan_amount,
            annual_rate=annual_rate,
            loan_years=loan_years,
        ).get_summary()
        return LoanSummaryResponse(**summary)
    except Exception as exc:
        logger.error("loan summary failed: %s", exc, exc_info=True)
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/api/content/preview", response_model=ContentPlan)
async def preview_content_plan(request: GenerateVideoRequest) -> ContentPlan:
    try:
        summary = LoanData(
            loan_amount=request.loan_amount,
            annual_rate=request.annual_rate,
            loan_years=request.loan_years,
        ).get_summary()
        return build_loan_content_plan(request, summary)
    except Exception as exc:
        logger.error("content preview failed: %s", exc, exc_info=True)
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/api/screenplay/providers", response_model=list[ProviderDescriptorResponse])
async def list_screenplay_providers() -> list[ProviderDescriptorResponse]:
    return [ProviderDescriptorResponse(**item) for item in ai_planner.list_available_providers()]


@app.post("/api/screenplay/preview", response_model=ScreenplayPreviewResponse)
async def preview_screenplay(request: ScreenplayPreviewRequest) -> ScreenplayPreviewResponse:
    try:
        summary = LoanData(
            loan_amount=request.loan_amount,
            annual_rate=request.annual_rate,
            loan_years=request.loan_years,
        ).get_summary()
        topic = build_loan_screenplay_topic(
            topic=request.topic,
            loan_amount=request.loan_amount,
            loan_years=request.loan_years,
        )
        context = build_loan_screenplay_context(summary, style=request.style, platform=request.platform.value)
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
        logger.error("screenplay preview failed: %s", exc, exc_info=True)
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.patch("/api/screenplay/preview", response_model=ScreenplayEditResponse)
async def edit_screenplay(request: ScreenplayEditRequest) -> ScreenplayEditResponse:
    try:
        result = ai_planner.revise_screenplay(
            screenplay=request.screenplay,
            provider_name=request.screenplay_provider,
            edit_instruction=request.edit_instruction,
            title=request.title,
            logline=request.logline,
            scene_narration_overrides=request.scene_narration_overrides,
        )
        changed_scene_ids = list(request.scene_narration_overrides)
        return ScreenplayEditResponse(
            screenplay=result.screenplay,
            provider_used=result.provider_used,
            requested_provider=result.requested_provider,
            fallback_used=result.fallback_used,
            changed_scene_ids=changed_scene_ids,
        )
    except Exception as exc:
        logger.error("screenplay edit failed: %s", exc, exc_info=True)
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/api/library/scripts", response_model=ScriptCreateResponse)
async def library_create_script(body: ScriptCreateRequest) -> ScriptCreateResponse:
    script_id = screenplay_store.create_script(goal=body.goal, platform=body.platform, topic=body.topic)
    version = screenplay_store.add_version(script_id, body.screenplay, status=ScriptVersionStatus.DRAFT)
    return ScriptCreateResponse(script_id=script_id, version=version, status=ScriptVersionStatus.DRAFT.value)


@app.get("/api/library/scripts")
async def library_list_scripts(limit: int = Query(default=100, ge=1, le=500)) -> list[dict[str, object]]:
    return screenplay_store.list_scripts(limit=limit)


@app.get("/api/library/scripts/{script_id}")
async def library_get_script(
    script_id: str,
    version: int | None = Query(default=None),
) -> dict[str, object]:
    rec = screenplay_store.get_version(script_id, version)
    if rec is None:
        raise HTTPException(status_code=404, detail="剧本或版本不存在")
    return {
        "script_id": rec.script_id,
        "version": rec.version,
        "status": rec.status.value,
        "parent_version": rec.parent_version,
        "goal": rec.goal,
        "platform": rec.platform,
        "topic": rec.topic,
        "created_at": rec.created_at.isoformat(),
        "screenplay": rec.screenplay.model_dump(mode="json"),
    }


@app.get("/api/library/scripts/{script_id}/versions")
async def library_list_versions(script_id: str) -> list[dict[str, object]]:
    return screenplay_store.list_versions(script_id)


@app.post("/api/library/scripts/{script_id}/versions")
async def library_add_version(script_id: str, body: ScriptVersionCreateRequest) -> dict[str, object]:
    status = ScriptVersionStatus.APPROVED if body.status.lower().strip() == "approved" else ScriptVersionStatus.DRAFT
    if status == ScriptVersionStatus.APPROVED:
        try:
            validate_screenplay_for_approval(body.screenplay)
        except ScreenplayValidationError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
    try:
        ver = screenplay_store.add_version(
            script_id,
            body.screenplay,
            status=status,
            parent_version=body.parent_version,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"script_id": script_id, "version": ver, "status": status.value}


@app.post("/api/library/scripts/{script_id}/refine")
async def library_refine(script_id: str, body: ScriptRefineRequest) -> dict[str, object]:
    base = screenplay_store.get_version(script_id, body.base_version)
    if base is None:
        raise HTTPException(status_code=404, detail="剧本或版本不存在")
    try:
        result = ai_planner.revise_screenplay(
            screenplay=base.screenplay,
            provider_name=body.screenplay_provider,
            edit_instruction=body.edit_instruction,
            title=body.title,
            logline=body.logline,
            scene_narration_overrides=body.scene_narration_overrides,
        )
    except Exception as exc:
        logger.error("library refine failed: %s", exc, exc_info=True)
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    new_ver = screenplay_store.add_version(
        script_id,
        result.screenplay,
        status=ScriptVersionStatus.DRAFT,
        parent_version=base.version,
    )
    return {
        "script_id": script_id,
        "version": new_ver,
        "provider_used": result.provider_used,
        "requested_provider": result.requested_provider,
        "fallback_used": result.fallback_used,
        "changed_scene_ids": list(body.scene_narration_overrides.keys()),
        "screenplay": result.screenplay.model_dump(mode="json"),
    }


@app.post("/api/library/scripts/{script_id}/versions/{version}/approve")
async def library_approve_version(script_id: str, version: int) -> dict[str, str | int]:
    rec = screenplay_store.get_version(script_id, version)
    if rec is None:
        raise HTTPException(status_code=404, detail="版本不存在")
    try:
        validate_screenplay_for_approval(rec.screenplay)
    except ScreenplayValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    screenplay_store.set_version_status(script_id, version, ScriptVersionStatus.APPROVED)
    return {"script_id": script_id, "version": version, "status": ScriptVersionStatus.APPROVED.value}


@app.get("/api/library/assets", response_model=list[AssetListItem])
async def library_list_assets() -> list[AssetListItem]:
    return [
        AssetListItem(
            id=a.id,
            type=a.type.value,
            path=str(a.path),
            description=a.description,
            tags=list(a.tags),
        )
        for a in asset_manager.list_assets()
    ]


@app.post("/api/generate-video", response_model=VideoTaskResponse)
async def generate_video(
    request: GenerateVideoRequest,
    background_tasks: BackgroundTasks,
) -> VideoTaskResponse:
    if request.require_approved_script and not request.script_id:
        raise HTTPException(status_code=400, detail="require_approved_script 需要同时提供 script_id")

    if request.script_id:
        loaded = screenplay_store.get_version(request.script_id, request.script_version)
        if loaded is None:
            raise HTTPException(status_code=404, detail="未找到对应剧本或版本")
        if request.require_approved_script and loaded.status != ScriptVersionStatus.APPROVED:
            raise HTTPException(status_code=400, detail="该剧本版本尚未定稿(approved)，无法按此约束出片")
        _missing_assets = collect_asset_ids_from_screenplay(loaded.screenplay)
        _ok, missing = asset_manager.validate_ids(_missing_assets)
        if not _ok:
            logger.warning("剧本引用了素材库中不存在的 asset_id: %s", missing)

    try:
        task_id = task_manager.create_task(
            progress=0,
            current_step="queued",
            metadata={
                "platform": request.platform.value,
                "quality": request.quality.value,
                "output_format": request.output_format,
                "subtitle_burned": request.burn_subtitles,
                "bgm_applied": bool(request.background_music),
                "script_id": request.script_id,
                "script_version": request.script_version,
            },
        )

        background_tasks.add_task(
            _generate_video_background,
            task_id=task_id,
            request=request,
        )

        return VideoTaskResponse(
            task_id=task_id,
            status=TaskStatus.QUEUED,
            message="task queued",
            created_at=utc_now(),
        )
    except Exception as exc:
        logger.error("video task creation failed: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.get("/api/task/{task_id}", response_model=VideoProgressResponse)
async def get_task_status(task_id: str) -> VideoProgressResponse:
    task = task_manager.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail=f"task not found: {task_id}")

    return VideoProgressResponse(
        task_id=task.task_id,
        status=task.status,
        progress=task.progress,
        current_step=task.current_step,
        eta_seconds=task.eta_seconds,
        error_message=task.error_message,
        created_at=task.created_at,
        updated_at=task.updated_at,
    )


@app.get("/api/task/{task_id}/result", response_model=VideoResultResponse)
async def get_task_result(task_id: str) -> VideoResultResponse:
    task = task_manager.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail=f"task not found: {task_id}")

    result = VideoResultResponse(
        task_id=task.task_id,
        status=task.status,
        platform=task.metadata.get("platform"),
        quality=task.metadata.get("quality"),
        content_style=task.metadata.get("content_style"),
        content_variant=task.metadata.get("content_variant"),
        conclusion_card_title=task.metadata.get("conclusion_card_title"),
        theme_name=task.metadata.get("theme_name"),
        visual_focus=task.metadata.get("visual_focus"),
        subtitle_burned=task.metadata.get("subtitle_burned"),
        bgm_applied=task.metadata.get("bgm_applied"),
        rendered_video_path=task.metadata.get("rendered_video_path"),
        final_video_path=task.metadata.get("final_video_path"),
        subtitle_render_mode=task.metadata.get("subtitle_render_mode"),
        scene_schedule_path=task.metadata.get("scene_schedule_path"),
        scene_schedule=task.metadata.get("scene_schedule"),
        render_manifest_path=task.metadata.get("render_manifest_path"),
        created_at=task.created_at,
        completed_at=task.completed_at,
        error_message=task.error_message,
    )

    if task.status == TaskStatus.COMPLETED:
        output_file_value = task.metadata.get("output_file")
        output_file = Path(output_file_value) if output_file_value else None
        if output_file and output_file.exists():
            result.file_path = str(output_file)
            result.file_size = int(task.metadata.get("file_size", output_file.stat().st_size))
            result.video_url = f"/api/download/{task_id}"
            result.duration = float(task.metadata.get("duration", 0.0)) or None
            result.resolution = task.metadata.get("resolution")
            result.subtitle_path = task.metadata.get("subtitle_path")
            result.styled_subtitle_path = task.metadata.get("styled_subtitle_path")
            result.cover_path = task.metadata.get("cover_path")
            if task.completed_at:
                result.processing_time = (task.completed_at - task.created_at).total_seconds()

    return result


@app.get("/api/download/{task_id}")
async def download_video(task_id: str):
    task = task_manager.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail=f"task not found: {task_id}")

    if task.status != TaskStatus.COMPLETED:
        raise HTTPException(status_code=400, detail=f"task not completed: {task.status}")

    output_file_value = task.metadata.get("output_file")
    output_file = Path(output_file_value) if output_file_value else None
    if output_file is None or not output_file.exists():
        raise HTTPException(status_code=404, detail="output file not found")

    return FileResponse(
        path=output_file,
        media_type="video/mp4",
        filename=f"loan_comparison_{task_id}.mp4",
    )


def _generate_video_background(task_id: str, request: GenerateVideoRequest) -> None:
    tracker = ProgressTracker(task_manager, task_id, total_steps=100)

    try:
        tracker.start_step("init loan data")
        video_config = request.build_video_config(settings.video)
        output_paths = _build_output_paths(task_id, request.output_format)
        task_manager.update_task(
            task_id,
            metadata={
                "platform": request.platform.value,
                "quality": request.quality.value,
                "resolution": f"{video_config.width}x{video_config.height}",
                "duration": float(video_config.total_duration),
                "rendered_video_path": str(output_paths["rendered"]),
                "final_video_path": str(output_paths["final"]),
                "output_file": str(output_paths["final"]),
                "subtitle_path": str(output_paths["subtitle"]),
                "cover_path": str(output_paths["cover"]),
                "subtitle_burned": request.burn_subtitles,
                "bgm_applied": bool(request.background_music),
            },
        )
        loan_data = LoanData(
            loan_amount=request.loan_amount,
            annual_rate=request.annual_rate,
            loan_years=request.loan_years,
        )
        tracker.update(step=10)

        script_record = None
        if request.script_id:
            script_record = screenplay_store.get_version(request.script_id, request.script_version)
            if script_record is None:
                raise ValueError("剧本不存在或版本已删除")

        tracker.start_step("generate animation")
        engine = ContentEngine(loan_data=loan_data, video_config=video_config)
        background_music = _resolve_optional_bgm(request.background_music)
        if background_music is not None and not background_music.exists():
            raise FileNotFoundError(f"background music not found: {background_music}")

        def animation_progress(current_frame: int, total_frames: int) -> None:
            progress = 10 + int((current_frame / max(total_frames, 1)) * 70)
            tracker.update(step=progress)

        summary = loan_data.get_summary()
        content_plan = build_loan_content_plan(request, summary)
        render_expression = build_render_expression(content_plan)
        if script_record is not None:
            subtitle_items = screenplay_to_subtitle_items(
                script_record.screenplay,
                total_secs=float(video_config.total_duration),
                fps=int(video_config.fps),
            )
        else:
            subtitle_items = content_plan.to_subtitle_items()

        task_manager.update_task(
            task_id,
            metadata={
                "content_hook": content_plan.hook,
                "content_style": request.style.value,
                "content_variant": content_plan.variant.value,
                "conclusion_card_title": content_plan.conclusion_card.title,
                "theme_name": render_expression.theme.theme_name,
                "visual_focus": render_expression.visual_focus,
            },
        )
        engine.generate_animation(
            output_paths["rendered"],
            progress_callback=animation_progress,
            render_expression=render_expression,
            screenplay=script_record.screenplay if script_record else None,
        )
        rendered_schedule_path = resolve_scene_schedule_sidecar_path(output_paths["rendered"])
        scene_schedule_payload: dict[str, object] | None = None
        if rendered_schedule_path.exists():
            scene_schedule_payload = json.loads(rendered_schedule_path.read_text(encoding="utf-8"))
            task_manager.update_task(
                task_id,
                metadata={
                    "scene_schedule_path": str(rendered_schedule_path),
                    "scene_schedule": scene_schedule_payload,
                },
            )
        tracker.update(step=82)

        tracker.start_step("generate subtitle")
        if video_editor is None:
            raise RuntimeError("VideoEditor unavailable")
        video_editor.write_srt(subtitle_items, output_paths["subtitle"])
        styled_subtitle_path = None
        subtitle_render_mode = "srt"
        try:
            video_editor.write_ass(
                subtitle_items,
                output_paths["styled_subtitle"],
                render_expression=render_expression,
            )
            styled_subtitle_path = output_paths["styled_subtitle"]
            subtitle_render_mode = "ass"
        except Exception as exc:
            logger.warning("styled subtitle generation failed, fallback to srt: %s", exc)
        tracker.update(step=88)

        tracker.start_step("finalize video")
        video_editor.compose_final_video(
            rendered_video=output_paths["rendered"],
            final_video=output_paths["final"],
            subtitle_file=styled_subtitle_path or output_paths["subtitle"],
            burn_subtitles=request.burn_subtitles,
            background_music=background_music,
            bgm_volume=request.bgm_volume,
            video_audio_volume=request.video_audio_volume,
            loop_audio=request.bgm_loop,
            ducking_enabled=request.ducking_enabled,
            ducking_strength=request.ducking_strength,
        )
        video_editor.generate_cover_image(
            output_image=output_paths["cover"],
            render_expression=render_expression,
            input_video=output_paths["final"],
            timestamp_seconds=0.5,
        )
        video_info = video_editor.get_video_info(output_paths["final"])
        manifest_path = output_paths["final"].with_name(f"{output_paths['final'].stem}.render_manifest.json")
        manifest_payload = build_render_manifest_payload(
            task_id=task_id,
            final_video=output_paths["final"],
            platform=request.platform.value,
            quality=request.quality.value,
            video_config=video_config.model_dump(mode="json"),
            loan={
                "loan_amount": request.loan_amount,
                "annual_rate": request.annual_rate,
                "loan_years": request.loan_years,
            },
            script_id=request.script_id,
            script_version=script_record.version if script_record else None,
            script_status=script_record.status.value if script_record else None,
            screenplay=script_record.screenplay if script_record else None,
            scene_schedule=scene_schedule_payload,
            viz_backend_default=default_backend_name(),
        )
        write_render_manifest(manifest_path, manifest_payload)
        task_manager.update_task(
            task_id,
            metadata={
                "file_size": video_info.get("file_size"),
                "duration": video_info.get("duration") or float(video_config.total_duration),
                "resolution": video_info.get("resolution") or f"{video_config.width}x{video_config.height}",
                "rendered_video_path": str(output_paths["rendered"]),
                "final_video_path": str(output_paths["final"]),
                "output_file": str(output_paths["final"]),
                "subtitle_path": str(output_paths["subtitle"]),
                "styled_subtitle_path": str(styled_subtitle_path) if styled_subtitle_path else None,
                "subtitle_render_mode": subtitle_render_mode,
                "cover_path": str(output_paths["cover"]),
                "subtitle_burned": request.burn_subtitles,
                "bgm_applied": background_music is not None,
                "content_hook": content_plan.hook,
                "content_style": request.style.value,
                "content_variant": content_plan.variant.value,
                "conclusion_card_title": content_plan.conclusion_card.title,
                "theme_name": render_expression.theme.theme_name,
                "visual_focus": render_expression.visual_focus,
                "render_manifest_path": str(manifest_path),
            },
        )
        tracker.update(step=92)

        tracker.start_step("finish")
        tracker.complete()

        logger.info("video generated: %s -> %s", task_id, output_paths["final"])
    except Exception as exc:
        logger.error("video generation failed: %s - %s", task_id, exc, exc_info=True)
        tracker.fail(str(exc))


@app.get("/")
async def root():
    return {
        "message": "Free Ride Python 自动化演示成功！",
        "features": [
            "自动化测试",
            "代码格式化",
            "类型检查",
            "API 文档",
            "Docker 容器化",
        ],
        "service": "Video Generation Service",
        "version": "1.0.0",
        "endpoints": {
            "health_check": "/health",
            "api_docs": "/docs",
            "loan_summary": "POST /api/loan/summary",
            "screenplay_providers": "GET /api/screenplay/providers",
            "screenplay_preview": "POST /api/screenplay/preview",
            "screenplay_edit": "PATCH /api/screenplay/preview",
            "generate_video": "POST /api/generate-video",
            "task_status": "GET /api/task/{task_id}",
            "task_result": "GET /api/task/{task_id}/result",
            "download_video": "GET /api/download/{task_id}",
        },
        "timestamp": utc_now().isoformat(),
    }


def _build_uvicorn_log_config() -> dict:
    return {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "default": {
                "format": "[%(asctime)s] [%(name)s] [%(levelname)s] %(message)s",
            },
        },
        "handlers": {
            "default": {
                "formatter": "default",
                "class": "logging.StreamHandler",
            },
        },
        "loggers": {
            "uvicorn": {"handlers": ["default"], "level": "INFO"},
            "uvicorn.access": {"handlers": ["default"], "level": "INFO", "propagate": False},
        },
    }


def start_api_server(host: str = "0.0.0.0", port: int = 8000) -> None:
    logger.info("Starting API service")
    uvicorn.run(
        app,
        host=host,
        port=port,
        log_config=_build_uvicorn_log_config(),
    )


if __name__ == "__main__":
    start_api_server()
