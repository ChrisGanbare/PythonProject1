"""FastAPI app for loan_comparison project."""

from __future__ import annotations

import sys
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
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

from shared.config.settings import settings
from shared.core.task_manager import ProgressTracker, TaskManager
from shared.media.video_editor import VideoEditor
from shared.utils.logger import setup_logger
from loan_comparison.models.loan import LoanData
from loan_comparison.models.schemas import (
    GenerateVideoRequest,
    HealthCheckResponse,
    LoanSummaryResponse,
    VideoProgressResponse,
    VideoResultResponse,
    VideoTaskResponse,
)
from loan_comparison.models.schemas import TaskStatus
from loan_comparison.renderer.animation import ContentEngine


logger = setup_logger(
    name="video_api",
    log_dir=settings.log.log_dir,
    log_level=settings.log.log_level,
    log_to_file=settings.log.log_to_file,
    log_to_console=settings.log.log_to_console,
)

app = FastAPI(
    title="Video Generation Service",
    description="Loan comparison visualization API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

task_manager = TaskManager()
try:
    video_editor = VideoEditor()
except Exception as exc:
    logger.warning("VideoEditor unavailable: %s", exc)
    video_editor = None

executor = ThreadPoolExecutor(max_workers=2)


@app.get("/health", response_model=HealthCheckResponse)
async def health_check() -> HealthCheckResponse:
    return HealthCheckResponse(
        status="OK",
        timestamp=datetime.utcnow(),
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


@app.post("/api/generate-video", response_model=VideoTaskResponse)
async def generate_video(
    request: GenerateVideoRequest,
    background_tasks: BackgroundTasks,
) -> VideoTaskResponse:
    try:
        task_id = task_manager.create_task(progress=0, current_step="queued")

        background_tasks.add_task(
            _generate_video_background,
            task_id=task_id,
            request=request,
        )

        return VideoTaskResponse(
            task_id=task_id,
            status=TaskStatus.QUEUED,
            message="task queued",
            created_at=datetime.utcnow(),
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
        created_at=task.created_at,
        completed_at=task.completed_at,
    )

    if task.status == TaskStatus.COMPLETED:
        output_file = settings.video.output_dir / f"loan_comparison_{task_id}.mp4"
        if output_file.exists():
            result.file_path = str(output_file)
            result.file_size = output_file.stat().st_size
            result.video_url = f"/api/download/{task_id}"
            result.duration = float(settings.video.total_duration)
            result.resolution = f"{settings.video.width}x{settings.video.height}"
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

    output_file = settings.video.output_dir / f"loan_comparison_{task_id}.mp4"
    if not output_file.exists():
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
        loan_data = LoanData(
            loan_amount=request.loan_amount,
            annual_rate=request.annual_rate,
            loan_years=request.loan_years,
        )
        tracker.update(step=10)

        tracker.start_step("generate animation")
        engine = ContentEngine(loan_data=loan_data)

        output_file = settings.video.output_dir / f"loan_comparison_{task_id}.mp4"

        def animation_progress(current_frame: int, total_frames: int) -> None:
            progress = 10 + int((current_frame / max(total_frames, 1)) * 70)
            tracker.update(step=progress)

        engine.generate_animation(output_file, progress_callback=animation_progress)
        tracker.update(step=80)

        tracker.start_step("finish")
        tracker.complete()

        logger.info("video generated: %s -> %s", task_id, output_file)
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
            "generate_video": "POST /api/generate-video",
            "task_status": "GET /api/task/{task_id}",
            "task_result": "GET /api/task/{task_id}/result",
            "download_video": "GET /api/download/{task_id}",
        },
        "timestamp": datetime.utcnow().isoformat(),
    }


@app.on_event("startup")
async def startup_event() -> None:
    logger.info("FastAPI startup")
    logger.info("output dir: %s", settings.video.output_dir)


@app.on_event("shutdown")
async def shutdown_event() -> None:
    logger.info("FastAPI shutdown")
    executor.shutdown(wait=True)


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
