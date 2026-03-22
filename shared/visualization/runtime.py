"""Bridge subprocess / env-based renderers to shared FrameRequest / VideoFormatSpec."""

from __future__ import annotations

import os


from shared.visualization.types import FrameRequest, VideoFormatSpec


def frame_request_from_env() -> FrameRequest:
    """Build FrameRequest from VIDEO_* environment (used by matplotlib impl.py workers)."""
    width = int(os.getenv("VIDEO_WIDTH", "1080"))
    height = int(os.getenv("VIDEO_HEIGHT", "1920"))
    dpi = int(os.getenv("VIDEO_DPI", "100"))
    fps = int(os.getenv("VIDEO_FPS", "30"))
    total_secs = float(os.getenv("VIDEO_DURATION", "30"))
    computed = max(1, int(round(total_secs * fps)))
    total_frames = int(os.getenv("VIDEO_TOTAL_FRAMES", str(computed)))

    fmt = VideoFormatSpec(
        width_px=width,
        height_px=height,
        dpi=dpi,
        fps=fps,
        total_duration_secs=total_secs,
        total_frames=total_frames,
    )
    frame_index = int(os.getenv("VIDEO_FRAME_INDEX", "0"))
    viz_scene = os.getenv("VIDEO_VIZ_SCENE_ID") or None
    theme = os.getenv("VIDEO_THEME_NAME") or None

    return FrameRequest(
        frame_index=max(0, frame_index),
        total_frames=max(1, total_frames),
        format=fmt,
        theme_token=theme,
        viz_scene_id=viz_scene,
    )


def cache_key_components_from_env() -> dict[str, str]:
    """Stable strings for frame-cache keys (extend with data hash in projects)."""
    keys = [
        "VIDEO_WIDTH",
        "VIDEO_HEIGHT",
        "VIDEO_DPI",
        "VIDEO_FPS",
        "VIDEO_DURATION",
        "VIDEO_LOAN_AMOUNT",
        "VIDEO_ANNUAL_RATE",
        "VIDEO_LOAN_YEARS",
        "VIDEO_RENDER_EXPRESSION",
        "VIDEO_THEME_CONFIG",
    ]
    return {k: os.getenv(k, "") for k in keys}
