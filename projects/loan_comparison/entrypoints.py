"""Callable entrypoints exposed for the root scheduler."""

from __future__ import annotations

import json

from shared.config.settings import settings
from shared.content.render_timeline import build_render_timeline
from .models.loan import LoanData
from .renderer.animation import generate_loan_animation, resolve_scene_schedule_sidecar_path
from shared.platform.presets import get_platform_preset
from shared.content.screenplay import Screenplay


def run_smoke_check() -> dict[str, float]:
    """Quick validation task that does not require ffmpeg/OpenAI."""
    summary = LoanData(loan_amount=1_000_000, annual_rate=0.045, loan_years=30).get_summary()
    result = {
        "equal_interest_total_interest": round(summary["equal_interest"]["total_interest"], 2),
        "equal_principal_total_interest": round(summary["equal_principal"]["total_interest"], 2),
    }
    print("Smoke check passed:", result)
    return result


def run_loan_animation(
    use_original: bool = False,
    output_file: str | None = None,
    platform: str | None = None,
    quality: str | None = None,
    width: int | None = None,
    height: int | None = None,
    duration: int | None = None,
    fps: int | None = None,
    loan_amount: float | None = None,
    annual_rate: float | None = None,
    loan_years: int | None = None,
    screenplay: dict | None = None,
    style: str | None = None,  # New param
    topic: str | None = None,  # New param
) -> dict[str, str | float | None]:
    """
    Generate the loan comparison animation video.

    If `style` or `topic` is provided, the AI Planner is engaged to generate a screenplay.
    """
    if use_original:
        print("`use_original=true` is no longer needed; using subproject-local renderer.")

    screenplay_model = Screenplay.model_validate(screenplay) if screenplay else None
    if screenplay_model is None and (style or topic):
        from shared.content.ai_planner import ai_planner

        print(
            f"Engagement AI Planner for topic='{topic or 'Loan Comparison'}' style='{style or 'Cinematic'}'..."
        )
        screenplay_model = ai_planner.generate_screenplay(topic or "Loan Interest", style or "Cinematic")

    output_path = generate_loan_animation(
        output_file=output_file,
        platform=platform,
        quality=quality,
        width=width,
        height=height,
        duration=duration,
        fps=fps,
        loan_amount=loan_amount,
        annual_rate=annual_rate,
        loan_years=loan_years,
        screenplay=screenplay_model,
    )

    scene_schedule_path = resolve_scene_schedule_sidecar_path(output_path)
    scene_schedule = None
    if scene_schedule_path.exists():
        scene_schedule = json.loads(scene_schedule_path.read_text(encoding="utf-8"))

    resolved_topic = topic or (screenplay_model.topic if screenplay_model else "Loan Interest")
    resolved_style = style or (screenplay_model.visual_style.value if screenplay_model else "default")

    return {
        "final_video_path": str(output_path),
        "scene_schedule_path": str(scene_schedule_path) if scene_schedule_path.exists() else None,
        "scene_schedule": scene_schedule,
        "topic": resolved_topic,
        "style": resolved_style,
        "screenplay_title": screenplay_model.title if screenplay_model else None,
    }


def run_scene_schedule_preview(
    platform: str = "douyin",
    duration: int | None = None,
    fps: int | None = None,
    screenplay: dict | None = None,
    style: str | None = None,
    topic: str | None = None,
) -> dict[str, object]:
    """Build scene-level schedule metadata without rendering video."""
    screenplay_model = Screenplay.model_validate(screenplay) if screenplay else None
    if screenplay_model is None and (style or topic):
        from shared.content.ai_planner import ai_planner

        screenplay_model = ai_planner.generate_screenplay(topic or "Loan Interest", style or "Cinematic")

    if screenplay_model is None:
        raise ValueError("screenplay, style, or topic is required to preview a scene schedule")

    preset = get_platform_preset(platform)
    effective_duration = int(duration or settings.video.total_duration)
    effective_fps = int(fps or preset.fps or settings.video.fps)
    timeline = build_render_timeline(screenplay_model, total_secs=effective_duration, fps=effective_fps)

    return {
        "platform": platform,
        "duration": effective_duration,
        "fps": effective_fps,
        "screenplay_title": screenplay_model.title,
        "scene_schedule": timeline.export_schedule_payload(),
    }


def run_api(host: str = "0.0.0.0", port: int = 8000) -> None:
    """Start FastAPI service for this project."""
    from .api.main import start_api_server

    start_api_server(host=host, port=port)
