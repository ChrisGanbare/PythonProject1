"""Shared types for data-viz video rendering (backend-agnostic)."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class VideoFormatSpec(BaseModel):
    """Target raster / video dimensions and timing."""

    width_px: int = Field(ge=480, le=4096)
    height_px: int = Field(ge=480, le=4096)
    dpi: int = Field(default=100, ge=48, le=300)
    fps: int = Field(default=30)
    total_duration_secs: float = Field(default=30.0, gt=0)
    total_frames: int = Field(default=900, ge=1)

    @property
    def aspect_ratio(self) -> float:
        return self.width_px / max(self.height_px, 1)


class FrameRequest(BaseModel):
    """Single-frame or animation-global request passed to a viz backend."""

    frame_index: int = Field(default=0, ge=0)
    total_frames: int = Field(default=1, ge=1)
    format: VideoFormatSpec
    theme_token: str | None = Field(default=None, description="e.g. dark_flourish, from render_expression")
    viz_scene_id: str | None = Field(default=None, description="Bound to Screenplay scene or chart layer id")
    extra: dict[str, Any] = Field(default_factory=dict)


BackendName = Literal["matplotlib", "plotly_static", "manim"]


class VizSceneRef(BaseModel):
    """Logical chart scene for manifest / cache keys (not the full dataset)."""

    scene_id: str
    backend: BackendName = "matplotlib"
    spec_fingerprint: str = Field(default="", description="hash or short id of chart recipe + data snapshot")
