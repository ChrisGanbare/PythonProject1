"""Platform specification presets for major Chinese and international video platforms."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PlatformPreset:
    name: str
    width: int
    height: int
    fps: int
    min_duration: int   # seconds
    max_duration: int   # seconds
    safe_top: int       # px to reserve at top
    safe_bottom: int    # px to reserve at bottom
    safe_left: int      # px to reserve at left
    safe_right: int     # px to reserve at right
    orientation: str    # "landscape" | "vertical" | "square"


# ── 哔哩哔哩 ──────────────────────────────────────────────────
BILIBILI_LANDSCAPE = PlatformPreset(
    name="bilibili_landscape",
    width=1920,
    height=1080,
    fps=60,
    min_duration=180,
    max_duration=900,
    safe_top=80,
    safe_bottom=80,
    safe_left=0,
    safe_right=0,
    orientation="landscape",
)

BILIBILI_VERTICAL = PlatformPreset(
    name="bilibili_vertical",
    width=1080,
    height=1920,
    fps=60,
    min_duration=60,
    max_duration=180,
    safe_top=200,
    safe_bottom=0,
    safe_left=0,
    safe_right=0,
    orientation="vertical",
)

# ── 抖音 ──────────────────────────────────────────────────────
DOUYIN = PlatformPreset(
    name="douyin",
    width=1080,
    height=1920,
    fps=30,
    min_duration=15,
    max_duration=180,
    safe_top=0,
    safe_bottom=300,
    safe_left=0,
    safe_right=0,
    orientation="vertical",
)

# ── 小红书 ────────────────────────────────────────────────────
XIAOHONGSHU = PlatformPreset(
    name="xiaohongshu",
    width=1080,
    height=1350,
    fps=30,
    min_duration=15,
    max_duration=180,
    safe_top=60,
    safe_bottom=60,
    safe_left=60,
    safe_right=60,
    orientation="square",
)

# ── YouTube (参考规格) ─────────────────────────────────────────
# YOUTUBE_1080P = PlatformPreset(
#     name="youtube_1080p",
#     width=1920,
#     height=1080,
#     fps=60,
#     min_duration=0,
#     max_duration=43200,
#     safe_top=66,
#     safe_bottom=66,
#     safe_left=120,
#     safe_right=120,
#     orientation="landscape",
# )

ALL_PRESETS: dict[str, PlatformPreset] = {
    "bilibili_landscape": BILIBILI_LANDSCAPE,
    "bilibili_vertical": BILIBILI_VERTICAL,
    "douyin": DOUYIN,
    "xiaohongshu": XIAOHONGSHU,
}
