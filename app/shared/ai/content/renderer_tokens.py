"""Renderer 共享令牌解析与派生辅助。"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from shared.ai.content.typography import apply_matplotlib_typography, normalize_font_weight


@dataclass(frozen=True)
class FontSizeSpec:
    """单个字号角色的换算规则。"""

    token_key: str
    multiplier: float
    minimum: int
    extra: float = 0.0
    scale_key: str | None = None


@dataclass(frozen=True)
class FigureBoundsConfig:
    """安全区到 figure 边界的映射配置。"""

    default_left: float
    default_right: float
    default_top: float
    default_bottom: float
    left_scale: float
    right_scale: float
    top_scale: float
    bottom_scale: float
    min_left: float
    max_left: float
    min_right: float
    max_right: float
    min_top: float
    max_top: float
    min_bottom: float
    max_bottom: float


@dataclass(frozen=True)
class FigureBounds:
    left: float
    right: float
    top: float
    bottom: float


@dataclass(frozen=True)
class RendererThemeCardTokens:
    accent_color: str
    secondary_color: str
    background_color: str
    panel_color: str
    panel_alt_color: str
    title_color: str
    muted_text_color: str
    body_color: str
    cta_color: str
    card_background_color: str
    card_border_color: str
    card_border_width: float
    card_boxstyle: str
    card_fill_alpha: float
    card_title_color: str
    card_body_color: str
    card_accent_color: str
    card_badge_background_color: str


DEFAULT_SCALE_KEYS = ("title_scale", "summary_scale", "accent_scale", "conclusion_scale")
DEFAULT_WEIGHT_DEFAULTS = {
    "title_weight": "bold",
    "subtitle_weight": "semibold",
    "body_weight": "normal",
    "caption_weight": "normal",
}
DEFAULT_LINE_HEIGHT_DEFAULTS = {
    "title_line_height": 1.18,
    "body_line_height": 1.46,
    "caption_line_height": 1.24,
}


def _theme_value(theme: dict[str, Any], key: str, fallback: Any) -> Any:
    return theme.get(key, fallback)


def _card_value(card: dict[str, Any], key: str, fallback: Any) -> Any:
    return card.get(key, fallback)


def resolve_renderer_theme_card(
    theme: dict[str, Any],
    card: dict[str, Any],
    defaults: dict[str, Any],
) -> RendererThemeCardTokens:
    """解析 renderer 需要的主题/卡片基础令牌与 fallback。"""

    accent_color = _theme_value(theme, "accent_color", defaults["accent_color"])
    panel_color = _theme_value(theme, "panel_color", defaults["panel_color"])
    return RendererThemeCardTokens(
        accent_color=accent_color,
        secondary_color=_theme_value(theme, "secondary_color", defaults["secondary_color"]),
        background_color=_theme_value(theme, "background_color", defaults["background_color"]),
        panel_color=panel_color,
        panel_alt_color=_theme_value(theme, "panel_alt_color", defaults["panel_alt_color"]),
        title_color=_theme_value(theme, "title_color", defaults["title_color"]),
        muted_text_color=_theme_value(theme, "muted_text_color", defaults["muted_text_color"]),
        body_color=_theme_value(theme, "body_color", defaults["body_color"]),
        cta_color=_theme_value(theme, "cta_color", accent_color),
        card_background_color=_card_value(card, "background_color", panel_color),
        card_border_color=_card_value(card, "border_color", defaults["card_border_color"]),
        card_border_width=float(_card_value(card, "border_width", defaults["card_border_width"])),
        card_boxstyle=str(_card_value(card, "boxstyle", defaults["card_boxstyle"])),
        card_fill_alpha=float(_card_value(card, "fill_alpha", defaults["card_fill_alpha"])),
        card_title_color=_card_value(card, "title_color", _theme_value(theme, "title_color", defaults["title_color"])),
        card_body_color=_card_value(card, "body_color", _theme_value(theme, "muted_text_color", defaults["muted_text_color"])),
        card_accent_color=_card_value(card, "accent_color", accent_color),
        card_badge_background_color=_card_value(card, "badge_background_color", _card_value(card, "border_color", defaults["card_border_color"])),
    )


def initialize_renderer_typography(typography: dict[str, Any]) -> str | None:
    """应用共享 Matplotlib 字体栈。"""

    return apply_matplotlib_typography(typography)


def resolve_scale_tokens(typography: dict[str, Any]) -> dict[str, float]:
    """解析共享排版缩放令牌。"""

    return {
        key: float(typography.get(key, 1.0))
        for key in DEFAULT_SCALE_KEYS
    }


def resolve_font_sizes(
    typography: dict[str, Any],
    specs: dict[str, FontSizeSpec],
    scales: dict[str, float] | None = None,
) -> dict[str, int]:
    """按共享规格计算 renderer 角色字号。"""

    scale_map = scales or resolve_scale_tokens(typography)
    resolved: dict[str, int] = {}
    for role, spec in specs.items():
        token_value = float(typography.get(spec.token_key, spec.minimum))
        scale_value = scale_map.get(spec.scale_key or "", 1.0)
        computed = int((token_value + spec.extra) * spec.multiplier * scale_value)
        resolved[role] = max(spec.minimum, computed)
    return resolved


def resolve_font_weights(
    typography: dict[str, Any],
    defaults: dict[str, str] | None = None,
) -> dict[str, str]:
    """解析共享字重令牌。"""

    fallback_map = {**DEFAULT_WEIGHT_DEFAULTS, **(defaults or {})}
    return {
        key: normalize_font_weight(typography.get(key), fallback)
        for key, fallback in fallback_map.items()
    }


def resolve_line_heights(
    typography: dict[str, Any],
    defaults: dict[str, float] | None = None,
) -> dict[str, float]:
    """解析共享行高令牌。"""

    fallback_map = {**DEFAULT_LINE_HEIGHT_DEFAULTS, **(defaults or {})}
    return {
        key: float(typography.get(key, fallback))
        for key, fallback in fallback_map.items()
    }


def resolve_figure_bounds(safe_area: dict[str, Any], config: FigureBoundsConfig) -> FigureBounds:
    """按安全区和项目配置导出 figure 边界。"""

    safe_left = float(safe_area.get("left_ratio", 0.0))
    safe_right = float(safe_area.get("right_ratio", 0.0))
    safe_top = float(safe_area.get("top_ratio", 0.0))
    safe_bottom = float(safe_area.get("bottom_ratio", 0.0))
    return FigureBounds(
        left=max(config.min_left, min(config.max_left, config.default_left + safe_left * config.left_scale)),
        right=min(config.max_right, max(config.min_right, config.default_right - safe_right * config.right_scale)),
        top=min(config.max_top, max(config.min_top, config.default_top - safe_top * config.top_scale)),
        bottom=max(config.min_bottom, min(config.max_bottom, config.default_bottom + safe_bottom * config.bottom_scale)),
    )

