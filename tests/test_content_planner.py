"""内容规划器测试。"""

from __future__ import annotations

from shared.content.planner import build_content_plan
from shared.content.rhythm import build_story_windows
from shared.content.schemas import ContentBrief, ContentStyle, ContentVariant, StoryBeatType


def test_build_story_windows_cover_total_duration() -> None:
    windows = build_story_windows(30)

    assert len(windows) == 4
    assert windows[0][0] == 0.0
    assert windows[-1][1] == 30.0
    assert all(start < end for start, end in windows)
    assert all(windows[index][1] == windows[index + 1][0] for index in range(len(windows) - 1))


def test_build_content_plan_generates_four_beats() -> None:
    brief = ContentBrief(
        topic="测试主题",
        platform="douyin",
        style=ContentStyle.TECH,
        total_duration=30,
        hook_fact="先把问题抛出来",
        setup_fact="数据开始拉开差距",
        climax_fact="高潮数字已经出现",
        conclusion_fact="最后给出决策建议",
        tags=["测试"],
    )

    plan = build_content_plan(brief)

    assert plan.topic == "测试主题"
    assert plan.style == ContentStyle.TECH
    assert len(plan.beats) == 4
    assert len(plan.subtitle_cues) == 4
    assert [beat.beat_type for beat in plan.beats] == [
        StoryBeatType.HOOK,
        StoryBeatType.SETUP,
        StoryBeatType.CLIMAX,
        StoryBeatType.CONCLUSION,
    ]
    assert [cue.beat_type for cue in plan.subtitle_cues] == [
        StoryBeatType.HOOK,
        StoryBeatType.SETUP,
        StoryBeatType.CLIMAX,
        StoryBeatType.CONCLUSION,
    ]
    assert plan.hook.startswith("先把结论砸出来")
    assert len(plan.to_subtitle_items()) == 4
    assert plan.to_subtitle_items()[0]["style_token"] == "hook_emphasis"
    assert plan.tags == ["测试"]


def test_build_story_windows_supports_short_variant() -> None:
    short_windows = build_story_windows(30, variant=ContentVariant.SHORT)
    standard_windows = build_story_windows(90, variant=ContentVariant.STANDARD)

    assert short_windows[1][1] < standard_windows[1][1]
    assert short_windows[-1][1] == 30.0
    assert standard_windows[-1][1] == 90.0


def test_build_content_plan_uses_platform_hook_and_variant() -> None:
    brief = ContentBrief(
        topic="平台钩子测试",
        platform="douyin",
        style=ContentStyle.TRENDY,
        variant=ContentVariant.SHORT,
        total_duration=30,
        hook_fact="这个差距真的不小",
        setup_fact="先把背景交代清楚",
        climax_fact="高潮数字已经出现",
        conclusion_fact="一句话给出判断",
    )

    plan = build_content_plan(brief)

    assert plan.variant == ContentVariant.SHORT
    assert plan.hook.startswith("别划走")
    assert plan.beats[0].visual_hint is not None
    assert plan.conclusion_card.title
    assert plan.conclusion_card.theme
    assert plan.subtitle_cues[-1].style_token == "conclusion_summary"


def test_build_content_plan_maps_call_to_action_to_conclusion_cta_subtitle() -> None:
    brief = ContentBrief(
        topic="CTA 字幕映射",
        platform="douyin",
        style=ContentStyle.NEWS,
        total_duration=30,
        hook_fact="先抛结论",
        setup_fact="补充背景",
        climax_fact="给出关键数字",
        conclusion_fact="最后总结",
        call_to_action="关注后续系列",
    )

    plan = build_content_plan(brief)

    assert plan.subtitle_cues[-1].style_token == "conclusion_cta"
    items = plan.to_subtitle_items()
    assert items[-1]["beat_type"] == "conclusion"
    assert items[-1]["style_token"] == "conclusion_cta"


