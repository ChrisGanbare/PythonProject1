"""
基金手续费复利侵蚀可视化动画
Flourish 深色风格 | 抖音 / 哔哩哔哩 竖屏 9:16 | 30 秒

场景结构：
  Scene 1  0~5s   — 冲击标题：差距高达 XXX 万！
  Scene 2  5~25s  — 四条复利曲线同步从左向右生长
  Scene 3 25~30s  — 定格，添加终值标注 + 费用侵蚀缺口线
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

# ── 中文字体 ─────────────────────────────────────────────────
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
    print("错误: 未找到 ffmpeg，请先安装 https://ffmpeg.org/download.html")
    raise SystemExit(1)

# ── 参数（可通过环境变量覆盖）────────────────────────────────
PRINCIPAL    = float(os.getenv("VIDEO_PRINCIPAL",    "1000000"))   # 元
GROSS_RETURN = float(os.getenv("VIDEO_GROSS_RETURN", "0.08"))      # 年化毛收益率
YEARS        = int(os.getenv("VIDEO_YEARS",          "30"))
WIDTH        = int(os.getenv("VIDEO_WIDTH",          "1080"))
HEIGHT       = int(os.getenv("VIDEO_HEIGHT",         "1920"))
FPS          = int(os.getenv("VIDEO_FPS",            "30"))
DURATION     = int(os.getenv("VIDEO_DURATION",       "30"))
OUTPUT_FILE  = os.getenv("VIDEO_OUTPUT_FILE",        "runtime/outputs/fund_fee_erosion.mp4")
DPI          = 100

# ── 费用场景 ─────────────────────────────────────────────────
SCENARIOS = [
    {"label": "无费用基准",        "fee": 0.0000, "color": "#22D47E"},
    {"label": "ETF  0.15%/年",     "fee": 0.0015, "color": "#4F9EFF"},
    {"label": "主动基金  1.5%/年", "fee": 0.0150, "color": "#FF7F35"},
    {"label": "高费用  2.0%/年",   "fee": 0.0200, "color": "#F43F5E"},
]

YEAR_AXIS = np.arange(0, YEARS + 1)
for _s in SCENARIOS:
    _s["vals"] = PRINCIPAL * (1 + GROSS_RETURN - _s["fee"]) ** YEAR_AXIS / 10_000  # 万元

BASELINE_FINAL = SCENARIOS[0]["vals"][-1]
MAX_Y = BASELINE_FINAL * 1.15
GAP_ACTIVE = BASELINE_FINAL - SCENARIOS[2]["vals"][-1]   # 主动基金 vs 无费用缺口

# ── 配色 ─────────────────────────────────────────────────────
BG    = "#0D0D1A"
MID   = "#12122A"
SUB   = "#94A3B8"
GOLD  = "#FBBF24"
WHITE = "#FFFFFF"
GRID  = "#2A2A4A"

# ── 时间轴 ───────────────────────────────────────────────────
N_FRAMES = FPS * DURATION
T1 = FPS * 5    # scene 1 结束帧
T2 = FPS * 25   # scene 2 结束帧


def _ease(t: float) -> float:
    t = max(0.0, min(1.0, t))
    return 4 * t ** 3 if t < 0.5 else 1 - (-2 * t + 2) ** 3 / 2


# ── Figure ───────────────────────────────────────────────────
fig = plt.figure(figsize=(WIDTH / DPI, HEIGHT / DPI), dpi=DPI, facecolor=BG)
gs  = fig.add_gridspec(
    3, 1, height_ratios=[2.2, 7.0, 0.8],
    hspace=0, top=0.97, bottom=0.03, left=0.11, right=0.96,
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

# ── Header ──────────────────────────────────────────────────
ax_h.text(
    0.5, 0.95, "基金手续费的复利侵蚀",
    ha="center", va="top", fontsize=36, fontweight="bold",
    color=WHITE, transform=ax_h.transAxes,
)
ax_h.text(
    0.5, 0.63, "同样的收益率，每年多 1.5% 费用",
    ha="center", va="top", fontsize=22, color=SUB,
    transform=ax_h.transAxes,
)
ax_h.text(
    0.5, 0.42, "30 年后差了多少？",
    ha="center", va="top", fontsize=22, color=SUB,
    transform=ax_h.transAxes,
)

# 冲击数字（动画中渐显）
shock_t = ax_h.text(
    0.5, 0.16,
    f"差距高达  {GAP_ACTIVE:.0f} 万元！",
    ha="center", va="top", fontsize=44, fontweight="bold",
    color=GOLD, alpha=0.0, transform=ax_h.transAxes,
    bbox=dict(
        boxstyle="round,pad=0.25",
        facecolor="#1C1C3A", edgecolor=GOLD, linewidth=1.5, alpha=0,
    ),
)

# ── Footer ──────────────────────────────────────────────────
ax_f.text(
    0.5, 0.5,
    f"初始本金 {PRINCIPAL / 10_000:.0f} 万元 | 年化毛收益 {GROSS_RETURN * 100:.0f}%"
    f" | 投资 {YEARS} 年",
    ha="center", va="center", fontsize=14, color=SUB,
    transform=ax_f.transAxes,
)

# ── Main chart ──────────────────────────────────────────────
ax_m.set_facecolor(MID)
ax_m.set_xlim(0, YEARS)
ax_m.set_ylim(0, MAX_Y)
ax_m.tick_params(colors=SUB, labelsize=16)
ax_m.set_xlabel("投资年限（年）", color=SUB, fontsize=18, labelpad=6)
ax_m.set_ylabel("资产价值（万元）", color=SUB, fontsize=18, labelpad=6)
for _sp in ax_m.spines.values():
    _sp.set_visible(True)
    _sp.set_color(GRID)
    _sp.set_linewidth(0.8)
ax_m.yaxis.grid(True, color=GRID, linewidth=0.5, alpha=0.7)
ax_m.set_axisbelow(True)
ax_m.set_xticks(range(0, YEARS + 1, 5))

# ── Line artists ─────────────────────────────────────────────
_lines: list = []
_tip_labels: list = []
for _s in SCENARIOS:
    _ln, = ax_m.plot([], [], color=_s["color"], linewidth=4,
                     solid_capstyle="round", zorder=4)
    _lines.append(_ln)
    _tl = ax_m.text(
        0, 0, "", color=_s["color"], fontsize=16, fontweight="bold",
        va="center", ha="left", zorder=5, alpha=0.0,
    )
    _tip_labels.append(_tl)

# Year-30 vertical reference line
_vline, = ax_m.plot([], [], color=GRID, linewidth=1.2,
                    linestyle="--", zorder=2, alpha=0.0)

# ── Scene 3 artists ──────────────────────────────────────────

# Final value text labels at year=30
_val_texts: list = []
for _s in SCENARIOS:
    _vt = ax_m.text(
        0, 0, "", color=_s["color"], fontsize=18, fontweight="bold",
        va="center", ha="left", zorder=5, alpha=0.0,
    )
    _val_texts.append(_vt)

# Gap bracket: vertical line from active-fund final to baseline final
_gap_line, = ax_m.plot([], [], color=GOLD, linewidth=2.0,
                       linestyle="-", zorder=3, alpha=0.0)
# Tick marks at both ends of the bracket
_gap_tick_top, = ax_m.plot([], [], color=GOLD, linewidth=2.0, zorder=3, alpha=0.0)
_gap_tick_bot, = ax_m.plot([], [], color=GOLD, linewidth=2.0, zorder=3, alpha=0.0)
_gap_text = ax_m.text(
    0, 0, "", color=GOLD, fontsize=17, fontweight="bold",
    va="center", ha="right", zorder=5, alpha=0.0,
)

ALL_ARTISTS = (
    _lines + _tip_labels + [_vline, shock_t]
    + _val_texts + [_gap_line, _gap_tick_top, _gap_tick_bot, _gap_text]
)


def init():
    for _ln in _lines:
        _ln.set_data([], [])
    for _tl in _tip_labels:
        _tl.set_text("")
        _tl.set_alpha(0)
    _vline.set_data([], [])
    _vline.set_alpha(0)
    shock_t.set_alpha(0)
    for _vt in _val_texts:
        _vt.set_text("")
        _vt.set_alpha(0)
    _gap_line.set_data([], [])
    _gap_line.set_alpha(0)
    _gap_tick_top.set_data([], [])
    _gap_tick_top.set_alpha(0)
    _gap_tick_bot.set_data([], [])
    _gap_tick_bot.set_alpha(0)
    _gap_text.set_text("")
    _gap_text.set_alpha(0)
    return ALL_ARTISTS


def animate(frame: int):
    # ── Scene 1: 冲击标题淡入 ─────────────────────────────────
    if frame < T1:
        t  = frame / T1
        et = _ease(t)
        shock_t.set_alpha(et if t > 0.25 else _ease(max(0, (t - 0.25) / 0.75)))
        for _ln in _lines:
            _ln.set_data([], [])
        for _tl in _tip_labels:
            _tl.set_text("")
            _tl.set_alpha(0)
        _vline.set_data([], [])
        _vline.set_alpha(0)
        for _vt in _val_texts:
            _vt.set_text("")
            _vt.set_alpha(0)
        _gap_line.set_alpha(0)
        _gap_tick_top.set_alpha(0)
        _gap_tick_bot.set_alpha(0)
        _gap_text.set_alpha(0)
        return ALL_ARTISTS

    # ── Scene 2: 曲线从左向右生长 ────────────────────────────
    if frame < T2:
        local = frame - T1
        t  = local / (T2 - T1)
        et = _ease(t)

        # 冲击文字在场景 2 后半段淡出
        shock_t.set_alpha(_ease(max(0, (0.6 - t) / 0.4)))

        x_reveal = et * YEARS
        mask = YEAR_AXIS <= x_reveal

        for _s, _ln, _tl in zip(SCENARIOS, _lines, _tip_labels):
            if mask.sum() < 2:
                _ln.set_data([], [])
                _tl.set_text("")
                _tl.set_alpha(0)
                continue
            _ln.set_data(YEAR_AXIS[mask], _s["vals"][mask])
            tip_x = float(YEAR_AXIS[mask][-1])
            tip_y = float(_s["vals"][mask][-1])
            _tl.set_position((tip_x + 0.4, tip_y))
            _tl.set_text(_s["label"])
            label_a = _ease(max(0, (t - 0.08) / 0.20))
            _tl.set_alpha(label_a)

        # 年=30 参考线在最后 15% 出现
        vline_a = _ease(max(0, (t - 0.85) / 0.15))
        _vline.set_data([YEARS, YEARS], [0, MAX_Y])
        _vline.set_alpha(vline_a * 0.55)

        for _vt in _val_texts:
            _vt.set_text("")
            _vt.set_alpha(0)
        _gap_line.set_alpha(0)
        _gap_tick_top.set_alpha(0)
        _gap_tick_bot.set_alpha(0)
        _gap_text.set_alpha(0)
        return ALL_ARTISTS

    # ── Scene 3: 定格 + 缺口标注 ────────────────────────────
    local = frame - T2
    t  = local / max(N_FRAMES - T2, 1)
    et = _ease(t)

    shock_t.set_alpha(0)

    # 全曲线显示
    for _s, _ln in zip(SCENARIOS, _lines):
        _ln.set_data(YEAR_AXIS, _s["vals"])

    # 曲线末端标签移至稍靠左，避免与终值文字重叠
    for _s, _tl in zip(SCENARIOS, _tip_labels):
        _tl.set_position((YEARS - 7, _s["vals"][-1]))
        _tl.set_text(_s["label"])
        _tl.set_alpha(1)

    _vline.set_data([YEARS, YEARS], [0, MAX_Y])
    _vline.set_alpha(0.55)

    # 终值文字（年=30 右侧）
    for _s, _vt in zip(SCENARIOS, _val_texts):
        _vt.set_position((YEARS + 0.4, _s["vals"][-1]))
        _vt.set_text(f"{_s['vals'][-1]:.0f}万")
        _vt.set_alpha(et)

    # 缺口括线：无费用基准 vs 主动基金 (最具视觉冲击的一组)
    act_y30 = SCENARIOS[2]["vals"][-1]   # 主动基金 1.5%
    bas_y30 = SCENARIOS[0]["vals"][-1]   # 无费用基准
    bx = YEARS - 2.5                     # 括线 x 位置

    _gap_line.set_data([bx, bx], [act_y30, bas_y30])
    _gap_line.set_alpha(et * 0.9)

    tick_w = 0.6
    _gap_tick_top.set_data([bx - tick_w / 2, bx + tick_w / 2], [bas_y30, bas_y30])
    _gap_tick_top.set_alpha(et * 0.9)
    _gap_tick_bot.set_data([bx - tick_w / 2, bx + tick_w / 2], [act_y30, act_y30])
    _gap_tick_bot.set_alpha(et * 0.9)

    mid_y = (act_y30 + bas_y30) / 2
    drag_pct = (bas_y30 - act_y30) / bas_y30 * 100
    _gap_text.set_position((bx - 0.6, mid_y))
    _gap_text.set_text(f"侵蚀\n{bas_y30 - act_y30:.0f}万\n({drag_pct:.0f}%)")
    _gap_text.set_alpha(et)

    return ALL_ARTISTS


# ── 渲染 ─────────────────────────────────────────────────────
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
