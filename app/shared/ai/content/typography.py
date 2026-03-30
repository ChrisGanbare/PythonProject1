"""共享排版辅助能力。"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

import matplotlib.font_manager as fm
import matplotlib.pyplot as plt


DEFAULT_FONT_FALLBACKS = [
    "Source Han Sans SC",
    "Noto Sans CJK SC",
    "Alibaba PuHuiTi 2.0",
    "Microsoft YaHei",
    "PingFang SC",
    "SimHei",
    "DejaVu Sans",
]

DEFAULT_NUMERIC_FONT_FALLBACKS = [
    "Inter",
    "DIN Condensed",
    "Arial",
    "DejaVu Sans",
]


def normalize_font_weight(weight: str | None, fallback: str = "regular") -> str:
    """规范化 Matplotlib 兼容的字重名称。"""

    if not weight:
        return fallback
    normalized = weight.strip().lower().replace("_", "-")
    aliases = {
        "normal": "normal",
        "regular": "normal",
        "book": "normal",
        "medium": "medium",
        "semibold": "semibold",
        "semi-bold": "semibold",
        "demibold": "semibold",
        "bold": "bold",
        "heavy": "heavy",
    }
    return aliases.get(normalized, fallback)


def build_font_candidates(preferred: str | None, fallbacks: Sequence[str] | None = None) -> list[str]:
    """构建去重后的字体候选列表。"""

    ordered = [preferred, *(fallbacks or [])]
    seen: set[str] = set()
    candidates: list[str] = []
    for name in ordered:
        if not name:
            continue
        cleaned = str(name).strip()
        if not cleaned or cleaned in seen:
            continue
        seen.add(cleaned)
        candidates.append(cleaned)
    return candidates


def resolve_available_font(candidates: Sequence[str]) -> str | None:
    """从候选字体中解析当前环境可用的首选字体。"""

    available = {font.name for font in fm.fontManager.ttflist}
    for name in candidates:
        if name in available:
            return name
    return None


def apply_matplotlib_typography(typography: Mapping[str, Any] | None = None) -> str | None:
    """按共享排版令牌设置 Matplotlib 字体栈。"""

    tokens = typography or {}
    candidates = build_font_candidates(
        tokens.get("font_family") if isinstance(tokens, Mapping) else None,
        (tokens.get("font_fallbacks") if isinstance(tokens, Mapping) else None) or DEFAULT_FONT_FALLBACKS,
    )
    resolved = resolve_available_font(candidates)
    font_stack = candidates or list(DEFAULT_FONT_FALLBACKS)
    if resolved:
        font_stack = [resolved, *[name for name in font_stack if name != resolved]]
    if "DejaVu Sans" not in font_stack:
        font_stack.append("DejaVu Sans")
    plt.rcParams["font.sans-serif"] = font_stack
    plt.rcParams["axes.unicode_minus"] = False
    return resolved

