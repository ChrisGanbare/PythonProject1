"""
基金手续费复利侵蚀可视化动画  v3
Flourish 深色风格 | 抖音 / 哔哩哔哩 竖屏 9:16 | 30 秒

场景结构：
  Scene 1   0~8s  — 冲击标题淡入，引发悬念
  Scene 2  8~23s  — 四条曲线匀速生长（无标注，聚焦轨迹差异）
  Scene 3 23~30s  — 定格 + 计数动画 + 缺口标注 + 结论卡片
"""

from __future__ import annotations

import json
import os
import shutil
import sys
import warnings
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.animation import FFMpegWriter, FuncAnimation

_WORKSPACE_ROOT = Path(__file__).resolve().parents[3]
if str(_WORKSPACE_ROOT) not in sys.path:
    sys.path.insert(0, str(_WORKSPACE_ROOT))

from shared.content.renderer_tokens import (
    FigureBoundsConfig,
    FontSizeSpec,
    initialize_renderer_typography,
    resolve_figure_bounds,
    resolve_font_sizes,
    resolve_font_weights,
    resolve_line_heights,
    resolve_renderer_theme_card,
    resolve_scale_tokens,
)
from shared.visualization.png_frame_cache import (
    PngCachingFFMpegWriter,
    all_frames_cached,
    encode_video_from_png_sequence_ffmpeg,
    frame_png_path,
)

warnings.filterwarnings("ignore")


if not shutil.which("ffmpeg"):
    raise SystemExit("错误: 未找到 ffmpeg，请先安装 https://ffmpeg.org/download.html")


# ── 参数 ──────────────────────────────────────────────────────

PRINCIPAL    = float(os.getenv("VIDEO_PRINCIPAL",    "1000000"))
GROSS_RETURN = float(os.getenv("VIDEO_GROSS_RETURN", "0.08"))
YEARS        = int(os.getenv("VIDEO_YEARS",          "30"))
WIDTH        = int(os.getenv("VIDEO_WIDTH",          "1080"))
HEIGHT       = int(os.getenv("VIDEO_HEIGHT",         "1920"))
FPS          = int(os.getenv("VIDEO_FPS",            "30"))
DURATION     = int(os.getenv("VIDEO_DURATION",       "50"))
OUTPUT_FILE  = os.getenv("VIDEO_OUTPUT_FILE",        "runtime/outputs/fund_fee_erosion.mp4")
DPI          = int(os.getenv("VIDEO_DPI",            "100"))
VIDEO_BITRATE = int(os.getenv("VIDEO_BITRATE",       "8000"))
VIDEO_PRESET = os.getenv("VIDEO_PRESET",             "medium")
VIDEO_CRF    = int(os.getenv("VIDEO_CRF",            "20"))
RENDER_EXPRESSION = json.loads(os.getenv("VIDEO_RENDER_EXPRESSION", "{}") or "{}")
VIDEO_RENDER_FINGERPRINT = os.getenv("VIDEO_RENDER_FINGERPRINT", "").strip()
VIDEO_FRAME_CACHE_DIR = os.getenv("VIDEO_FRAME_CACHE_DIR", "").strip()
_CURRENT_ANIM_FRAME = 0


def _using_frame_cache() -> bool:
    return bool(VIDEO_FRAME_CACHE_DIR) and not os.getenv("VIDEO_FRAME_CACHE_DISABLE", "").strip()


# ── 费用场景（使用真实基金分类名称）──────────────────────────

SCENARIOS = [
    {"label": "零费用基准",   "sublabel": "理论上限",   "fee": 0.0000, "color": "#22D47E"},
    {"label": "指数型ETF",    "sublabel": "0.15%/年",   "fee": 0.0015, "color": "#4F9EFF"},
    {"label": "偏股混合型",   "sublabel": "1.50%/年",   "fee": 0.0150, "color": "#FF7F35"},
    {"label": "高费率权益型", "sublabel": "2.00%/年",   "fee": 0.0200, "color": "#F43F5E"},
]

YEAR_AXIS = np.arange(0, YEARS + 1)
if VIDEO_RENDER_FINGERPRINT:
    print(f"[指纹] {VIDEO_RENDER_FINGERPRINT[:24]}…")
if VIDEO_FRAME_CACHE_DIR:
    print(f"[帧缓存目录 PNG] {VIDEO_FRAME_CACHE_DIR}")
for _s in SCENARIOS:
    _s["vals"] = PRINCIPAL * (1 + GROSS_RETURN - _s["fee"]) ** YEAR_AXIS / 10_000  # 万元

BASELINE = SCENARIOS[0]["vals"][-1]   # 无费用终值（万元）
MAX_Y    = BASELINE * 1.15
GAP_ACT  = BASELINE - SCENARIOS[2]["vals"][-1]   # 偏股混合型缺口

# ── 配色 ──────────────────────────────────────────────────────

BG    = "#0D0D1A"
MID   = "#12122A"
SUB   = "#94A3B8"
GOLD  = "#FBBF24"
WHITE = "#FFFFFF"
GRID  = "#2A2A4A"

THEME = RENDER_EXPRESSION.get("theme", {})
TYPOGRAPHY = RENDER_EXPRESSION.get("typography", {})
CARD_STYLE = RENDER_EXPRESSION.get("card", {})
LAYOUT_HINTS = RENDER_EXPRESSION.get("layout", {})
VISUAL_CUES = RENDER_EXPRESSION.get("visual_cues", {})
SCENE_BEHAVIOR = RENDER_EXPRESSION.get("scene_behavior", {})
SAFE_AREA = RENDER_EXPRESSION.get("safe_area", {})
VISUAL_FOCUS = RENDER_EXPRESSION.get("visual_focus", "")
RENDERER_THEME = resolve_renderer_theme_card(
    THEME,
    CARD_STYLE,
    {
        "accent_color": GOLD,
        "secondary_color": SUB,
        "background_color": BG,
        "panel_color": MID,
        "panel_alt_color": MID,
        "title_color": WHITE,
        "muted_text_color": SUB,
        "body_color": WHITE,
        "card_border_color": GOLD,
        "card_border_width": 1.5,
        "card_boxstyle": "round,pad=0.35",
        "card_fill_alpha": 0.92,
    },
)
GOLD = RENDERER_THEME.accent_color
SUB = RENDERER_THEME.secondary_color
BG = RENDERER_THEME.background_color
MID = RENDERER_THEME.panel_color
PANEL_ALT = RENDERER_THEME.panel_alt_color
WHITE = RENDERER_THEME.title_color
BODY = RENDERER_THEME.body_color
MUTED = RENDERER_THEME.muted_text_color
CTA_COLOR = RENDERER_THEME.cta_color
SCALES = resolve_scale_tokens(TYPOGRAPHY)
TITLE_SCALE = SCALES["title_scale"]
SUMMARY_SCALE = SCALES["summary_scale"]
ACCENT_SCALE = SCALES["accent_scale"]
CONCLUSION_SCALE = SCALES["conclusion_scale"]
FONT_NAME = initialize_renderer_typography(TYPOGRAPHY)

CARD_BACKGROUND_COLOR = RENDERER_THEME.card_background_color
CARD_BORDER_COLOR = RENDERER_THEME.card_border_color
CARD_TITLE_COLOR = RENDERER_THEME.card_title_color
CARD_BODY_COLOR = RENDERER_THEME.card_body_color
CARD_ACCENT_COLOR = RENDERER_THEME.card_accent_color
CARD_BADGE_BG = RENDERER_THEME.card_badge_background_color
CARD_BORDER_WIDTH = RENDERER_THEME.card_border_width
CARD_BOXSTYLE = RENDERER_THEME.card_boxstyle
CARD_FILL_ALPHA = RENDERER_THEME.card_fill_alpha

HOOK_LAYOUT = LAYOUT_HINTS.get("hook_layout", "stacked")
CHART_FOCUS = LAYOUT_HINTS.get("chart_focus", "balanced")
CONCLUSION_LAYOUT = LAYOUT_HINTS.get("conclusion_layout", "summary-band")
HOOK_FOCUS = VISUAL_CUES.get("hook_focus", "headline_focus")
HOOK_MODE = SCENE_BEHAVIOR.get("hook_mode", "context-lead")
HOOK_SUPPORT_DENSITY = SCENE_BEHAVIOR.get("hook_support_density", "balanced")
SETUP_DENSITY = SCENE_BEHAVIOR.get("setup_density", "balanced")
SHOW_REFERENCE_GUIDES = bool(SCENE_BEHAVIOR.get("show_reference_guides", True))
CONCLUSION_MODE = SCENE_BEHAVIOR.get("conclusion_mode", "summary-band")
CONCLUSION_REVEAL_ORDER = list(SCENE_BEHAVIOR.get("conclusion_reveal_order", ["headline", "body", "badge", "footer"]))
CONCLUSION_CARD_SCALE = float(SCENE_BEHAVIOR.get("conclusion_card_scale", 1.0))

FONT_SIZES = resolve_font_sizes(
    TYPOGRAPHY,
    {
        "title": FontSizeSpec("title_size", 1.0, 44, scale_key="title_scale"),
        "summary": FontSizeSpec("subtitle_size", 1.0, 24, scale_key="summary_scale"),
        "accent": FontSizeSpec("body_size", 1.0, 22, extra=10, scale_key="accent_scale"),
        "hook": FontSizeSpec("title_size", 1.0, 42, extra=(12 if HOOK_LAYOUT == "hero" else 4), scale_key="title_scale"),
        "conclusion_title": FontSizeSpec("subtitle_size", 1.0, 22, scale_key="conclusion_scale"),
        "conclusion_body": FontSizeSpec("body_size", 1.0, 16, scale_key="summary_scale"),
        "conclusion_badge": FontSizeSpec("caption_size", 1.0, 14, extra=2, scale_key="accent_scale"),
        "footnote": FontSizeSpec("caption_size", 1.0, 16, extra=1),
    },
    scales=SCALES,
)
TITLE_FONT_SIZE = FONT_SIZES["title"]
SUMMARY_FONT_SIZE = FONT_SIZES["summary"]
ACCENT_FONT_SIZE = FONT_SIZES["accent"]
HOOK_FONT_SIZE = FONT_SIZES["hook"]
CONCLUSION_TITLE_SIZE = FONT_SIZES["conclusion_title"]
CONCLUSION_BODY_SIZE = FONT_SIZES["conclusion_body"]
CONCLUSION_BADGE_SIZE = FONT_SIZES["conclusion_badge"]
FOOTNOTE_SIZE = FONT_SIZES["footnote"]
WEIGHTS = resolve_font_weights(TYPOGRAPHY)
TITLE_FONT_WEIGHT = WEIGHTS["title_weight"]
SUBTITLE_FONT_WEIGHT = WEIGHTS["subtitle_weight"]
BODY_FONT_WEIGHT = WEIGHTS["body_weight"]
CAPTION_FONT_WEIGHT = WEIGHTS["caption_weight"]
LINE_HEIGHTS = resolve_line_heights(TYPOGRAPHY, {"title_line_height": 1.18, "body_line_height": 1.46, "caption_line_height": 1.24})
TITLE_LINE_HEIGHT = LINE_HEIGHTS["title_line_height"]
BODY_LINE_HEIGHT = LINE_HEIGHTS["body_line_height"]
CAPTION_LINE_HEIGHT = LINE_HEIGHTS["caption_line_height"]
AXIS_LABEL_SIZE = max(20, int(TYPOGRAPHY.get("subtitle_size", 32) * 0.94))
REFERENCE_LABEL_SIZE = max(18, int(TYPOGRAPHY.get("body_size", 22) * 0.9))
SERIES_LABEL_SIZE = max(20, int(TYPOGRAPHY.get("body_size", 22) * 1.18))
SERIES_VALUE_SIZE = max(22, int(TYPOGRAPHY.get("body_size", 22) * 1.28))
GAP_LABEL_SIZE = max(20, int(TYPOGRAPHY.get("subtitle_size", 32) * 0.84))
FIGURE_BOUNDS = resolve_figure_bounds(
    SAFE_AREA,
    FigureBoundsConfig(
        default_left=0.14,
        default_right=0.96,
        default_top=0.97,
        default_bottom=0.03,
        left_scale=0.75,
        right_scale=0.75,
        top_scale=0.45,
        bottom_scale=0.60,
        min_left=0.10,
        max_left=0.20,
        min_right=0.82,
        max_right=0.96,
        min_top=0.80,
        max_top=0.97,
        min_bottom=0.03,
        max_bottom=0.28,
    ),
)
FIG_LEFT, FIG_RIGHT, FIG_TOP, FIG_BOTTOM = (
    FIGURE_BOUNDS.left,
    FIGURE_BOUNDS.right,
    FIGURE_BOUNDS.top,
    FIGURE_BOUNDS.bottom,
)

TITLE_Y = 0.97
SUMMARY_Y = 0.81 if HOOK_LAYOUT == "hero" else 0.80
ACCENT_Y = 0.68 if HOOK_LAYOUT == "hero" else 0.66
HOOK_Y = 0.47 if HOOK_LAYOUT == "hero" else 0.50

if CONCLUSION_LAYOUT == "spotlight-card":
    CONCLUSION_TITLE_POS = (0.5, 0.90)
    CONCLUSION_BADGE_POS = (0.5, 0.81)
    CONCLUSION_BODY_POS = (0.5, 0.71)
    CONCLUSION_BODY_HA = "center"
    CONCLUSION_BODY_VA = "center"
elif CONCLUSION_LAYOUT == "stacked-summary":
    CONCLUSION_TITLE_POS = (0.76, 0.92)
    CONCLUSION_BADGE_POS = (0.76, 0.83)
    CONCLUSION_BODY_POS = (0.76, 0.73)
    CONCLUSION_BODY_HA = "center"
    CONCLUSION_BODY_VA = "center"
else:
    CONCLUSION_TITLE_POS = (0.5, 0.96)
    CONCLUSION_BADGE_POS = (0.5, 0.87)
    CONCLUSION_BODY_POS = (0.5, 0.07)
    CONCLUSION_BODY_HA = "center"
    CONCLUSION_BODY_VA = "bottom"

TITLE_TEXT = RENDER_EXPRESSION.get("title_text", "基金手续费的复利侵蚀")
HOOK_TEXT = RENDER_EXPRESSION.get("hook_text", f"差距高达  {GAP_ACT:.0f} 万元！")
SUMMARY_TEXT = RENDER_EXPRESSION.get("summary_text", "同样的收益率，每年多 1.5% 费用")
CONCLUSION_TITLE = RENDER_EXPRESSION.get("conclusion_title", "1.5% 年费率 · 30 年吞噬 34% 财富")
CONCLUSION_BODY = RENDER_EXPRESSION.get("conclusion_body", "看收益时别只看涨幅，也要看费用结构。")
ACCENT_LABEL = RENDER_EXPRESSION.get("accent_label", "30 年后差了多少？")

# ── 时间轴 ────────────────────────────────────────────────────

N_FRAMES = FPS * DURATION
CONTENT_VARIANT = RENDER_EXPRESSION.get("variant", "standard")
if CONTENT_VARIANT == "short":
    T1 = int(FPS * max(4, DURATION * 0.18))
    T2 = int(FPS * max(T1 / FPS + 6, DURATION * 0.72))
else:
    T1 = FPS * 10
    T2 = FPS * 38


def _ease(t: float) -> float:
    t = max(0.0, min(1.0, t))
    return 4 * t ** 3 if t < 0.5 else 1 - (-2 * t + 2) ** 3 / 2


# ── Figure ────────────────────────────────────────────────────

fig = plt.figure(figsize=(WIDTH / DPI, HEIGHT / DPI), dpi=DPI, facecolor=BG)
if CHART_FOCUS == "single-compare":
    height_ratios = [3.9, 5.3, 0.8]
elif CHART_FOCUS == "trend-gap":
    height_ratios = [3.2, 6.0, 0.8]
else:
    height_ratios = [3.5, 5.7, 0.8]
if HOOK_MODE == "hero-spotlight":
    height_ratios[0] += 0.35
    height_ratios[1] -= 0.20
if SETUP_DENSITY == "full-context":
    height_ratios[1] += 0.25
gs  = fig.add_gridspec(
    3, 1,
    height_ratios=height_ratios,
    hspace=0, top=FIG_TOP, bottom=FIG_BOTTOM, left=FIG_LEFT, right=FIG_RIGHT,
)
ax_h = fig.add_subplot(gs[0])
ax_m = fig.add_subplot(gs[1])
ax_f = fig.add_subplot(gs[2])

for _ax in (ax_h, ax_m, ax_f):
    _ax.set_facecolor(BG)
    for _sp in _ax.spines.values():
        _sp.set_visible(False)
    _ax.set_xticks([])
    _ax.set_yticks([])


# ── Header（静态文字，y 坐标精确错开，避免重叠）────────────────

ax_h.text(0.5, TITLE_Y, TITLE_TEXT,
          ha="center", va="top", fontsize=TITLE_FONT_SIZE, fontweight=TITLE_FONT_WEIGHT,
          color=WHITE, transform=ax_h.transAxes)

summary_alpha = 0.78 if HOOK_SUPPORT_DENSITY == "sparse" else 1.0
accent_alpha = 0.82 if HOOK_SUPPORT_DENSITY == "sparse" else 1.0
ax_h.text(0.5, SUMMARY_Y, SUMMARY_TEXT,
          ha="center", va="top", fontsize=SUMMARY_FONT_SIZE, color=MUTED,
          transform=ax_h.transAxes, alpha=summary_alpha)

ax_h.text(0.5, ACCENT_Y, ACCENT_LABEL,
          ha="center", va="top", fontsize=ACCENT_FONT_SIZE, color=CARD_BODY_COLOR,
          transform=ax_h.transAxes, alpha=accent_alpha)

# 冲击数字（动画渐显）
shock_t = ax_h.text(
    0.5, HOOK_Y,
    HOOK_TEXT,
    ha="center", va="top", fontsize=HOOK_FONT_SIZE, fontweight=TITLE_FONT_WEIGHT,
    color=CTA_COLOR, alpha=0.0, transform=ax_h.transAxes,
    bbox=dict(
        boxstyle=CARD_BOXSTYLE,
        facecolor=CARD_BACKGROUND_COLOR, edgecolor=CARD_BORDER_COLOR, linewidth=CARD_BORDER_WIDTH,
    ),
)


# ── Footer（两行：假设 + 来源）────────────────────────────────

ax_f.text(
    0.5, 0.72,
    f"本金 {PRINCIPAL / 10_000:.0f} 万元 · 年化毛收益 {GROSS_RETURN * 100:.0f}% · 投资 {YEARS} 年",
    ha="center", va="center", fontsize=CONCLUSION_BODY_SIZE, color=MUTED,
    transform=ax_f.transAxes,
)
ax_f.text(
    0.5, 0.22,
    VISUAL_FOCUS or "数据来源：中国基金业协会 2024 · Wind 金融终端 · 仅供参考",
    ha="center", va="center", fontsize=FOOTNOTE_SIZE, color=THEME.get("muted_text_color", "#64748B"),
    transform=ax_f.transAxes,
)


# ── Main chart ────────────────────────────────────────────────

XLIM_MAX = YEARS + 8   # 右侧预留标注空间

ax_m.set_facecolor(MID)
ax_m.set_xlim(0, XLIM_MAX)
ax_m.set_ylim(0, MAX_Y)
ax_m.tick_params(colors=MUTED, labelsize=26)
ax_m.set_xlabel("投资年限（年）", color=MUTED, fontsize=AXIS_LABEL_SIZE, labelpad=10)
ax_m.set_ylabel("资产价值（万元）", color=MUTED, fontsize=AXIS_LABEL_SIZE, labelpad=10)
for _sp in ax_m.spines.values():
    _sp.set_visible(True)
    _sp.set_color(GRID)
    _sp.set_linewidth(1.0)
ax_m.yaxis.grid(True, color=GRID, linewidth=0.8, alpha=0.6)
ax_m.set_axisbelow(True)
ax_m.set_xticks(range(0, YEARS + 1, 5))

# 静态水平参考线
reference_lines = [(500, "500万"), (1000, "1000万")]
if SHOW_REFERENCE_GUIDES:
    reference_lines = [(250, "250万"), (500, "500万"), (750, "750万"), (1000, "1000万")]
for _ref_y, _ref_lbl in reference_lines:
    if _ref_y < MAX_Y:
        ax_m.axhline(_ref_y, color=GRID, linewidth=0.7,
                     linestyle=":" if SHOW_REFERENCE_GUIDES else "-", alpha=0.9, zorder=1)
        ax_m.text(
            -0.01, _ref_y, _ref_lbl,
            ha="right", va="center", fontsize=REFERENCE_LABEL_SIZE, color=MUTED, alpha=0.8,
            transform=ax_m.get_yaxis_transform(),
        )


# ── 折线 artists：光晕层 + 主线层 ─────────────────────────────

_glow_lines: list = []
_lines:      list = []
for _s in SCENARIOS:
    _g, = ax_m.plot([], [], color=_s["color"], linewidth=20,
                    solid_capstyle="round", alpha=0.10, zorder=3)
    _glow_lines.append(_g)
    _ln, = ax_m.plot([], [], color=_s["color"], linewidth=6,
                     solid_capstyle="round", zorder=4)
    _lines.append(_ln)

# 年=YEARS 参考竖线
_vline, = ax_m.plot([], [], color=GRID, linewidth=1.8,
                    linestyle="--", zorder=2, alpha=0.0)


# ── Scene 3 artists ───────────────────────────────────────────

# 曲线名称标签（Scene 3，ha=right，x=YEARS-1，贴近曲线末端）
# 零费用/ETF 终值较近（1006 vs 965万），用 y 向错位避免重叠
LABEL_NUDGE = [+25, -20, +10, -10]   # 万元

_tip_labels: list = []
for _s in SCENARIOS:
    _tl = ax_m.text(
        0, 0, "",
        color=_s["color"], fontsize=SERIES_LABEL_SIZE, fontweight=SUBTITLE_FONT_WEIGHT,
        va="center", ha="right", zorder=5, alpha=0.0,
    )
    _tip_labels.append(_tl)

# 终值数字（ha=left，x=YEARS+0.5，含计数动画）
VAL_NUDGE = [+40, -30, +10, -10]   # 万元，同向偏移

_val_texts: list = []
for _s in SCENARIOS:
    _vt = ax_m.text(
        0, 0, "",
        color=_s["color"], fontsize=SERIES_VALUE_SIZE, fontweight=TITLE_FONT_WEIGHT,
        va="center", ha="left", zorder=5, alpha=0.0,
    )
    _val_texts.append(_vt)

# 缺口括线（零费用 vs 偏股混合型）
_gap_line,     = ax_m.plot([], [], color=GOLD, linewidth=3.0, zorder=3, alpha=0.0)
_gap_tick_top, = ax_m.plot([], [], color=GOLD, linewidth=3.0, zorder=3, alpha=0.0)
_gap_tick_bot, = ax_m.plot([], [], color=GOLD, linewidth=3.0, zorder=3, alpha=0.0)
_gap_text = ax_m.text(
    0, 0, "",
    color=CTA_COLOR, fontsize=GAP_LABEL_SIZE, fontweight=TITLE_FONT_WEIGHT,
    va="center", ha="left", zorder=5, alpha=0.0,
)

# 结论卡片（最后 40% 出现）
_conclusion = ax_m.text(
    CONCLUSION_TITLE_POS[0], CONCLUSION_TITLE_POS[1],
    CONCLUSION_TITLE,
    ha="center", va="top", fontsize=CONCLUSION_TITLE_SIZE, fontweight=TITLE_FONT_WEIGHT,
    color=CARD_TITLE_COLOR, alpha=0.0, transform=ax_m.transAxes,
    bbox=dict(
        boxstyle=CARD_BOXSTYLE,
        facecolor=CARD_BACKGROUND_COLOR, edgecolor=CARD_BORDER_COLOR, linewidth=CARD_BORDER_WIDTH,
    ),
)

_conclusion_badge = ax_m.text(
    CONCLUSION_BADGE_POS[0], CONCLUSION_BADGE_POS[1],
    ACCENT_LABEL,
    ha="center", va="center", fontsize=CONCLUSION_BADGE_SIZE, fontweight=SUBTITLE_FONT_WEIGHT,
    color=WHITE, alpha=0.0, transform=ax_m.transAxes,
    bbox=dict(
        boxstyle=CARD_BOXSTYLE,
        facecolor=CARD_BADGE_BG, edgecolor=CARD_BADGE_BG, linewidth=1.0,
    ),
)

# 计算公式（权威感，最后 30% 出现）
_formula = ax_m.text(
    CONCLUSION_BODY_POS[0], CONCLUSION_BODY_POS[1],
    CONCLUSION_BODY,
    ha=CONCLUSION_BODY_HA, va=CONCLUSION_BODY_VA, fontsize=CONCLUSION_BODY_SIZE, color=CARD_BODY_COLOR,
    style="italic", alpha=0.0, transform=ax_m.transAxes, linespacing=BODY_LINE_HEIGHT,
)

ALL_ARTISTS = (
    _glow_lines + _lines + _tip_labels
    + [_vline, shock_t]
    + _val_texts
    + [_gap_line, _gap_tick_top, _gap_tick_bot, _gap_text,
       _conclusion, _conclusion_badge, _formula]
)


# ── 工具函数 ──────────────────────────────────────────────────

def _set_curve(idx: int, xs, ys) -> None:
    _glow_lines[idx].set_data(xs, ys)
    _lines[idx].set_data(xs, ys)


def _hide_scene3() -> None:
    for _tl in _tip_labels:
        _tl.set_text("")
        _tl.set_alpha(0)
    for _vt in _val_texts:
        _vt.set_text("")
        _vt.set_alpha(0)
    _gap_line.set_alpha(0)
    _gap_tick_top.set_alpha(0)
    _gap_tick_bot.set_alpha(0)
    _gap_text.set_text("")
    _gap_text.set_alpha(0)
    _conclusion.set_alpha(0)
    _conclusion_badge.set_alpha(0)
    _formula.set_alpha(0)


# ── init ─────────────────────────────────────────────────────

def init():
    for i in range(len(SCENARIOS)):
        _set_curve(i, [], [])
    for _tl in _tip_labels:
        _tl.set_text("")
        _tl.set_alpha(0)
    _vline.set_data([], [])
    _vline.set_alpha(0)
    shock_t.set_alpha(0)
    _hide_scene3()
    return ALL_ARTISTS


# ── animate ───────────────────────────────────────────────────

def animate(frame: int):
    global _CURRENT_ANIM_FRAME
    _CURRENT_ANIM_FRAME = frame
    if _using_frame_cache() and frame_png_path(Path(VIDEO_FRAME_CACHE_DIR), frame).is_file():
        return ALL_ARTISTS

    # ── Scene 1: 冲击标题 ─────────────────────────────────────
    if frame < T1:
        t = frame / T1
        # 前 30% 匀速淡入，之后保持
        shock_alpha = _ease(min(t / 0.24, 1.0)) if HOOK_MODE == "hero-spotlight" else _ease(min(t / 0.30, 1.0))
        shock_t.set_alpha(shock_alpha)
        for i in range(len(SCENARIOS)):
            _set_curve(i, [], [])
        _vline.set_data([], [])
        _vline.set_alpha(0)
        _hide_scene3()
        return ALL_ARTISTS

    # ── Scene 2: 曲线匀速生长，无标签 ────────────────────────
    if frame < T2:
        local = frame - T1
        t = local / (T2 - T1)

        # shock 在前段淡出；hero 模式给曲线更快出场
        fade_window = 0.18 if HOOK_MODE == "hero-spotlight" else 0.25
        shock_t.set_alpha(_ease(max(0, (fade_window - t) / fade_window)))

        # 匀速展开（线性，无加速感）
        x_reveal = t * YEARS
        mask = YEAR_AXIS <= x_reveal
        for i, _s in enumerate(SCENARIOS):
            if mask.sum() < 2:
                _set_curve(i, [], [])
            else:
                _set_curve(i, YEAR_AXIS[mask], _s["vals"][mask])

        # 年=YEARS 参考线末段出现；full-context 模式更早给上下文
        vline_start = 0.82 if SHOW_REFERENCE_GUIDES else 0.92
        vline_window = 0.12 if SHOW_REFERENCE_GUIDES else 0.08
        _vline.set_data([YEARS, YEARS], [0, MAX_Y])
        _vline.set_alpha(_ease(max(0, (t - vline_start) / vline_window)) * 0.55)

        _hide_scene3()
        return ALL_ARTISTS

    # ── Scene 3: 定格 + 逐步标注 ─────────────────────────────
    local = frame - T2
    t  = local / max(N_FRAMES - T2, 1)
    et = _ease(t)

    shock_t.set_alpha(0)
    _vline.set_data([YEARS, YEARS], [0, MAX_Y])
    _vline.set_alpha(0.55)

    # 全曲线保持完整
    for i, _s in enumerate(SCENARIOS):
        _set_curve(i, YEAR_AXIS, _s["vals"])

    # ① 曲线名称标签
    label_window = 0.24 if SHOW_REFERENCE_GUIDES else 0.30
    label_a = _ease(min(t / label_window, 1.0))
    for _s, _tl, _ny in zip(SCENARIOS, _tip_labels, LABEL_NUDGE):
        _tl.set_position((YEARS - 1, _s["vals"][-1] + _ny))
        _tl.set_text(_s["label"])
        _tl.set_alpha(label_a)

    # ② 终值计数动画
    val_window = 0.42 if SHOW_REFERENCE_GUIDES else 0.50
    val_a = _ease(min(t / val_window, 1.0))
    for _s, _vt, _ny in zip(SCENARIOS, _val_texts, VAL_NUDGE):
        cur = _s["vals"][-1] * et
        _vt.set_position((YEARS + 0.5, _s["vals"][-1] + _ny))
        _vt.set_text(f"{cur:.0f}万\n{_s['sublabel']}")
        _vt.set_alpha(val_a)

    # ③ 缺口括线（30% 后出现，用 35% 渐入）
    bk_a = _ease(max(0, (t - 0.30) / 0.35))
    bas  = SCENARIOS[0]["vals"][-1]
    act  = SCENARIOS[2]["vals"][-1]
    bx   = YEARS - 1.5
    tw   = 0.9
    _gap_line.set_data([bx, bx], [act, bas])
    _gap_line.set_alpha(bk_a * 0.9)
    _gap_tick_top.set_data([bx - tw/2, bx + tw/2], [bas, bas])
    _gap_tick_top.set_alpha(bk_a * 0.9)
    _gap_tick_bot.set_data([bx - tw/2, bx + tw/2], [act, act])
    _gap_tick_bot.set_alpha(bk_a * 0.9)
    cur_gap = (bas - act) * et
    drag_pct = (bas - act) / bas * 100
    _gap_text.set_position((bx + 0.4, (bas + act) / 2))
    _gap_text.set_text(f"少了\n{cur_gap:.0f}万！\n({drag_pct:.0f}%)")
    _gap_text.set_alpha(bk_a)

    # ④ 结论正文与强调标签
    reveal_offsets = {name: idx * 0.12 for idx, name in enumerate(CONCLUSION_REVEAL_ORDER)}
    body_start = 0.44 + reveal_offsets.get("body", 0.0)
    badge_start = 0.48 + reveal_offsets.get("badge", 0.0)
    body_alpha = _ease(max(0, (t - body_start) / 0.20)) * 0.85
    badge_alpha = _ease(max(0, (t - badge_start) / 0.16))
    _formula.set_alpha(body_alpha)
    _conclusion_badge.set_alpha(badge_alpha)

    # ⑤ 结论卡片（70% 后淡入，给观众时间先吸收数字）
    headline_start = 0.56 + reveal_offsets.get("headline", 0.0)
    conclusion_alpha = _ease(max(0, (t - headline_start) / 0.22))
    if CONCLUSION_MODE == "cta-spotlight":
        conclusion_alpha *= min(1.0, CONCLUSION_CARD_SCALE)
    _conclusion.set_alpha(conclusion_alpha)

    return ALL_ARTISTS


# ── 渲染 ──────────────────────────────────────────────────────

anim = FuncAnimation(
    fig, animate, init_func=init,
    frames=N_FRAMES, interval=1000 / FPS, blit=not _using_frame_cache(),
)

out = Path(OUTPUT_FILE)
out.parent.mkdir(parents=True, exist_ok=True)

_savefig_kw = {"facecolor": BG, "edgecolor": "none"}
_cache_path = Path(VIDEO_FRAME_CACHE_DIR) if VIDEO_FRAME_CACHE_DIR else None

if _using_frame_cache() and _cache_path and all_frames_cached(_cache_path, N_FRAMES):
    encode_video_from_png_sequence_ffmpeg(
        out,
        _cache_path,
        N_FRAMES,
        FPS,
        bitrate=VIDEO_BITRATE,
        preset=VIDEO_PRESET,
        crf=VIDEO_CRF,
    )
    print(f"[完成] 全量帧缓存命中，已跳过 matplotlib 逐帧绘制 → {out}")
elif _using_frame_cache() and _cache_path:
    writer = PngCachingFFMpegWriter(
        fps=FPS,
        codec="libx264",
        bitrate=VIDEO_BITRATE,
        cache_dir=str(_cache_path),
        frame_getter=lambda: _CURRENT_ANIM_FRAME,
        extra_args=["-pix_fmt", "yuv420p", "-preset", VIDEO_PRESET, "-crf", str(VIDEO_CRF)],
    )
    print(f"[渲染] {N_FRAMES} 帧 → {out}")
    anim.save(str(out), writer=writer, dpi=DPI, savefig_kwargs=_savefig_kw)
    print(f"[完成] {out}")
else:
    writer = FFMpegWriter(
        fps=FPS, codec="libx264", bitrate=VIDEO_BITRATE,
        extra_args=["-pix_fmt", "yuv420p", "-preset", VIDEO_PRESET, "-crf", str(VIDEO_CRF)],
    )
    print(f"[渲染] {N_FRAMES} 帧 → {out}")
    anim.save(str(out), writer=writer, dpi=DPI, savefig_kwargs=_savefig_kw)
    print(f"[完成] {out}")
