"""Platform specification presets for major Chinese and international video platforms."""

from __future__ import annotations

from dataclasses import dataclass


def infer_orientation(width: int, height: int) -> str:
    if width > height:
        return "landscape"
    if width == height:
        return "square"
    return "vertical"


def build_scene_copy_band_tokens(
    *,
    platform: str,
    width: int,
    height: int,
    safe_top: int,
    safe_bottom: int,
    safe_left: int,
    safe_right: int,
    orientation: str | None = None,
) -> dict[str, float | int | str | dict[str, float | int]]:
    resolved_orientation = str(orientation or infer_orientation(width, height))
    safe_top_ratio = safe_top / height if height else 0.0
    safe_bottom_ratio = safe_bottom / height if height else 0.0
    safe_left_ratio = safe_left / width if width else 0.0
    safe_right_ratio = safe_right / width if width else 0.0
    side_padding_ratio = min(0.12, max(safe_left_ratio, safe_right_ratio) + 0.02)

    if resolved_orientation == "landscape":
        full = {
            "x": 4,
            "y": 18,
            "w": 92,
            "h": 64,
            "label_y": 68,
            "headline_y": 51,
            "detail_y": 32,
            "headline_scale": 0.95,
            "detail_scale": 0.92,
        }
        compact = {
            "x": 4,
            "y": 70,
            "w": 92,
            "h": 22,
            "label_y": 86,
            "headline_y": 82,
            "detail_y": 75,
            "headline_scale": 0.90,
            "detail_scale": 0.86,
        }
    elif resolved_orientation == "square":
        full = {
            "x": 6,
            "y": 14,
            "w": 88,
            "h": 72,
            "label_y": 74,
            "headline_y": 53,
            "detail_y": 31,
            "headline_scale": 1.00,
            "detail_scale": 0.96,
        }
        compact = {
            "x": 6,
            "y": 68,
            "w": 88,
            "h": 24,
            "label_y": 85,
            "headline_y": 80,
            "detail_y": 73,
            "headline_scale": 0.94,
            "detail_scale": 0.90,
        }
    else:
        full = {
            "x": 3,
            "y": 10,
            "w": 94,
            "h": 78,
            "label_y": 74,
            "headline_y": 52,
            "detail_y": 28,
            "headline_scale": 1.05,
            "detail_scale": 1.00,
        }
        compact = {
            "x": 3,
            "y": 66,
            "w": 94,
            "h": 26,
            "label_y": 84,
            "headline_y": 79,
            "detail_y": 72,
            "headline_scale": 0.98,
            "detail_scale": 0.92,
        }

    if safe_top_ratio >= 0.08:
        full["y"] += 2
        full["h"] = max(60, int(full["h"]) - 4)
        compact["y"] += 1
    if safe_bottom_ratio >= 0.14:
        compact["h"] = min(30, int(compact["h"]) + 2)
        compact["y"] = max(62, int(compact["y"]) - 2)

    return {
        "platform": platform,
        "orientation": resolved_orientation,
        "safe_top_ratio": safe_top_ratio,
        "safe_bottom_ratio": safe_bottom_ratio,
        "safe_left_ratio": safe_left_ratio,
        "safe_right_ratio": safe_right_ratio,
        "side_padding_ratio": side_padding_ratio,
        "full": full,
        "compact": compact,
    }


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

    @property
    def safe_top_ratio(self) -> float:
        return self.safe_top / self.height

    @property
    def safe_bottom_ratio(self) -> float:
        return self.safe_bottom / self.height

    @property
    def safe_left_ratio(self) -> float:
        return self.safe_left / self.width

    @property
    def safe_right_ratio(self) -> float:
        return self.safe_right / self.width

    @property
    def content_top_ratio(self) -> float:
        return 1.0 - self.safe_top_ratio

    @property
    def content_bottom_ratio(self) -> float:
        return self.safe_bottom_ratio

    @property
    def content_left_ratio(self) -> float:
        return self.safe_left_ratio

    @property
    def content_right_ratio(self) -> float:
        return 1.0 - self.safe_right_ratio

    def to_safe_area_dict(self) -> dict[str, float | int | str]:
        """导出渲染层可直接消费的安全区描述。"""

        return {
            "platform": self.name,
            "orientation": self.orientation,
            "frame_width": self.width,
            "frame_height": self.height,
            "top_px": self.safe_top,
            "bottom_px": self.safe_bottom,
            "left_px": self.safe_left,
            "right_px": self.safe_right,
            "top_ratio": self.safe_top_ratio,
            "bottom_ratio": self.safe_bottom_ratio,
            "left_ratio": self.safe_left_ratio,
            "right_ratio": self.safe_right_ratio,
            "content_top": self.content_top_ratio,
            "content_bottom": self.content_bottom_ratio,
            "content_left": self.content_left_ratio,
            "content_right": self.content_right_ratio,
            "subtitle_band_top": 1.0 - self.safe_bottom_ratio,
        }

    def to_subtitle_layout_dict(self) -> dict[str, float | int | str]:
        """导出字幕布局建议令牌。"""

        max_width_ratio = 0.72 if self.orientation == "landscape" else 0.82
        max_lines = 2 if self.orientation == "landscape" else 3
        return {
            "platform": self.name,
            "align": "center",
            "anchor": "bottom",
            "bottom_px": self.safe_bottom,
            "bottom_ratio": self.safe_bottom_ratio,
            "max_width_ratio": max_width_ratio,
            "max_lines": max_lines,
            "safe_left_ratio": self.safe_left_ratio,
            "safe_right_ratio": self.safe_right_ratio,
            "subtitle_band_top": 1.0 - self.safe_bottom_ratio,
        }

    def to_scene_copy_band_dict(self) -> dict[str, float | int | str | dict[str, float | int]]:
        """导出 scene copy band 布局令牌。"""

        return build_scene_copy_band_tokens(
            platform=self.name,
            width=self.width,
            height=self.height,
            safe_top=self.safe_top,
            safe_bottom=self.safe_bottom,
            safe_left=self.safe_left,
            safe_right=self.safe_right,
            orientation=self.orientation,
        )


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


def get_platform_preset(name: str) -> PlatformPreset:
    """根据平台名称返回规格预设。"""
    preset = ALL_PRESETS.get(name)
    if preset is None:
        supported = ", ".join(sorted(ALL_PRESETS))
        raise ValueError(f"unsupported platform '{name}'. Supported: {supported}")
    return preset

