"""Shared theme registry tests."""

from __future__ import annotations

from shared.content.schemas import ContentStyle
from shared.content.themes import STYLE_THEME_PRESETS, get_style_theme_preset


def test_theme_registry_covers_all_content_styles() -> None:
    assert set(STYLE_THEME_PRESETS) == set(ContentStyle)


def test_each_theme_preset_contains_complete_visual_assets() -> None:
    for style in ContentStyle:
        preset = get_style_theme_preset(style)
        assert preset.theme_name
        assert preset.accent_color.startswith("#")
        assert preset.secondary_color.startswith("#")
        assert preset.background_color.startswith("#")
        assert preset.panel_color.startswith("#")
        assert preset.panel_alt_color.startswith("#")
        assert preset.muted_text_color.startswith("#")
        assert preset.title_color.startswith("#")
        assert preset.body_color.startswith("#")
        assert preset.cta_color.startswith("#")
        assert preset.typography.title_size > 0
        assert preset.typography.subtitle_size > 0
        assert preset.typography.body_size > 0
        assert preset.typography.caption_size > 0
        assert preset.typography.font_family
        assert preset.typography.font_fallbacks
        assert preset.typography.numeric_font_family
        assert preset.typography.numeric_font_fallbacks
        assert preset.typography.title_weight
        assert preset.typography.subtitle_weight
        assert preset.typography.body_weight
        assert preset.typography.caption_weight
        assert preset.typography.title_line_height > 1.0
        assert preset.typography.body_line_height > 1.0
        assert preset.typography.caption_line_height > 1.0
        assert preset.card_theme.background_color.startswith("#")
        assert preset.card_theme.border_color.startswith("#")
        assert preset.card_theme.title_color.startswith("#")
        assert preset.card_theme.body_color.startswith("#")
        assert preset.card_theme.accent_color.startswith("#")
        assert preset.card_theme.badge_background_color.startswith("#")
        assert preset.card_theme.border_width > 0
        assert preset.card_theme.boxstyle
        assert 0 < preset.card_theme.fill_alpha <= 1
        assert preset.subtitle_theme.hook_emphasis.font_role in {"primary", "numeric"}
        assert preset.subtitle_theme.hook_emphasis.size_role in {"title", "subtitle", "body", "caption"}
        assert preset.subtitle_theme.hook_emphasis.weight_role in {"title", "subtitle", "body", "caption"}
        assert preset.subtitle_theme.body_explainer.text_color_role.endswith("_color")
        assert preset.subtitle_theme.climax_emphasis.stroke_width > 0
        assert preset.subtitle_theme.conclusion_summary.line_height_role in {"title", "body", "caption"}
        assert 0 <= preset.subtitle_theme.conclusion_cta.background_alpha <= 1

