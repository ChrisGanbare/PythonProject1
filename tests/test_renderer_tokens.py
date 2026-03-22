"""Shared renderer token helper tests."""

from __future__ import annotations

from shared.content.renderer_tokens import (
    FigureBoundsConfig,
    FontSizeSpec,
    resolve_figure_bounds,
    resolve_font_sizes,
    resolve_renderer_theme_card,
    resolve_scale_tokens,
)


def test_resolve_renderer_theme_card_applies_theme_and_card_fallbacks() -> None:
    resolved = resolve_renderer_theme_card(
        theme={"accent_color": "#123456", "panel_color": "#111111", "title_color": "#eeeeee"},
        card={"border_color": "#abcdef", "fill_alpha": 0.77},
        defaults={
            "accent_color": "#ff0000",
            "secondary_color": "#00ff00",
            "background_color": "#000000",
            "panel_color": "#222222",
            "panel_alt_color": "#333333",
            "title_color": "#ffffff",
            "muted_text_color": "#888888",
            "body_color": "#aaaaaa",
            "card_border_color": "#444444",
            "card_border_width": 1.5,
            "card_boxstyle": "round,pad=0.3",
            "card_fill_alpha": 0.9,
        },
    )

    assert resolved.accent_color == "#123456"
    assert resolved.card_border_color == "#abcdef"
    assert resolved.card_background_color == "#111111"
    assert resolved.card_fill_alpha == 0.77
    assert resolved.card_title_color == "#eeeeee"


def test_resolve_font_sizes_uses_role_specs_and_scales() -> None:
    typography = {
        "title_size": 60,
        "body_size": 22,
        "title_scale": 1.1,
        "conclusion_scale": 1.05,
    }
    scales = resolve_scale_tokens(typography)
    sizes = resolve_font_sizes(
        typography,
        {
            "title": FontSizeSpec("title_size", 0.5, 18, scale_key="title_scale"),
            "conclusion": FontSizeSpec("body_size", 1.0, 16, extra=4, scale_key="conclusion_scale"),
        },
        scales=scales,
    )

    assert sizes["title"] == 33
    assert sizes["conclusion"] == 27


def test_resolve_figure_bounds_maps_safe_area_into_clamped_margins() -> None:
    bounds = resolve_figure_bounds(
        {"left_ratio": 0.05, "right_ratio": 0.04, "top_ratio": 0.10, "bottom_ratio": 0.12},
        FigureBoundsConfig(
            default_left=0.06,
            default_right=0.94,
            default_top=0.97,
            default_bottom=0.03,
            left_scale=0.7,
            right_scale=0.7,
            top_scale=0.4,
            bottom_scale=0.5,
            min_left=0.05,
            max_left=0.12,
            min_right=0.88,
            max_right=0.95,
            min_top=0.86,
            max_top=0.97,
            min_bottom=0.03,
            max_bottom=0.20,
        ),
    )

    assert round(bounds.left, 3) == 0.095
    assert round(bounds.right, 3) == 0.912
    assert round(bounds.top, 3) == 0.93
    assert round(bounds.bottom, 3) == 0.09

