"""FastAPI app for fund_fee_erosion project."""

from __future__ import annotations

import sys
from contextlib import asynccontextmanager
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

# Allow direct execution: `python projects/fund_fee_erosion/api/main.py`
if __package__ in (None, ""):
    _projects_root  = Path(__file__).resolve().parents[2]   # projects/
    _workspace_root = Path(__file__).resolve().parents[3]   # video_project/
    for _p in [str(_projects_root), str(_workspace_root)]:
        if _p not in sys.path:
            sys.path.insert(0, _p)

from fastapi import BackgroundTasks, FastAPI, HTTPException, Query
from fastapi.responses import FileResponse
import uvicorn

from shared.config.settings import settings
from shared.content.render_mapping import build_render_expression
from shared.content.schemas import ContentPlan
from shared.core.task_manager import ProgressTracker, TaskManager
from shared.library.render_manifest import build_fund_render_manifest_payload, write_render_manifest
from shared.media.video_editor import VideoEditor
from shared.utils.logger import setup_logger
from shared.utils.time import utc_now
from shared.visualization.registry import default_backend_name
from fund_fee_erosion.content.planner import build_fund_content_plan
from fund_fee_erosion.data.pipeline import fund_params_for_viz
from fund_fee_erosion.models.calculator import FundParams
from fund_fee_erosion.models.schemas import (
    FundSummaryResponse,
    GenerateFundVideoRequest,
    HealthCheckResponse,
    TaskStatus,
    VideoProgressResponse,
    VideoResultResponse,
    VideoTaskResponse,
)
from fund_fee_erosion.renderer.animation import ContentEngine


logger = setup_logger(
    name="fund_api",
    log_dir=settings.log.log_dir,
    log_level=settings.log.log_level,
    log_to_file=settings.log.log_to_file,
    log_to_console=settings.log.log_to_console,
)

task_manager = TaskManager()
video_editor = VideoEditor()
executor = ThreadPoolExecutor(max_workers=2)


@asynccontextmanager
async def lifespan(_: FastAPI):
    logger.info("Fund Fee Erosion API startup")
    logger.info("output dir: %s", settings.video.output_dir)
    try:
        yield
    finally:
        logger.info("Fund Fee Erosion API shutdown")
        executor.shutdown(wait=True)


app = FastAPI(
    title="Fund Fee Erosion Service",
    description="基金手续费复利侵蚀可视化 API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)


def _build_output_paths(task_id: str, output_format: str) -> dict[str, Path]:
    base_dir = settings.video.output_dir
    return {
        "rendered": base_dir / f"fund_fee_erosion_{task_id}.rendered.{output_format}",
        "final": base_dir / f"fund_fee_erosion_{task_id}.{output_format}",
        "subtitle": base_dir / f"fund_fee_erosion_{task_id}.srt",
        "styled_subtitle": base_dir / f"fund_fee_erosion_{task_id}.ass",
        "cover": base_dir / f"fund_fee_erosion_{task_id}.png",
    }


def _resolve_optional_bgm(background_music: str | None) -> Path | None:
    if not background_music:
        return None
    candidate = Path(background_music).expanduser()
    if not candidate.is_absolute():
        candidate = settings.project_root / candidate
    return candidate.resolve()


# ── Endpoints ────────────────────────────────────────────────

@app.get("/health", response_model=HealthCheckResponse)
async def health_check() -> HealthCheckResponse:
    return HealthCheckResponse(
        status="OK",
        timestamp=utc_now(),
        version="1.0.0",
        message="service is running",
    )


@app.get("/api/fund/summary", response_model=FundSummaryResponse)
async def calculate_fund_summary(
    principal: float = Query(default=1_000_000, ge=10_000, le=100_000_000),
    gross_return: float = Query(default=0.08, ge=0.0, le=1.0),
    years: int = Query(default=30, ge=1, le=50),
) -> FundSummaryResponse:
    try:
        params = FundParams(principal=principal, gross_return=gross_return, years=years)
        return FundSummaryResponse(
            principal=params.principal,
            gross_return=params.gross_return,
            years=params.years,
            scenarios=params.get_summary(),
        )
    except Exception as exc:
        logger.error("fund summary failed: %s", exc, exc_info=True)
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/api/content/preview", response_model=ContentPlan)
async def preview_content_plan(request: GenerateFundVideoRequest) -> ContentPlan:
    try:
        params = FundParams(
            principal=request.principal,
            gross_return=request.gross_return,
            years=request.years,
        )
        return build_fund_content_plan(request, params.get_summary())
    except Exception as exc:
        logger.error("content preview failed: %s", exc, exc_info=True)
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/api/generate-video", response_model=VideoTaskResponse)
async def generate_video(
    request: GenerateFundVideoRequest,
    background_tasks: BackgroundTasks,
) -> VideoTaskResponse:
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
        render_manifest_path=task.metadata.get("render_manifest_path"),
        render_fingerprint=task.metadata.get("render_fingerprint"),
        subtitle_burned=task.metadata.get("subtitle_burned"),
        bgm_applied=task.metadata.get("bgm_applied"),
        rendered_video_path=task.metadata.get("rendered_video_path"),
        final_video_path=task.metadata.get("final_video_path"),
        subtitle_render_mode=task.metadata.get("subtitle_render_mode"),
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
                result.processing_time = (
                    task.completed_at - task.created_at
                ).total_seconds()

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
        filename=f"fund_fee_erosion_{task_id}.mp4",
    )


@app.get("/")
async def root():
    return {
        "service": "Fund Fee Erosion Service",
        "version": "1.0.0",
        "endpoints": {
            "health_check":   "/health",
            "api_docs":       "/docs",
            "fund_summary":   "GET /api/fund/summary",
            "generate_video": "POST /api/generate-video",
            "task_status":    "GET /api/task/{task_id}",
            "task_result":    "GET /api/task/{task_id}/result",
            "download_video": "GET /api/download/{task_id}",
        },
        "timestamp": utc_now().isoformat(),
    }


# ── 后台任务 ─────────────────────────────────────────────────

def _generate_video_background(task_id: str, request: GenerateFundVideoRequest) -> None:
    tracker = ProgressTracker(task_manager, task_id, total_steps=100)

    try:
        tracker.start_step("init fund params")
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
        params = FundParams(
            principal=request.principal,
            gross_return=request.gross_return,
            years=request.years,
        )
        tracker.update(step=10)

        tracker.start_step("generate animation")
        engine = ContentEngine(fund_params=params, video_config=video_config)
        background_music = _resolve_optional_bgm(request.background_music)
        if background_music is not None and not background_music.exists():
            raise FileNotFoundError(f"background music not found: {background_music}")

        def _progress(current: int, total: int) -> None:
            tracker.update(step=10 + int((current / max(total, 1)) * 70))

        summary = params.get_summary()
        content_plan = build_fund_content_plan(request, summary)
        render_expression = build_render_expression(content_plan)
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
            progress_callback=_progress,
            render_expression=render_expression,
        )
        tracker.update(step=82)

        tracker.start_step("generate subtitle")
        video_editor.write_srt(content_plan.to_subtitle_items(), output_paths["subtitle"])
        styled_subtitle_path = None
        subtitle_render_mode = "srt"
        try:
            video_editor.write_ass(
                content_plan.to_subtitle_items(),
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
        mf_payload = build_fund_render_manifest_payload(
            task_id=task_id,
            final_video=output_paths["final"],
            platform=request.platform.value,
            quality=request.quality.value,
            video_config=video_config.model_dump(mode="json"),
            fund=fund_params_for_viz(params),
            viz_backend_default=default_backend_name(),
        )
        write_render_manifest(manifest_path, mf_payload)
        _render_fp = str(mf_payload["viz"]["reproducibility_fingerprint"])
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
                "render_fingerprint": _render_fp,
            },
        )
        tracker.update(step=92)

        tracker.start_step("finish")
        tracker.complete()
        logger.info("video generated: %s -> %s", task_id, output_paths["final"])
    except Exception as exc:
        logger.error("video generation failed: %s - %s", task_id, exc, exc_info=True)
        tracker.fail(str(exc))



def _build_uvicorn_log_config() -> dict:
    return {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "default": {"format": "[%(asctime)s] [%(name)s] [%(levelname)s] %(message)s"},
        },
        "handlers": {
            "default": {"formatter": "default", "class": "logging.StreamHandler"},
        },
        "loggers": {
            "uvicorn":        {"handlers": ["default"], "level": "INFO"},
            "uvicorn.access": {"handlers": ["default"], "level": "INFO", "propagate": False},
        },
    }


def start_api_server(host: str = "0.0.0.0", port: int = 8001) -> None:
    logger.info("Starting Fund Fee Erosion API service")
    uvicorn.run(app, host=host, port=port, log_config=_build_uvicorn_log_config())


if __name__ == "__main__":
    start_api_server()
