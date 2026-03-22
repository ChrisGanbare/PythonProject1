"""公共内容规划器。"""

from __future__ import annotations

from shared.content.rhythm import build_story_windows
from shared.content.schemas import ContentBrief, ContentPlan, ContentVariant, ConclusionCard, StoryBeat, StoryBeatType, SubtitleCue
from shared.content.templates import (
    CONCLUSION_CARD_THEMES,
    NARRATION_WRAPPERS,
    PLATFORM_HOOKS,
    STYLE_HEADLINES,
    VARIANT_VISUAL_HINTS,
)


def resolve_content_variant(brief: ContentBrief) -> ContentVariant:
    """根据时长与显式配置选择内容结构版本。"""
    if brief.variant is not None:
        return brief.variant
    return ContentVariant.SHORT if brief.total_duration <= 45 else ContentVariant.STANDARD


def _resolve_subtitle_style_token(beat_type: StoryBeatType, call_to_action: str | None = None) -> str:
    if beat_type is StoryBeatType.HOOK:
        return "hook_emphasis"
    if beat_type is StoryBeatType.SETUP:
        return "body_explainer"
    if beat_type is StoryBeatType.CLIMAX:
        return "climax_emphasis"
    return "conclusion_cta" if call_to_action else "conclusion_summary"


def build_content_plan(brief: ContentBrief) -> ContentPlan:
    """根据业务摘要生成可复用的短视频内容方案。"""
    variant = resolve_content_variant(brief)
    windows = build_story_windows(brief.total_duration, variant=variant)
    wrappers = NARRATION_WRAPPERS[brief.style]
    headlines = STYLE_HEADLINES[brief.style]
    platform_hooks = PLATFORM_HOOKS.get(brief.platform, {})
    visual_hints = VARIANT_VISUAL_HINTS[variant]
    facts = {
        StoryBeatType.HOOK: brief.hook_fact,
        StoryBeatType.SETUP: brief.setup_fact,
        StoryBeatType.CLIMAX: brief.climax_fact,
        StoryBeatType.CONCLUSION: brief.conclusion_fact,
    }

    beats: list[StoryBeat] = []
    subtitle_cues: list[SubtitleCue] = []
    ordered_beats = [
        StoryBeatType.HOOK,
        StoryBeatType.SETUP,
        StoryBeatType.CLIMAX,
        StoryBeatType.CONCLUSION,
    ]

    for beat_type, window in zip(
        ordered_beats,
        windows,
        strict=True,
    ):
        narration = wrappers[beat_type].format(fact=facts[beat_type])
        if beat_type == StoryBeatType.HOOK:
            hook_template = platform_hooks.get(brief.style)
            if hook_template:
                narration = hook_template.format(fact=facts[beat_type])

        beats.append(
            StoryBeat(
                beat_type=beat_type,
                headline=headlines[beat_type],
                narration=narration,
                visual_hint=visual_hints[beat_type],
                start_seconds=window[0],
                end_seconds=window[1],
            )
        )
        subtitle_cues.append(
            SubtitleCue(
                start_seconds=window[0],
                end_seconds=window[1],
                text=narration,
                beat_type=beat_type,
                style_token=_resolve_subtitle_style_token(beat_type, brief.call_to_action),
            )
        )

    summary_parts = [brief.setup_fact, brief.climax_fact, brief.conclusion_fact]
    if brief.call_to_action:
        summary_parts.append(brief.call_to_action)

    conclusion_theme = CONCLUSION_CARD_THEMES[brief.style]
    conclusion_card = ConclusionCard(
        title=conclusion_theme["title"],
        body=brief.conclusion_fact,
        accent_label=brief.call_to_action or brief.climax_fact,
        theme=conclusion_theme["theme"],
    )

    return ContentPlan(
        topic=brief.topic,
        platform=brief.platform,
        style=brief.style,
        variant=variant,
        total_duration=brief.total_duration,
        hook=beats[0].narration,
        summary=" ".join(summary_parts),
        beats=beats,
        subtitle_cues=subtitle_cues,
        conclusion_card=conclusion_card,
        tags=brief.tags,
    )

