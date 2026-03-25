"""Callable entrypoints exposed for the root scheduler."""

from __future__ import annotations


def run_smoke_check() -> dict[str, str]:
    return {"project": "my_tutor", "status": "ok"}


def run_render(
    quality: str = "draft",
    platform: str = "douyin",
    output_file: str = "",
) -> dict[str, str]:
    """Generate visualization video via the project renderer."""
    from my_tutor.renderer.viz_backend import render_video

    result_path = render_video(
        quality=quality,
        platform=platform,
        output_file=output_file or None,
    )
    return {"final_video_path": str(result_path), "status": "success"}
