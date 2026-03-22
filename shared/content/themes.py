"""共享视觉主题资产库。"""

from __future__ import annotations

from pydantic import BaseModel

from shared.content.schemas import ContentStyle


class TypographyScale(BaseModel):
    """风格级排版基线。"""

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


class CardTheme(BaseModel):
    """卡片样式资产。"""

    background_color: str
    border_color: str
    title_color: str
    body_color: str
    accent_color: str
    badge_background_color: str
    border_width: float
    boxstyle: str
    fill_alpha: float


class SubtitleRoleTheme(BaseModel):
    """单类字幕角色的主题模板。"""

    font_role: str
    size_role: str
    size_delta: int = 0
    size_multiplier: float = 1.0
    weight_role: str
    text_color_role: str
    stroke_color_role: str = "background_color"
    line_height_role: str
    stroke_width: float
    background_alpha: float


class SubtitleTheme(BaseModel):
    """按字幕角色拆分的字幕主题模板。"""

    hook_emphasis: SubtitleRoleTheme
    body_explainer: SubtitleRoleTheme
    climax_emphasis: SubtitleRoleTheme
    conclusion_summary: SubtitleRoleTheme
    conclusion_cta: SubtitleRoleTheme


class StyleThemePreset(BaseModel):
    """单个内容风格对应的一整套视觉预设。"""

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
    card_theme: CardTheme
    typography: TypographyScale
    subtitle_theme: SubtitleTheme


STYLE_THEME_PRESETS: dict[ContentStyle, StyleThemePreset] = {
    ContentStyle.MINIMAL: StyleThemePreset(
        theme_name="clean-slate",
        accent_color="#E2E8F0",
        secondary_color="#94A3B8",
        background_color="#0B1120",
        panel_color="#111827",
        panel_alt_color="#0F172A",
        muted_text_color="#94A3B8",
        title_color="#F8FAFC",
        body_color="#CBD5E1",
        cta_color="#E2E8F0",
        card_theme=CardTheme(
            background_color="#111827",
            border_color="#CBD5E1",
            title_color="#F8FAFC",
            body_color="#CBD5E1",
            accent_color="#E2E8F0",
            badge_background_color="#1E293B",
            border_width=1.4,
            boxstyle="round,pad=0.28",
            fill_alpha=0.84,
        ),
        typography=TypographyScale(
            font_family="Source Han Sans SC",
            font_fallbacks=["Noto Sans CJK SC", "Microsoft YaHei", "PingFang SC", "SimHei", "DejaVu Sans"],
            numeric_font_family="Inter",
            numeric_font_fallbacks=["DIN Condensed", "Arial", "DejaVu Sans"],
            title_size=56,
            subtitle_size=28,
            body_size=20,
            caption_size=15,
            title_weight="bold",
            subtitle_weight="semibold",
            body_weight="regular",
            caption_weight="regular",
            title_line_height=1.18,
            body_line_height=1.50,
            caption_line_height=1.28,
            title_letter_spacing=0.0,
            caption_letter_spacing=0.01,
            title_scale=0.96,
            summary_scale=0.90,
            accent_scale=0.90,
            conclusion_scale=0.98,
        ),
        subtitle_theme=SubtitleTheme(
            hook_emphasis=SubtitleRoleTheme(
                font_role="primary",
                size_role="subtitle",
                weight_role="subtitle",
                text_color_role="title_color",
                line_height_role="title",
                stroke_width=2.4,
                background_alpha=0.18,
            ),
            body_explainer=SubtitleRoleTheme(
                font_role="primary",
                size_role="body",
                weight_role="body",
                text_color_role="body_color",
                line_height_role="body",
                stroke_width=2.0,
                background_alpha=0.14,
            ),
            climax_emphasis=SubtitleRoleTheme(
                font_role="primary",
                size_role="subtitle",
                weight_role="subtitle",
                text_color_role="secondary_color",
                line_height_role="title",
                stroke_width=2.4,
                background_alpha=0.18,
            ),
            conclusion_summary=SubtitleRoleTheme(
                font_role="primary",
                size_role="caption",
                weight_role="caption",
                text_color_role="body_color",
                line_height_role="caption",
                stroke_width=1.8,
                background_alpha=0.12,
            ),
            conclusion_cta=SubtitleRoleTheme(
                font_role="primary",
                size_role="caption",
                size_delta=1,
                weight_role="subtitle",
                text_color_role="cta_color",
                line_height_role="caption",
                stroke_width=1.8,
                background_alpha=0.14,
            ),
        ),
    ),
    ContentStyle.TECH: StyleThemePreset(
        theme_name="tech-blue",
        accent_color="#4F9EFF",
        secondary_color="#22D47E",
        background_color="#0D0D1A",
        panel_color="#12122A",
        panel_alt_color="#1A2040",
        muted_text_color="#94A3B8",
        title_color="#FFFFFF",
        body_color="#E2E8F0",
        cta_color="#FBBF24",
        card_theme=CardTheme(
            background_color="#1C1C3A",
            border_color="#4F9EFF",
            title_color="#FFFFFF",
            body_color="#CBD5E1",
            accent_color="#4F9EFF",
            badge_background_color="#1E3A8A",
            border_width=2.2,
            boxstyle="round,pad=0.34",
            fill_alpha=0.92,
        ),
        typography=TypographyScale(
            font_family="Source Han Sans SC",
            font_fallbacks=["Noto Sans CJK SC", "Microsoft YaHei", "PingFang SC", "SimHei", "DejaVu Sans"],
            numeric_font_family="Inter",
            numeric_font_fallbacks=["DIN Condensed", "Arial", "DejaVu Sans"],
            title_size=60,
            subtitle_size=32,
            body_size=22,
            caption_size=16,
            title_weight="bold",
            subtitle_weight="bold",
            body_weight="medium",
            caption_weight="regular",
            title_line_height=1.16,
            body_line_height=1.46,
            caption_line_height=1.24,
            title_letter_spacing=0.01,
            caption_letter_spacing=0.02,
            title_scale=1.06,
            summary_scale=0.96,
            accent_scale=0.98,
            conclusion_scale=1.04,
        ),
        subtitle_theme=SubtitleTheme(
            hook_emphasis=SubtitleRoleTheme(
                font_role="numeric",
                size_role="subtitle",
                size_multiplier=1.04,
                weight_role="subtitle",
                text_color_role="title_color",
                line_height_role="title",
                stroke_width=2.8,
                background_alpha=0.24,
            ),
            body_explainer=SubtitleRoleTheme(
                font_role="primary",
                size_role="body",
                weight_role="body",
                text_color_role="body_color",
                line_height_role="body",
                stroke_width=2.2,
                background_alpha=0.18,
            ),
            climax_emphasis=SubtitleRoleTheme(
                font_role="numeric",
                size_role="subtitle",
                size_delta=2,
                size_multiplier=1.04,
                weight_role="subtitle",
                text_color_role="accent_color",
                line_height_role="title",
                stroke_width=3.0,
                background_alpha=0.22,
            ),
            conclusion_summary=SubtitleRoleTheme(
                font_role="primary",
                size_role="caption",
                weight_role="caption",
                text_color_role="body_color",
                line_height_role="caption",
                stroke_width=2.0,
                background_alpha=0.18,
            ),
            conclusion_cta=SubtitleRoleTheme(
                font_role="primary",
                size_role="caption",
                size_delta=1,
                weight_role="subtitle",
                text_color_role="cta_color",
                line_height_role="caption",
                stroke_width=2.0,
                background_alpha=0.20,
            ),
        ),
    ),
    ContentStyle.NEWS: StyleThemePreset(
        theme_name="news-red",
        accent_color="#F43F5E",
        secondary_color="#FBBF24",
        background_color="#111827",
        panel_color="#1F2937",
        panel_alt_color="#172033",
        muted_text_color="#9CA3AF",
        title_color="#F9FAFB",
        body_color="#E5E7EB",
        cta_color="#F43F5E",
        card_theme=CardTheme(
            background_color="#1F2937",
            border_color="#F43F5E",
            title_color="#F9FAFB",
            body_color="#E5E7EB",
            accent_color="#F43F5E",
            badge_background_color="#7F1D1D",
            border_width=2.0,
            boxstyle="round,pad=0.28",
            fill_alpha=0.90,
        ),
        typography=TypographyScale(
            font_family="Source Han Sans SC",
            font_fallbacks=["Noto Sans CJK SC", "Microsoft YaHei", "PingFang SC", "SimHei", "DejaVu Sans"],
            numeric_font_family="Inter",
            numeric_font_fallbacks=["DIN Condensed", "Arial", "DejaVu Sans"],
            title_size=58,
            subtitle_size=30,
            body_size=22,
            caption_size=16,
            title_weight="bold",
            subtitle_weight="semibold",
            body_weight="regular",
            caption_weight="regular",
            title_line_height=1.20,
            body_line_height=1.48,
            caption_line_height=1.26,
            title_letter_spacing=0.0,
            caption_letter_spacing=0.01,
            title_scale=1.00,
            summary_scale=0.92,
            accent_scale=0.90,
            conclusion_scale=1.00,
        ),
        subtitle_theme=SubtitleTheme(
            hook_emphasis=SubtitleRoleTheme(
                font_role="primary",
                size_role="subtitle",
                size_multiplier=1.02,
                weight_role="subtitle",
                text_color_role="title_color",
                line_height_role="title",
                stroke_width=2.6,
                background_alpha=0.20,
            ),
            body_explainer=SubtitleRoleTheme(
                font_role="primary",
                size_role="body",
                weight_role="body",
                text_color_role="body_color",
                line_height_role="body",
                stroke_width=2.1,
                background_alpha=0.16,
            ),
            climax_emphasis=SubtitleRoleTheme(
                font_role="primary",
                size_role="subtitle",
                size_delta=1,
                weight_role="subtitle",
                text_color_role="accent_color",
                line_height_role="title",
                stroke_width=2.8,
                background_alpha=0.20,
            ),
            conclusion_summary=SubtitleRoleTheme(
                font_role="primary",
                size_role="caption",
                weight_role="caption",
                text_color_role="body_color",
                line_height_role="caption",
                stroke_width=1.9,
                background_alpha=0.14,
            ),
            conclusion_cta=SubtitleRoleTheme(
                font_role="primary",
                size_role="caption",
                size_delta=1,
                weight_role="subtitle",
                text_color_role="cta_color",
                line_height_role="caption",
                stroke_width=2.0,
                background_alpha=0.16,
            ),
        ),
    ),
    ContentStyle.TRENDY: StyleThemePreset(
        theme_name="neon-pop",
        accent_color="#EC4899",
        secondary_color="#FBBF24",
        background_color="#140A1F",
        panel_color="#251236",
        panel_alt_color="#33194A",
        muted_text_color="#C4B5FD",
        title_color="#FFF7ED",
        body_color="#F5D0FE",
        cta_color="#FBBF24",
        card_theme=CardTheme(
            background_color="#251236",
            border_color="#EC4899",
            title_color="#FFF7ED",
            body_color="#F5D0FE",
            accent_color="#EC4899",
            badge_background_color="#9D174D",
            border_width=2.6,
            boxstyle="round,pad=0.42",
            fill_alpha=0.94,
        ),
        typography=TypographyScale(
            font_family="Alibaba PuHuiTi 2.0",
            font_fallbacks=["Source Han Sans SC", "Noto Sans CJK SC", "Microsoft YaHei", "PingFang SC", "DejaVu Sans"],
            numeric_font_family="DIN Condensed",
            numeric_font_fallbacks=["Inter", "Arial", "DejaVu Sans"],
            title_size=62,
            subtitle_size=33,
            body_size=22,
            caption_size=16,
            title_weight="bold",
            subtitle_weight="bold",
            body_weight="medium",
            caption_weight="medium",
            title_line_height=1.14,
            body_line_height=1.42,
            caption_line_height=1.22,
            title_letter_spacing=0.02,
            caption_letter_spacing=0.03,
            title_scale=1.10,
            summary_scale=0.98,
            accent_scale=1.02,
            conclusion_scale=1.08,
        ),
        subtitle_theme=SubtitleTheme(
            hook_emphasis=SubtitleRoleTheme(
                font_role="numeric",
                size_role="subtitle",
                size_delta=1,
                size_multiplier=1.08,
                weight_role="subtitle",
                text_color_role="title_color",
                line_height_role="title",
                stroke_width=2.8,
                background_alpha=0.28,
            ),
            body_explainer=SubtitleRoleTheme(
                font_role="primary",
                size_role="body",
                weight_role="body",
                text_color_role="body_color",
                line_height_role="body",
                stroke_width=2.3,
                background_alpha=0.20,
            ),
            climax_emphasis=SubtitleRoleTheme(
                font_role="numeric",
                size_role="subtitle",
                size_delta=2,
                size_multiplier=1.08,
                weight_role="subtitle",
                text_color_role="accent_color",
                line_height_role="title",
                stroke_width=3.0,
                background_alpha=0.24,
            ),
            conclusion_summary=SubtitleRoleTheme(
                font_role="primary",
                size_role="caption",
                size_delta=1,
                weight_role="caption",
                text_color_role="body_color",
                line_height_role="caption",
                stroke_width=2.0,
                background_alpha=0.18,
            ),
            conclusion_cta=SubtitleRoleTheme(
                font_role="numeric",
                size_role="caption",
                size_delta=2,
                weight_role="subtitle",
                text_color_role="cta_color",
                line_height_role="caption",
                stroke_width=2.2,
                background_alpha=0.22,
            ),
        ),
    ),
}


def get_style_theme_preset(style: ContentStyle) -> StyleThemePreset:
    """获取指定风格的共享视觉预设。"""

    return STYLE_THEME_PRESETS[style]

