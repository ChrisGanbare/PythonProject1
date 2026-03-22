"""Render expression mapping tests."""

from __future__ import annotations

from shared.content.planner import build_content_plan
from shared.content.render_mapping import build_render_expression
from shared.content.schemas import ContentBrief, ContentStyle, ContentVariant


def test_build_render_expression_uses_content_plan_fields() -> None:
    plan = build_content_plan(
        ContentBrief(
            topic="贷款还款方式对比",
            platform="douyin",
            style=ContentStyle.TECH,
            variant=ContentVariant.SHORT,
            total_duration=30,
            hook_fact="先看最关键的问题",
            setup_fact="两组数据开始分叉",
            climax_fact="高潮数字已经出现",
            conclusion_fact="最后一句话给出判断",
            call_to_action="根据现金流做选择",
        )
    )

    expression = build_render_expression(plan)

    assert expression.title_text == plan.topic
    assert expression.hook_text == plan.hook
    assert expression.summary_text == plan.summary
    assert expression.conclusion_title == plan.conclusion_card.title
    assert expression.conclusion_body == plan.conclusion_card.body
    assert expression.accent_label == plan.conclusion_card.accent_label
    assert expression.style == plan.style
    assert expression.variant == plan.variant
    assert expression.theme.accent_color
    assert expression.theme.background_color
    assert expression.theme.panel_color
    assert expression.theme.title_color
    assert expression.theme.muted_text_color
    assert expression.theme.card_theme
    assert expression.typography.font_family
    assert expression.typography.font_fallbacks
    assert expression.typography.numeric_font_family
    assert expression.typography.title_weight
    assert expression.typography.body_weight
    assert expression.typography.title_line_height > 1.0
    assert expression.typography.body_line_height > 1.0
    assert expression.typography.title_size > expression.typography.body_size
    assert expression.typography.subtitle_size > expression.typography.caption_size
    assert expression.typography.title_scale > 0
    assert expression.card.background_color
    assert expression.card.title_color
    assert expression.card.body_color
    assert expression.card.badge_background_color
    assert expression.card.border_width > 0
    assert expression.card.boxstyle
    assert expression.safe_area.platform == plan.platform
    assert expression.safe_area.frame_width == 1080
    assert expression.safe_area.frame_height == 1920
    assert expression.safe_area.bottom_px == 300
    assert expression.safe_area.subtitle_band_top < 1.0
    assert expression.subtitle_layout.platform == plan.platform
    assert expression.subtitle_layout.anchor == "bottom"
    assert expression.subtitle_layout.max_lines == 3
    assert expression.subtitle_styles.hook_emphasis.style_token == "hook_emphasis"
    assert expression.subtitle_styles.hook_emphasis.font_family == expression.typography.numeric_font_family
    assert expression.subtitle_styles.climax_emphasis.text_color == expression.theme.accent_color
    assert expression.subtitle_styles.body_explainer.font_family == expression.typography.font_family
    assert expression.subtitle_cues[0].style_token == "hook_emphasis"
    assert expression.cover.title_text == plan.topic
    assert expression.cover.highlight_text == plan.conclusion_card.title
    assert expression.cover.eyebrow_text == plan.beats[0].headline
    assert expression.scene_behavior.hook_mode == "hero-spotlight"
    assert expression.scene_behavior.hook_support_density == "sparse"
    assert expression.scene_behavior.setup_density == "focused"
    assert expression.scene_behavior.comparison_window_months == 48
    assert expression.scene_behavior.conclusion_mode == "cta-spotlight"
    assert expression.scene_behavior.conclusion_reveal_order[0] == "headline"
    assert expression.scene_behavior.conclusion_card_scale > 1.0
    assert expression.layout.hook_layout == "hero"
    assert expression.layout.chart_focus == "single-compare"
    assert expression.layout.conclusion_layout == "spotlight-card"
    assert expression.visual_cues.hook_focus == "hero_number"
    assert expression.visual_cues.setup_focus == "single_comparison"
    assert expression.visual_cues.climax_focus == "gap_focus"
    assert expression.visual_cues.conclusion_focus == "cta_card"
    assert expression.visual_focus == "强结论卡片 + CTA"


def test_build_render_expression_maps_standard_variant_to_stacked_summary() -> None:
    plan = build_content_plan(
        ContentBrief(
            topic="基金费率长期影响",
            platform="bilibili_landscape",
            style=ContentStyle.NEWS,
            variant=ContentVariant.STANDARD,
            total_duration=90,
            hook_fact="先建立问题背景",
            setup_fact="完整展开关键数据",
            climax_fact="关键节点与累计差距开始明显",
            conclusion_fact="最后给出选择建议",
            call_to_action="关注长期费率",
        )
    )

    expression = build_render_expression(plan)

    assert expression.layout.hook_layout == "stacked"
    assert expression.layout.chart_focus == "trend-gap"
    assert expression.layout.conclusion_layout == "stacked-summary"
    assert expression.visual_cues.hook_focus == "problem_setup"
    assert expression.visual_cues.setup_focus == "full_context"
    assert expression.visual_cues.climax_focus == "milestone_gap"
    assert expression.visual_cues.conclusion_focus == "advice_card"
    assert expression.visual_focus == "完整展示关键比较过程"
    assert expression.typography.caption_line_height > 1.0
    assert expression.safe_area.platform == "bilibili_landscape"
    assert expression.safe_area.top_px == 80
    assert expression.safe_area.bottom_px == 80
    assert expression.safe_area.content_left == 0.0
    assert expression.subtitle_layout.max_lines == 2
    assert expression.subtitle_layout.bottom_px == 80
    assert expression.subtitle_styles.conclusion_summary.style_token == "conclusion_summary"
    assert expression.subtitle_styles.hook_emphasis.font_family == expression.typography.font_family
    assert expression.cover.layout in {"insight-board", "compact-spotlight", "stacked-hero"}
    assert expression.scene_behavior.hook_mode == "context-lead"
    assert expression.scene_behavior.setup_density == "full-context"
    assert expression.scene_behavior.show_reference_guides is True
    assert expression.scene_behavior.conclusion_mode == "advice-stack"


def test_build_render_expression_makes_short_variant_more_punchy_than_standard() -> None:
    brief = ContentBrief(
        topic="同一主题不同版本",
        platform="douyin",
        style=ContentStyle.TRENDY,
        total_duration=30,
        hook_fact="先把最猛的数字打出来",
        setup_fact="再补对比背景",
        climax_fact="关键差额数字继续放大",
        conclusion_fact="最后给出判断",
        call_to_action="继续看完整过程",
    )
    short_expression = build_render_expression(
        build_content_plan(brief.model_copy(update={"variant": ContentVariant.SHORT}))
    )
    standard_expression = build_render_expression(
        build_content_plan(
            brief.model_copy(update={"variant": ContentVariant.STANDARD, "total_duration": 90, "platform": "bilibili_landscape"})
        )
    )

    assert short_expression.typography.title_size > standard_expression.typography.title_size
    assert short_expression.typography.accent_scale > standard_expression.typography.accent_scale
    assert short_expression.card.fill_alpha >= standard_expression.card.fill_alpha
    assert short_expression.typography.font_family == standard_expression.typography.font_family
    assert short_expression.subtitle_styles.hook_emphasis.font_family == short_expression.typography.numeric_font_family
    assert short_expression.subtitle_styles.hook_emphasis.font_size > standard_expression.subtitle_styles.hook_emphasis.font_size

