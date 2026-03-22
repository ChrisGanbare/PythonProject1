"""Screenplay adapter for the video_platform_introduction project."""

from __future__ import annotations

from copy import deepcopy
from typing import Any

from shared.content.schemas import ContentPlan, StoryBeatType
from shared.content.screenplay import Mood, Scene, Screenplay, VisualElement, VisualStyle

LOCAL_SCREENPLAY_PROVIDER_NAME = "video_platform_template"
LOCAL_SCREENPLAY_PROVIDER_DESCRIPTION = "Project-local deterministic screenplay template for dashboard preview/edit."


_BEAT_MOODS: dict[StoryBeatType, Mood] = {
    StoryBeatType.HOOK: Mood.EAGER,
    StoryBeatType.SETUP: Mood.NEUTRAL,
    StoryBeatType.CLIMAX: Mood.DRAMATIC,
    StoryBeatType.CONCLUSION: Mood.CALM,
}


def build_video_platform_screenplay_topic(topic: str | None) -> str:
    normalized = (topic or "").strip()
    return normalized or "Video Platform Introduction"


def build_video_platform_screenplay_context(request: Any, plan: ContentPlan) -> dict[str, Any]:
    return {
        "project": "video_platform_introduction",
        "platform": request.platform.value,
        "style": request.style.value,
        "video_duration": request.video_duration,
        "sample_metric": getattr(request, "sample_metric", None),
        "content_variant": plan.variant.value,
        "beats": [
            {
                "beat_type": beat.beat_type.value,
                "headline": beat.headline,
                "narration": beat.narration,
                "visual_hint": beat.visual_hint,
                "start_seconds": beat.start_seconds,
                "end_seconds": beat.end_seconds,
            }
            for beat in plan.beats
        ],
        "conclusion_card": plan.conclusion_card.model_dump(),
        "tags": list(plan.tags),
    }


def _visual_style_for(style: str) -> VisualStyle:
    mapping = {
        "minimal": VisualStyle.MINIMALIST,
        "tech": VisualStyle.DATA_DRIVEN,
        "news": VisualStyle.CORPORATE,
        "trendy": VisualStyle.CINEMATIC,
    }
    return mapping.get(style, VisualStyle.DATA_DRIVEN)


def _scene_id(index: int, beat_type: StoryBeatType) -> str:
    return f"scene_{index:02d}_{beat_type.value}"


def build_video_platform_screenplay(
    *,
    topic: str,
    target_audience: str,
    plan: ContentPlan,
    context: dict[str, Any] | None = None,
) -> Screenplay:
    context = context or {}
    scenes: list[Scene] = []
    for index, beat in enumerate(plan.beats, start=1):
        duration_est = max(0.5, float(beat.end_seconds - beat.start_seconds))
        visual_prompt = beat.visual_hint or beat.headline
        scenes.append(
            Scene(
                id=_scene_id(index, beat.beat_type),
                duration_est=duration_est,
                narration=beat.narration,
                visual_prompt=visual_prompt,
                visuals=[
                    VisualElement(
                        type="text",
                        content=beat.headline,
                        style={
                            "role": beat.beat_type.value,
                            "platform": plan.platform,
                            "style": plan.style.value,
                        },
                        animation_in="fade_in",
                        animation_out="fade_out",
                    )
                ],
                mood=_BEAT_MOODS.get(beat.beat_type, Mood.NEUTRAL),
                action_directives={
                    "beat_type": beat.beat_type.value,
                    "start_seconds": beat.start_seconds,
                    "end_seconds": beat.end_seconds,
                },
            )
        )

    return Screenplay(
        title=f"{topic}｜平台介绍短视频",
        logline=f"面向{target_audience}：{plan.summary}",
        topic=topic,
        target_audience=target_audience,
        mood=_BEAT_MOODS.get(plan.beats[0].beat_type, Mood.NEUTRAL) if plan.beats else Mood.NEUTRAL,
        visual_style=_visual_style_for(plan.style.value),
        scenes=scenes,
        total_duration_est=float(plan.total_duration),
        metadata={
            "provider": LOCAL_SCREENPLAY_PROVIDER_NAME,
            "source": "content_plan",
            "platform": plan.platform,
            "style": plan.style.value,
            "tags": list(plan.tags),
            "context": deepcopy(context),
        },
    )


def revise_video_platform_screenplay(
    screenplay: Screenplay,
    *,
    title: str | None = None,
    logline: str | None = None,
    edit_instruction: str | None = None,
    scene_narration_overrides: dict[str, str] | None = None,
) -> Screenplay:
    updated = screenplay.model_copy(deep=True)
    if title is not None:
        updated.title = title
    if logline is not None:
        updated.logline = logline
    overrides = scene_narration_overrides or {}
    for scene in updated.scenes:
        if scene.id in overrides:
            scene.narration = overrides[scene.id]
    if edit_instruction:
        metadata = dict(updated.metadata)
        metadata["last_edit_instruction"] = edit_instruction
        updated.metadata = metadata
    return updated

