"""Core screenplay and director schemas."""

from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

class Mood(str, Enum):
    """The emotional tone of a scene or the entire screenplay."""
    NEUTRAL = "neutral"
    EAGER = "eager"
    SERIOUS = "serious"
    DRAMATIC = "dramatic"
    UPBEAT = "upbeat"
    CALM = "calm"

class VisualStyle(str, Enum):
    """High-level visual style descriptors."""
    MINIMALIST = "minimalist"
    CORPORATE = "corporate"
    CINEMATIC = "cinematic"
    DATA_DRIVEN = "data_driven"
    HAND_DRAWN = "hand_drawn"

class AudioCue(BaseModel):
    """Sound effect or background music instruction."""
    asset_id: str = Field(..., description="ID of the audio asset (e.g., 'bgm_upbeat_01')")
    volume: float = Field(default=1.0, ge=0.0, le=1.0)
    start_offset: float = Field(default=0.0, description="Start time offset in seconds")
    duration: Optional[float] = Field(default=None, description="Duration in seconds. None means play until stopped/end.")
    loop: bool = False

class VisualElement(BaseModel):
    """A visual component in a scene."""
    type: str = Field(..., description="Type of visual (e.g., 'text', 'chart', 'image', 'video')")
    content: str = Field(..., description="Content data (text string, file path, data values)")
    style: Dict[str, Any] = Field(default_factory=dict, description="Style overrides like color, font, position")
    animation_in: Optional[str] = Field(default=None, description="Animation effect for appearing")
    animation_out: Optional[str] = Field(default=None, description="Animation effect for disappearing")

class Scene(BaseModel):
    """A distinct segment of the video."""
    id: str
    duration_est: float = Field(..., description="Estimated duration in seconds")
    narration: str = Field(..., description="Voiceover text")
    visual_prompt: str = Field(..., description="Description for AI image generation or human artist")
    visuals: List[VisualElement] = Field(default_factory=list, description="Concrete visual elements to render")
    mood: Mood = Field(default=Mood.NEUTRAL)
    audio_cues: List[AudioCue] = Field(default_factory=list)
    action_directives: Dict[str, Any] = Field(
        default_factory=dict,
        description=(
            "Renderer directives. Conventional keys: viz_scene_id (e.g. loan project main chart "
            "`loan_compare_main`), chart_type (e.g. dual_cumulative, trend_gap), "
            "reference_style (e.g. flourish_clarity); plus camera_movement etc."
        ),
    )

class Screenplay(BaseModel):
    """The complete blueprint for a video."""
    title: str
    logline: str = Field(..., description="One-sentence summary")
    topic: str
    target_audience: str
    mood: Mood = Field(default=Mood.NEUTRAL)
    visual_style: VisualStyle = Field(default=VisualStyle.DATA_DRIVEN)
    scenes: List[Scene]
    total_duration_est: float = Field(..., description="Total estimated duration")
    metadata: Dict[str, Any] = Field(default_factory=dict)

