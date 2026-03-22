"""内容方案到渲染表达的映射层。"""

from __future__ import annotations

from pydantic import BaseModel

from shared.content.schemas import ContentPlan, ContentStyle, ContentVariant, StoryBeatType, SubtitleCue
from shared.content.render_timeline import RenderTimeline
from shared.content.themes import get_style_theme_preset
from shared.platform.presets import get_platform_preset


class ThemeTokens(BaseModel):
    """渲染层可直接消费的主题令牌。"""

    theme_name: str
    accent_color: str
    secondary_color: str
    background_color: str
    panel_color: str
    panel_alt_color: str
    muted_text_color: str
    title_color: str
    body_color: str
    cta_color: str
    card_theme: str


class TypographyTokens(BaseModel):
    """标题层级和字号缩放令牌。"""

    font_family: str
    font_fallbacks: list[str]
    numeric_font_family: str
    numeric_font_fallbacks: list[str]
    title_size: int
    subtitle_size: int
    body_size: int
    caption_size: int
    title_weight: str
    subtitle_weight: str
    body_weight: str
    caption_weight: str
    title_line_height: float
    body_line_height: float
    caption_line_height: float
    title_letter_spacing: float
    caption_letter_spacing: float
    title_scale: float
    summary_scale: float
    accent_scale: float
    conclusion_scale: float


class CardTokens(BaseModel):
    """卡片外观令牌。"""

    background_color: str
    border_color: str
    title_color: str
    body_color: str
    accent_color: str
    badge_background_color: str
    border_width: float
    boxstyle: str
    fill_alpha: float


class LayoutTokens(BaseModel):
    """渲染布局提示。"""

    hook_layout: str
    chart_focus: str
    conclusion_layout: str


class VisualCueTokens(BaseModel):
    """将自然语言 visual_hint 归一化后的视觉提示。"""

    hook_focus: str
    setup_focus: str
    climax_focus: str
    conclusion_focus: str


class SceneBehaviorTokens(BaseModel):
    """由 visual cues 派生的场景行为令牌。"""

    hook_mode: str
    hook_support_density: str
    setup_density: str
    comparison_window_months: int
    show_reference_guides: bool
    conclusion_mode: str
    conclusion_reveal_order: list[str]
    conclusion_card_scale: float


class SafeAreaTokens(BaseModel):
    """平台安全区令牌。"""

    platform: str
    orientation: str
    frame_width: int
    frame_height: int
    top_px: int
    bottom_px: int
    left_px: int
    right_px: int
    top_ratio: float
    bottom_ratio: float
    left_ratio: float
    right_ratio: float
    content_top: float
    content_bottom: float
    content_left: float
    content_right: float
    subtitle_band_top: float


class CoverTemplateTokens(BaseModel):
    """封面模板令牌。"""

    eyebrow_text: str
    title_text: str
    highlight_text: str
    summary_text: str
    layout: str
    use_video_frame_background: bool


class SubtitleLayoutTokens(BaseModel):
    """字幕布局令牌。"""

    platform: str
    align: str
    anchor: str
    bottom_px: int
    bottom_ratio: float
    max_width_ratio: float
    max_lines: int
    safe_left_ratio: float
    safe_right_ratio: float
    subtitle_band_top: float


class SceneCopyBandModeTokens(BaseModel):
    """Scene copy band 单模式布局令牌。"""

    x: int
    y: int
    w: int
    h: int
    label_y: int
    headline_y: int
    detail_y: int
    headline_scale: float
    detail_scale: float


class SceneCopyBandTokens(BaseModel):
    """Scene copy band 平台适配布局令牌。"""

    platform: str
    orientation: str
    safe_top_ratio: float
    safe_bottom_ratio: float
    safe_left_ratio: float
    safe_right_ratio: float
    side_padding_ratio: float
    background_color: str
    border_color: str
    label_color: str
    accent_color: str
    headline_color: str
    detail_color: str
    border_width: float
    full_fill_alpha: float
    compact_fill_alpha: float
    full: SceneCopyBandModeTokens
    compact: SceneCopyBandModeTokens


class SubtitleRoleStyleTokens(BaseModel):
    """单类字幕样式令牌。"""

    style_token: str
    font_family: str
    font_size: int
    font_weight: str
    text_color: str
    stroke_color: str
    stroke_width: float
    line_height: float
    background_alpha: float


class SubtitleStylesTokens(BaseModel):
    """不同字幕角色的样式集合。"""

    hook_emphasis: SubtitleRoleStyleTokens
    body_explainer: SubtitleRoleStyleTokens
    climax_emphasis: SubtitleRoleStyleTokens
    conclusion_summary: SubtitleRoleStyleTokens
    conclusion_cta: SubtitleRoleStyleTokens


class RenderExpression(BaseModel):
    """由内容规划生成的渲染表达配置。"""

    title_text: str
    hook_text: str
    summary_text: str
    conclusion_title: str
    conclusion_body: str
    accent_label: str
    style: ContentStyle
    variant: ContentVariant
    theme: ThemeTokens
    typography: TypographyTokens
    card: CardTokens
    layout: LayoutTokens
    visual_cues: VisualCueTokens
    scene_behavior: SceneBehaviorTokens
    safe_area: SafeAreaTokens
    scene_copy_band: SceneCopyBandTokens
    cover: CoverTemplateTokens
    subtitle_layout: SubtitleLayoutTokens
    subtitle_styles: SubtitleStylesTokens
    subtitle_cues: list[SubtitleCue]
    visual_focus: str
    timeline: RenderTimeline | None = None


def _build_theme_tokens(style: ContentStyle) -> ThemeTokens:
    preset = get_style_theme_preset(style)
    return ThemeTokens(
        theme_name=preset.theme_name,
        accent_color=preset.accent_color,
        secondary_color=preset.secondary_color,
        background_color=preset.background_color,
        panel_color=preset.panel_color,
        panel_alt_color=preset.panel_alt_color,
        muted_text_color=preset.muted_text_color,
        title_color=preset.title_color,
        body_color=preset.body_color,
        cta_color=preset.cta_color,
        card_theme=preset.theme_name,
    )


def _build_typography_tokens(style: ContentStyle, variant: ContentVariant) -> TypographyTokens:
    preset = get_style_theme_preset(style)
    typography = preset.typography
    if variant is ContentVariant.SHORT:
        title_size = typography.title_size + 6
        subtitle_size = typography.subtitle_size + 2
        body_size = max(typography.body_size - 1, 16)
        caption_size = typography.caption_size
        title_scale = typography.title_scale + 0.05
        summary_scale = max(0.82, typography.summary_scale - 0.02)
        accent_scale = typography.accent_scale + 0.05
        conclusion_scale = typography.conclusion_scale + 0.06
    else:
        title_size = typography.title_size
        subtitle_size = typography.subtitle_size
        body_size = typography.body_size + 1
        caption_size = typography.caption_size + 1
        title_scale = typography.title_scale
        summary_scale = typography.summary_scale + 0.02
        accent_scale = typography.accent_scale
        conclusion_scale = typography.conclusion_scale

    return TypographyTokens(
        font_family=typography.font_family,
        font_fallbacks=list(typography.font_fallbacks),
        numeric_font_family=typography.numeric_font_family,
        numeric_font_fallbacks=list(typography.numeric_font_fallbacks),
        title_size=title_size,
        subtitle_size=subtitle_size,
        body_size=body_size,
        caption_size=caption_size,
        title_weight=typography.title_weight,
        subtitle_weight=typography.subtitle_weight,
        body_weight=typography.body_weight,
        caption_weight=typography.caption_weight,
        title_line_height=typography.title_line_height,
        body_line_height=typography.body_line_height,
        caption_line_height=typography.caption_line_height,
        title_letter_spacing=typography.title_letter_spacing,
        caption_letter_spacing=typography.caption_letter_spacing,
        title_scale=title_scale,
        summary_scale=summary_scale,
        accent_scale=accent_scale,
        conclusion_scale=conclusion_scale,
    )


def _build_card_tokens(style: ContentStyle, variant: ContentVariant) -> CardTokens:
    preset = get_style_theme_preset(style)
    card_theme = preset.card_theme
    border_width = card_theme.border_width + (0.2 if variant is ContentVariant.SHORT else 0.0)
    fill_alpha = min(0.98, card_theme.fill_alpha + (0.02 if variant is ContentVariant.SHORT else 0.0))
    return CardTokens(
        background_color=card_theme.background_color,
        border_color=card_theme.border_color,
        title_color=card_theme.title_color,
        body_color=card_theme.body_color,
        accent_color=card_theme.accent_color,
        badge_background_color=card_theme.badge_background_color,
        border_width=border_width,
        boxstyle=card_theme.boxstyle,
        fill_alpha=fill_alpha,
    )


def _normalize_visual_hint(beat_type: StoryBeatType, hint: str | None) -> str:
    text = (hint or "").strip()
    if beat_type is StoryBeatType.HOOK:
        if "大字" in text or "冲击" in text:
            return "hero_number"
        if "问题" in text or "冲突" in text:
            return "problem_setup"
        return "headline_focus"

    if beat_type is StoryBeatType.SETUP:
        if "核心对比图" in text:
            return "single_comparison"
        if "完整展示" in text:
            return "full_context"
        return "comparison_flow"

    if beat_type is StoryBeatType.CLIMAX:
        if "差额数字" in text or "趋势拐点" in text:
            return "gap_focus"
        if "关键节点" in text or "累计差距" in text:
            return "milestone_gap"
        return "highlight_peak"

    if "强结论卡片" in text:
        return "cta_card"
    if "选择建议" in text:
        return "advice_card"
    return "summary_card"


def _build_visual_cues(plan: ContentPlan) -> VisualCueTokens:
    beat_map = {beat.beat_type: beat for beat in plan.beats}
    return VisualCueTokens(
        hook_focus=_normalize_visual_hint(StoryBeatType.HOOK, beat_map.get(StoryBeatType.HOOK).visual_hint if beat_map.get(StoryBeatType.HOOK) else None),
        setup_focus=_normalize_visual_hint(StoryBeatType.SETUP, beat_map.get(StoryBeatType.SETUP).visual_hint if beat_map.get(StoryBeatType.SETUP) else None),
        climax_focus=_normalize_visual_hint(StoryBeatType.CLIMAX, beat_map.get(StoryBeatType.CLIMAX).visual_hint if beat_map.get(StoryBeatType.CLIMAX) else None),
        conclusion_focus=_normalize_visual_hint(StoryBeatType.CONCLUSION, beat_map.get(StoryBeatType.CONCLUSION).visual_hint if beat_map.get(StoryBeatType.CONCLUSION) else None),
    )


def _build_layout_tokens(variant: ContentVariant, visual_cues: VisualCueTokens) -> LayoutTokens:
    hook_layout = "hero" if visual_cues.hook_focus == "hero_number" else "stacked"

    if visual_cues.setup_focus == "single_comparison":
        chart_focus = "single-compare"
    elif visual_cues.climax_focus in {"gap_focus", "milestone_gap"}:
        chart_focus = "trend-gap"
    else:
        chart_focus = "balanced"

    if visual_cues.conclusion_focus == "cta_card":
        conclusion_layout = "spotlight-card"
    elif variant is ContentVariant.SHORT:
        conclusion_layout = "summary-band"
    else:
        conclusion_layout = "stacked-summary"

    return LayoutTokens(
        hook_layout=hook_layout,
        chart_focus=chart_focus,
        conclusion_layout=conclusion_layout,
    )


def _build_visual_focus(variant: ContentVariant, visual_cues: VisualCueTokens) -> str:
    if visual_cues.conclusion_focus == "cta_card":
        return "强结论卡片 + CTA"
    if visual_cues.hook_focus == "hero_number":
        return "大字数字冲击 + 快速入场"
    if visual_cues.setup_focus == "full_context" or variant is ContentVariant.STANDARD:
        return "完整展示关键比较过程"
    if visual_cues.climax_focus in {"gap_focus", "milestone_gap"}:
        return "关键差额数字高亮"
    return "对比路径清晰展开"


def _build_scene_behavior(variant: ContentVariant, visual_cues: VisualCueTokens) -> SceneBehaviorTokens:
    hook_mode = "hero-spotlight" if visual_cues.hook_focus == "hero_number" else "context-lead"
    hook_support_density = "sparse" if visual_cues.hook_focus == "hero_number" else "balanced"

    if visual_cues.setup_focus == "full_context":
        setup_density = "full-context"
        comparison_window_months = 96
    elif visual_cues.setup_focus == "single_comparison":
        setup_density = "focused"
        comparison_window_months = 48
    else:
        setup_density = "balanced"
        comparison_window_months = 60 if variant is ContentVariant.SHORT else 72

    show_reference_guides = visual_cues.setup_focus == "full_context" or visual_cues.climax_focus == "milestone_gap"

    if visual_cues.conclusion_focus == "cta_card":
        conclusion_mode = "cta-spotlight"
        conclusion_reveal_order = ["headline", "summary", "highlight_card", "cta_footer"]
        conclusion_card_scale = 1.12 if variant is ContentVariant.SHORT else 1.06
    elif visual_cues.conclusion_focus == "advice_card":
        conclusion_mode = "advice-stack"
        conclusion_reveal_order = ["headline", "comparison_rows", "body", "badge"]
        conclusion_card_scale = 0.98
    else:
        conclusion_mode = "summary-band"
        conclusion_reveal_order = ["headline", "body", "badge", "footer"]
        conclusion_card_scale = 1.0

    return SceneBehaviorTokens(
        hook_mode=hook_mode,
        hook_support_density=hook_support_density,
        setup_density=setup_density,
        comparison_window_months=comparison_window_months,
        show_reference_guides=show_reference_guides,
        conclusion_mode=conclusion_mode,
        conclusion_reveal_order=conclusion_reveal_order,
        conclusion_card_scale=conclusion_card_scale,
    )


def _build_cover_tokens(
    plan: ContentPlan,
    visual_focus: str,
    visual_cues: VisualCueTokens,
) -> CoverTemplateTokens:
    if visual_cues.hook_focus == "hero_number":
        layout = "stacked-hero"
    elif plan.variant is ContentVariant.SHORT:
        layout = "compact-spotlight"
    else:
        layout = "insight-board"

    summary_text = plan.conclusion_card.accent_label or visual_focus
    if len(summary_text) > 30:
        summary_text = summary_text[:30].rstrip() + "…"

    return CoverTemplateTokens(
        eyebrow_text=plan.beats[0].headline if plan.beats else visual_focus,
        title_text=plan.topic,
        highlight_text=plan.conclusion_card.title,
        summary_text=summary_text,
        layout=layout,
        use_video_frame_background=plan.style in {ContentStyle.NEWS, ContentStyle.TRENDY},
    )


def _build_safe_area_tokens(platform: str) -> SafeAreaTokens:
    preset = get_platform_preset(platform)
    return SafeAreaTokens(**preset.to_safe_area_dict())


def _build_subtitle_layout_tokens(platform: str) -> SubtitleLayoutTokens:
    preset = get_platform_preset(platform)
    return SubtitleLayoutTokens(**preset.to_subtitle_layout_dict())


def _build_scene_copy_band_tokens(platform: str, theme: ThemeTokens, card: CardTokens) -> SceneCopyBandTokens:
    preset = get_platform_preset(platform)
    payload = dict(preset.to_scene_copy_band_dict())
    payload.update(
        {
            "background_color": card.background_color,
            "border_color": card.border_color,
            "label_color": card.accent_color,
            "accent_color": theme.cta_color,
            "headline_color": theme.title_color,
            "detail_color": card.body_color,
            "border_width": card.border_width,
            "full_fill_alpha": min(0.98, card.fill_alpha + 0.02),
            "compact_fill_alpha": min(1.0, card.fill_alpha + 0.06),
        }
    )
    return SceneCopyBandTokens(**payload)


def _normalize_font_weight(weight: str) -> str:
    return "normal" if weight == "regular" else weight


def _resolve_subtitle_font_family(typography: TypographyTokens, font_role: str) -> str:
    if font_role == "numeric":
        return typography.numeric_font_family
    return typography.font_family


def _resolve_subtitle_font_size(typography: TypographyTokens, size_role: str) -> int:
    size_map = {
        "title": typography.title_size,
        "subtitle": typography.subtitle_size,
        "body": max(18, typography.body_size),
        "caption": max(16, typography.caption_size + 2),
    }
    return int(size_map.get(size_role, max(18, typography.body_size)))


def _resolve_subtitle_font_weight(typography: TypographyTokens, weight_role: str) -> str:
    weight_map = {
        "title": typography.title_weight,
        "subtitle": typography.subtitle_weight,
        "body": typography.body_weight,
        "caption": typography.caption_weight,
    }
    return _normalize_font_weight(weight_map.get(weight_role, typography.body_weight))


def _resolve_subtitle_line_height(typography: TypographyTokens, line_height_role: str) -> float:
    line_height_map = {
        "title": typography.title_line_height,
        "body": typography.body_line_height,
        "caption": typography.caption_line_height,
    }
    return float(line_height_map.get(line_height_role, typography.body_line_height))


def _resolve_theme_color(theme: ThemeTokens, color_role: str) -> str:
    return str(getattr(theme, color_role, theme.body_color))


def _build_subtitle_role_style(
    *,
    style_token: str,
    role_theme,
    theme: ThemeTokens,
    typography: TypographyTokens,
) -> SubtitleRoleStyleTokens:
    base_size = _resolve_subtitle_font_size(typography, role_theme.size_role)
    font_size = max(16, int(round(base_size * role_theme.size_multiplier)) + role_theme.size_delta)
    return SubtitleRoleStyleTokens(
        style_token=style_token,
        font_family=_resolve_subtitle_font_family(typography, role_theme.font_role),
        font_size=font_size,
        font_weight=_resolve_subtitle_font_weight(typography, role_theme.weight_role),
        text_color=_resolve_theme_color(theme, role_theme.text_color_role),
        stroke_color=_resolve_theme_color(theme, role_theme.stroke_color_role),
        stroke_width=role_theme.stroke_width,
        line_height=_resolve_subtitle_line_height(typography, role_theme.line_height_role),
        background_alpha=role_theme.background_alpha,
    )


def _build_subtitle_styles(style: ContentStyle, theme: ThemeTokens, typography: TypographyTokens) -> SubtitleStylesTokens:
    subtitle_theme = get_style_theme_preset(style).subtitle_theme
    return SubtitleStylesTokens(
        hook_emphasis=_build_subtitle_role_style(
            style_token="hook_emphasis",
            role_theme=subtitle_theme.hook_emphasis,
            theme=theme,
            typography=typography,
        ),
        body_explainer=_build_subtitle_role_style(
            style_token="body_explainer",
            role_theme=subtitle_theme.body_explainer,
            theme=theme,
            typography=typography,
        ),
        climax_emphasis=_build_subtitle_role_style(
            style_token="climax_emphasis",
            role_theme=subtitle_theme.climax_emphasis,
            theme=theme,
            typography=typography,
        ),
        conclusion_summary=_build_subtitle_role_style(
            style_token="conclusion_summary",
            role_theme=subtitle_theme.conclusion_summary,
            theme=theme,
            typography=typography,
        ),
        conclusion_cta=_build_subtitle_role_style(
            style_token="conclusion_cta",
            role_theme=subtitle_theme.conclusion_cta,
            theme=theme,
            typography=typography,
        ),
    )


def build_render_expression(plan: ContentPlan) -> RenderExpression:
    """将内容方案映射为渲染层可直接消费的表达配置。"""
    theme = _build_theme_tokens(plan.style)
    typography = _build_typography_tokens(plan.style, plan.variant)
    card = _build_card_tokens(plan.style, plan.variant)
    visual_cues = _build_visual_cues(plan)
    layout = _build_layout_tokens(plan.variant, visual_cues)
    scene_behavior = _build_scene_behavior(plan.variant, visual_cues)
    safe_area = _build_safe_area_tokens(plan.platform)
    scene_copy_band = _build_scene_copy_band_tokens(plan.platform, theme, card)
    subtitle_layout = _build_subtitle_layout_tokens(plan.platform)
    subtitle_styles = _build_subtitle_styles(plan.style, theme, typography)
    visual_focus = _build_visual_focus(plan.variant, visual_cues)
    cover = _build_cover_tokens(plan, visual_focus, visual_cues)
    return RenderExpression(
        title_text=plan.topic,
        hook_text=plan.hook,
        summary_text=plan.summary,
        conclusion_title=plan.conclusion_card.title,
        conclusion_body=plan.conclusion_card.body,
        accent_label=plan.conclusion_card.accent_label,
        style=plan.style,
        variant=plan.variant,
        theme=theme,
        typography=typography,
        card=card,
        layout=layout,
        visual_cues=visual_cues,
        scene_behavior=scene_behavior,
        safe_area=safe_area,
        scene_copy_band=scene_copy_band,
        cover=cover,
        subtitle_layout=subtitle_layout,
        subtitle_styles=subtitle_styles,
        subtitle_cues=list(plan.subtitle_cues),
        visual_focus=visual_focus,
    )

