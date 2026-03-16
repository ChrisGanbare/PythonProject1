"""
基金手续费复利侵蚀可视化动画  v3
Flourish 深色风格 | 抖音 / 哔哩哔哩 竖屏 9:16 | 30 秒

场景结构：
  Scene 1   0~8s  — 冲击标题淡入，引发悬念
  Scene 2  8~23s  — 四条曲线匀速生长（无标注，聚焦轨迹差异）
  Scene 3 23~30s  — 定格 + 计数动画 + 缺口标注 + 结论卡片
"""

from __future__ import annotations

import os
import shutil
import warnings
from pathlib import Path

import matplotlib.font_manager as fm
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.animation import FFMpegWriter, FuncAnimation

warnings.filterwarnings("ignore")


# ── 字体 ──────────────────────────────────────────────────────

def _setup_font() -> None:
    preferred = [
        "Microsoft YaHei", "SimHei", "PingFang SC", "STHeiti",
        "Hiragino Sans GB", "Noto Sans CJK SC", "Source Han Sans SC", "SimSun",
    ]
    available = {f.name for f in fm.fontManager.ttflist}
    for name in preferred:
        if name in available:
            plt.rcParams["font.sans-serif"] = [name, "DejaVu Sans"]
            plt.rcParams["axes.unicode_minus"] = False
            print(f"[字体] {name}")
            return
    plt.rcParams["font.sans-serif"] = ["DejaVu Sans"]
    plt.rcParams["axes.unicode_minus"] = False


_setup_font()

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
DPI          = 100


# ── 费用场景（使用真实基金分类名称）──────────────────────────

SCENARIOS = [
    {"label": "零费用基准",   "sublabel": "理论上限",   "fee": 0.0000, "color": "#22D47E"},
    {"label": "指数型ETF",    "sublabel": "0.15%/年",   "fee": 0.0015, "color": "#4F9EFF"},
    {"label": "偏股混合型",   "sublabel": "1.50%/年",   "fee": 0.0150, "color": "#FF7F35"},
    {"label": "高费率权益型", "sublabel": "2.00%/年",   "fee": 0.0200, "color": "#F43F5E"},
]

YEAR_AXIS = np.arange(0, YEARS + 1)
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

# ── 时间轴 ────────────────────────────────────────────────────

N_FRAMES = FPS * DURATION
T1 = FPS * 10   # scene 1 → 2（10s 冲击留白）
T2 = FPS * 38   # scene 2 → 3（28s 曲线生长，近似每年 ~1s）


def _ease(t: float) -> float:
    t = max(0.0, min(1.0, t))
    return 4 * t ** 3 if t < 0.5 else 1 - (-2 * t + 2) ** 3 / 2


# ── Figure ────────────────────────────────────────────────────

fig = plt.figure(figsize=(WIDTH / DPI, HEIGHT / DPI), dpi=DPI, facecolor=BG)
gs  = fig.add_gridspec(
    3, 1,
    height_ratios=[3.5, 5.7, 0.8],
    hspace=0, top=0.97, bottom=0.03, left=0.14, right=0.96,
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

ax_h.text(0.5, 0.97, "基金手续费的复利侵蚀",
          ha="center", va="top", fontsize=60, fontweight="bold",
          color=WHITE, transform=ax_h.transAxes)

ax_h.text(0.5, 0.80, "同样的收益率，每年多 1.5% 费用",
          ha="center", va="top", fontsize=36, color=SUB,
          transform=ax_h.transAxes)

ax_h.text(0.5, 0.66, "30 年后差了多少？",
          ha="center", va="top", fontsize=36, color=SUB,
          transform=ax_h.transAxes)

# 冲击数字（动画渐显）
shock_t = ax_h.text(
    0.5, 0.50,
    f"差距高达  {GAP_ACT:.0f} 万元！",
    ha="center", va="top", fontsize=64, fontweight="bold",
    color=GOLD, alpha=0.0, transform=ax_h.transAxes,
    bbox=dict(
        boxstyle="round,pad=0.3",
        facecolor="#1C1C3A", edgecolor=GOLD, linewidth=2.0,
    ),
)


# ── Footer（两行：假设 + 来源）────────────────────────────────

ax_f.text(
    0.5, 0.72,
    f"本金 {PRINCIPAL / 10_000:.0f} 万元 · 年化毛收益 {GROSS_RETURN * 100:.0f}% · 投资 {YEARS} 年",
    ha="center", va="center", fontsize=22, color=SUB,
    transform=ax_f.transAxes,
)
ax_f.text(
    0.5, 0.22,
    "数据来源：中国基金业协会 2024 · Wind 金融终端 · 仅供参考",
    ha="center", va="center", fontsize=17, color="#64748B",
    transform=ax_f.transAxes,
)


# ── Main chart ────────────────────────────────────────────────

XLIM_MAX = YEARS + 8   # 右侧预留标注空间

ax_m.set_facecolor(MID)
ax_m.set_xlim(0, XLIM_MAX)
ax_m.set_ylim(0, MAX_Y)
ax_m.tick_params(colors=SUB, labelsize=26)
ax_m.set_xlabel("投资年限（年）", color=SUB, fontsize=30, labelpad=10)
ax_m.set_ylabel("资产价值（万元）", color=SUB, fontsize=30, labelpad=10)
for _sp in ax_m.spines.values():
    _sp.set_visible(True)
    _sp.set_color(GRID)
    _sp.set_linewidth(1.0)
ax_m.yaxis.grid(True, color=GRID, linewidth=0.8, alpha=0.6)
ax_m.set_axisbelow(True)
ax_m.set_xticks(range(0, YEARS + 1, 5))

# 静态水平参考线
for _ref_y, _ref_lbl in [(500, "500万"), (1000, "1000万")]:
    if _ref_y < MAX_Y:
        ax_m.axhline(_ref_y, color=GRID, linewidth=0.7,
                     linestyle=":", alpha=0.9, zorder=1)
        ax_m.text(
            -0.01, _ref_y, _ref_lbl,
            ha="right", va="center", fontsize=20, color=SUB, alpha=0.8,
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
        color=_s["color"], fontsize=26, fontweight="bold",
        va="center", ha="right", zorder=5, alpha=0.0,
    )
    _tip_labels.append(_tl)

# 终值数字（ha=left，x=YEARS+0.5，含计数动画）
VAL_NUDGE = [+40, -30, +10, -10]   # 万元，同向偏移

_val_texts: list = []
for _s in SCENARIOS:
    _vt = ax_m.text(
        0, 0, "",
        color=_s["color"], fontsize=28, fontweight="bold",
        va="center", ha="left", zorder=5, alpha=0.0,
    )
    _val_texts.append(_vt)

# 缺口括线（零费用 vs 偏股混合型）
_gap_line,     = ax_m.plot([], [], color=GOLD, linewidth=3.0, zorder=3, alpha=0.0)
_gap_tick_top, = ax_m.plot([], [], color=GOLD, linewidth=3.0, zorder=3, alpha=0.0)
_gap_tick_bot, = ax_m.plot([], [], color=GOLD, linewidth=3.0, zorder=3, alpha=0.0)
_gap_text = ax_m.text(
    0, 0, "",
    color=GOLD, fontsize=26, fontweight="bold",
    va="center", ha="left", zorder=5, alpha=0.0,
)

# 结论卡片（最后 40% 出现）
_conclusion = ax_m.text(
    0.5, 0.97,
    "1.5% 年费率 · 30 年吞噬 34% 财富",
    ha="center", va="top", fontsize=26, fontweight="bold",
    color=GOLD, alpha=0.0, transform=ax_m.transAxes,
    bbox=dict(
        boxstyle="round,pad=0.35",
        facecolor="#1C1C3A", edgecolor=GOLD, linewidth=1.5,
    ),
)

# 计算公式（权威感，最后 30% 出现）
_formula = ax_m.text(
    0.02, 0.04,
    "终值 = 本金 × (1 + r \u2212 f)\u207F",   # unicode 减号 + 上标n
    ha="left", va="bottom", fontsize=20, color=SUB,
    style="italic", alpha=0.0, transform=ax_m.transAxes,
)

ALL_ARTISTS = (
    _glow_lines + _lines + _tip_labels
    + [_vline, shock_t]
    + _val_texts
    + [_gap_line, _gap_tick_top, _gap_tick_bot, _gap_text,
       _conclusion, _formula]
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

    # ── Scene 1: 冲击标题 ─────────────────────────────────────
    if frame < T1:
        t = frame / T1
        # 前 30% 匀速淡入，之后保持
        shock_t.set_alpha(_ease(min(t / 0.30, 1.0)))
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

        # shock 在前 25% 缓慢淡出
        shock_t.set_alpha(_ease(max(0, (0.25 - t) / 0.25)))

        # 匀速展开（线性，无加速感）
        x_reveal = t * YEARS
        mask = YEAR_AXIS <= x_reveal
        for i, _s in enumerate(SCENARIOS):
            if mask.sum() < 2:
                _set_curve(i, [], [])
            else:
                _set_curve(i, YEAR_AXIS[mask], _s["vals"][mask])

        # 年=YEARS 参考线最后 8% 出现
        _vline.set_data([YEARS, YEARS], [0, MAX_Y])
        _vline.set_alpha(_ease(max(0, (t - 0.92) / 0.08)) * 0.55)

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

    # ① 曲线名称标签（前 30% 淡入）
    label_a = _ease(min(t / 0.30, 1.0))
    for _s, _tl, _ny in zip(SCENARIOS, _tip_labels, LABEL_NUDGE):
        _tl.set_position((YEARS - 1, _s["vals"][-1] + _ny))
        _tl.set_text(_s["label"])
        _tl.set_alpha(label_a)

    # ② 终值计数动画（前 50% 完成计数）
    val_a = _ease(min(t / 0.50, 1.0))
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

    # ④ 公式（50% 后淡入）
    _formula.set_alpha(_ease(max(0, (t - 0.50) / 0.25)) * 0.75)

    # ⑤ 结论卡片（70% 后淡入，给观众时间先吸收数字）
    _conclusion.set_alpha(_ease(max(0, (t - 0.70) / 0.25)))

    return ALL_ARTISTS


# ── 渲染 ──────────────────────────────────────────────────────

anim = FuncAnimation(
    fig, animate, init_func=init,
    frames=N_FRAMES, interval=1000 / FPS, blit=True,
)

out = Path(OUTPUT_FILE)
out.parent.mkdir(parents=True, exist_ok=True)

writer = FFMpegWriter(
    fps=FPS, codec="libx264", bitrate=8000,
    extra_args=["-pix_fmt", "yuv420p", "-preset", "medium", "-crf", "20"],
)

print(f"[渲染] {N_FRAMES} 帧 → {out}")
anim.save(str(out), writer=writer, dpi=DPI)
print(f"[完成] {out}")
