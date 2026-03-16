"""
贷款还款方式对比 - 电影级数据可视化动画
等额本息 vs 等额本金 | Flourish风格 | 抖音/B站竖屏9:16
时长: 30秒
"""

import numpy as np
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.patheffects as pe
import matplotlib.font_manager as fm
from matplotlib.animation import FuncAnimation, FFMpegWriter
from matplotlib.patches import FancyBboxPatch
from matplotlib.lines import Line2D
from matplotlib.gridspec import GridSpec
import warnings
import shutil
import os
from pathlib import Path

warnings.filterwarnings('ignore')

# ============================================================
# 字体设置
# ============================================================
def setup_chinese_font():
    preferred = [
        'Microsoft YaHei', 'SimHei', 'PingFang SC',
        'STHeiti', 'Hiragino Sans GB', 'WenQuanYi Micro Hei',
        'Noto Sans CJK SC', 'Source Han Sans SC', 'SimSun',
    ]
    available = {f.name for f in fm.fontManager.ttflist}
    for font in preferred:
        if font in available:
            plt.rcParams['font.sans-serif'] = [font, 'DejaVu Sans']
            plt.rcParams['axes.unicode_minus'] = False
            print(f"[字体] 使用: {font}")
            return font
    plt.rcParams['font.sans-serif'] = ['DejaVu Sans']
    plt.rcParams['axes.unicode_minus'] = False
    print("[字体] 未找到中文字体，使用备用字体")
    return None

FONT_NAME = setup_chinese_font()

# ============================================================
# 检查 ffmpeg
# ============================================================
if not shutil.which('ffmpeg'):
    print("错误: 未找到 ffmpeg！")
    print("请安装: https://ffmpeg.org/download.html")
    exit(1)

# ============================================================
# 贷款参数
# ============================================================
LOAN_AMOUNT   = float(os.getenv("VIDEO_LOAN_AMOUNT", "1000000"))   # 元
ANNUAL_RATE   = float(os.getenv("VIDEO_ANNUAL_RATE", "0.045"))      # 年利率
MONTHLY_RATE  = ANNUAL_RATE / 12
LOAN_YEARS    = int(os.getenv("VIDEO_LOAN_YEARS", "30"))
TOTAL_MONTHS  = LOAN_YEARS * 12

# ============================================================
# 配色方案（深色Flourish风格）
# ============================================================
BG_DARK    = '#0D0D1A'
BG_MID     = '#12122A'
BG_CARD    = '#1C1C3A'
BG_CARD2   = '#1A2040'

EI_BLUE        = '#4F9EFF'   # 等额本息蓝
EI_BLUE_DARK   = '#1E3A8A'
EP_ORANGE      = '#FF7F35'   # 等额本金橙
EP_ORANGE_DARK = '#92350D'

PRINCIPAL_GREEN = '#22D47E'  # 本金绿
INTEREST_RED    = '#F43F5E'  # 利息红
GAP_PINK        = '#EC4899'  # 差额粉
ACCENT_GOLD     = '#FBBF24'  # 金色强调

TEXT_WHITE = '#FFFFFF'
TEXT_GRAY  = '#94A3B8'
TEXT_DIM   = '#4B5563'

# ============================================================
# 视频规格（竖屏 9:16）
# ============================================================
FIG_W        = int(os.getenv("VIDEO_WIDTH", "1080")) / 100
FIG_H        = int(os.getenv("VIDEO_HEIGHT", "1920")) / 100
DPI          = 100
FPS          = int(os.getenv("VIDEO_FPS", "30"))
TOTAL_SECS   = int(os.getenv("VIDEO_DURATION", "30"))
TOTAL_FRAMES = FPS * TOTAL_SECS

# 场景边界（帧号）
F_INTRO_END  = int(5  * FPS)   # 0–5s   开场
F_ANIM_END   = int(25 * FPS)   # 5–25s  主动画
F_CONC_END   = TOTAL_FRAMES    # 25–30s 结论

# ============================================================
# 缓动函数
# ============================================================
def ease_in_out(t):
    t = max(0.0, min(1.0, t))
    return t * t * (3 - 2 * t)

def ease_out_cubic(t):
    t = max(0.0, min(1.0, t))
    return 1 - (1 - t) ** 3

def clamp(v, lo=0.0, hi=1.0):
    return max(lo, min(hi, v))

# ============================================================
# 贷款计算
# ============================================================
def calculate_loan_data():
    monthly_ei = (LOAN_AMOUNT * MONTHLY_RATE *
                  (1 + MONTHLY_RATE) ** TOTAL_MONTHS /
                  ((1 + MONTHLY_RATE) ** TOTAL_MONTHS - 1))
    ep_principal = LOAN_AMOUNT / TOTAL_MONTHS

    data = []
    rem_ei, rem_ep = LOAN_AMOUNT, LOAN_AMOUNT
    cum_ei_int = cum_ep_int = 0.0

    for i in range(TOTAL_MONTHS):
        ei_int  = rem_ei * MONTHLY_RATE
        ei_prin = monthly_ei - ei_int
        rem_ei -= ei_prin
        cum_ei_int += ei_int

        ep_int  = rem_ep * MONTHLY_RATE
        rem_ep -= ep_principal
        cum_ep_int += ep_int

        data.append({
            'month'         : i + 1,
            'ei_principal'  : ei_prin,
            'ei_interest'   : ei_int,
            'ei_total'      : monthly_ei,
            'ep_principal'  : ep_principal,
            'ep_interest'   : ep_int,
            'ep_total'      : ep_principal + ep_int,
            'cum_ei'        : cum_ei_int,
            'cum_ep'        : cum_ep_int,
            'gap'           : cum_ei_int - cum_ep_int,
        })
    return data, monthly_ei, ep_principal

print("计算贷款数据...")
LOAN_DATA, EI_MONTHLY, EP_FIXED_PRIN = calculate_loan_data()

CUM_EI   = [d['cum_ei']  for d in LOAN_DATA]
CUM_EP   = [d['cum_ep']  for d in LOAN_DATA]
GAP_LIST = [d['gap']     for d in LOAN_DATA]
FINAL_EI  = CUM_EI[-1]
FINAL_EP  = CUM_EP[-1]
FINAL_GAP = FINAL_EI - FINAL_EP
EP_FIRST_MONTH = LOAN_DATA[0]['ep_total']
EP_LAST_MONTH  = LOAN_DATA[-1]['ep_total']

print(f"  等额本息: 月供={EI_MONTHLY:.0f}元  总利息={FINAL_EI/10000:.1f}万")
print(f"  等额本金: 首月={EP_FIRST_MONTH:.0f}元  总利息={FINAL_EP/10000:.1f}万")
print(f"  差额: {FINAL_GAP/10000:.1f}万")

# 关键节点（月 → 标签）
KEY_MILESTONES = {12: '1年', 60: '5年', 120: '10年', 240: '20年', 360: '30年'}

# ============================================================
# 创建画布与轴（固定布局，不在 update 里重建）
# ============================================================
print("创建画布...")
fig = plt.figure(figsize=(FIG_W, FIG_H), facecolor=BG_DARK)

gs = GridSpec(
    5, 1, figure=fig,
    height_ratios=[0.9, 0.75, 3.0, 3.0, 1.35],
    hspace=0.08,
    left=0.06, right=0.94,
    top=0.97, bottom=0.03,
)

ax_title  = fig.add_subplot(gs[0])   # 标题栏（常驻）
ax_info   = fig.add_subplot(gs[1])   # 参数/当月信息
ax_top    = fig.add_subplot(gs[2])   # 柱状图 / 介绍内容
ax_bottom = fig.add_subplot(gs[3])   # 折线图 / 分叉图 / 结论
ax_foot   = fig.add_subplot(gs[4])   # 进度/底部说明

for ax in [ax_title, ax_info, ax_top, ax_bottom, ax_foot]:
    ax.set_facecolor(BG_DARK)
    ax.axis('off')

# ============================================================
# 工具函数
# ============================================================
def clear_ax(ax, bg=BG_DARK):
    ax.clear()
    ax.set_facecolor(bg)
    ax.axis('off')

def glow_line(ax, x, y, color, lw=3, glow_lw=10, glow_alpha=0.18):
    """带光晕的折线"""
    ax.plot(x, y, color=color, linewidth=glow_lw, alpha=glow_alpha,
            solid_capstyle='round', zorder=2)
    ax.plot(x, y, color=color, linewidth=lw, alpha=0.95,
            solid_capstyle='round', zorder=3)

def card_rect(ax, x, y, w, h, edge_color, face_color=BG_CARD, alpha=0.92, lw=1.8):
    r = FancyBboxPatch((x, y), w, h, boxstyle='round,pad=0.4',
                       facecolor=face_color, edgecolor=edge_color,
                       linewidth=lw, alpha=alpha, zorder=5)
    ax.add_patch(r)
    return r

# ============================================================
# 常驻标题栏（每帧都画）
# ============================================================
def draw_title(alpha=1.0):
    ax_title.clear()
    ax_title.set_facecolor(BG_DARK)
    ax_title.set_xlim(0, 100)
    ax_title.set_ylim(0, 100)
    ax_title.axis('off')

    card_rect(ax_title, 1, 10, 98, 80, '#2D3A60', BG_CARD, alpha=alpha * 0.9)

    ax_title.text(50, 82, '贷款还款方式对比',
                  fontsize=20, fontweight='bold', color=TEXT_WHITE,
                  ha='center', va='center', alpha=alpha, zorder=6)

    ax_title.text(28, 58, '等额本息', fontsize=14, fontweight='bold',
                  color=EI_BLUE, ha='center', va='center', alpha=alpha, zorder=6)
    ax_title.text(50, 58, 'vs', fontsize=12, color=TEXT_GRAY,
                  ha='center', va='center', alpha=alpha, zorder=6)
    ax_title.text(72, 58, '等额本金', fontsize=14, fontweight='bold',
                  color=EP_ORANGE, ha='center', va='center', alpha=alpha, zorder=6)

    ax_title.plot([5, 95], [42, 42], color='#334155', linewidth=0.8, alpha=0.5 * alpha)

    for label, value, cx in [('贷款', '100万', 22), ('利率', '4.5%/年', 50), ('期限', '30年', 78)]:
        ax_title.text(cx, 32, label, fontsize=9, color=TEXT_GRAY,
                      ha='center', va='center', alpha=alpha, zorder=6)
        ax_title.text(cx, 20, value, fontsize=11, fontweight='bold',
                      color=ACCENT_GOLD, ha='center', va='center', alpha=alpha, zorder=6)

# ============================================================
# 场景1：开场介绍  (0–5s)
# ============================================================
def draw_intro(frame):
    t = frame / F_INTRO_END   # 0→1

    draw_title(alpha=ease_out_cubic(clamp(t * 4)))

    # info 区域空白
    clear_ax(ax_info)
    clear_ax(ax_foot)

    # ── 阶段A (t<0.35)：贷款参数卡片 ──
    if t < 0.35:
        t_a = t / 0.35
        clear_ax(ax_top)
        ax_top.set_xlim(0, 100)
        ax_top.set_ylim(0, 100)

        ax_top.text(50, 90, '您的贷款条件', fontsize=19, fontweight='bold',
                    color=TEXT_WHITE, ha='center', va='center',
                    alpha=ease_out_cubic(clamp(t_a * 3)), zorder=6)

        params = [
            ('💰  贷款金额', '100 万元', EI_BLUE,    70),
            ('📈  年利率',   '4.5 %',   ACCENT_GOLD, 50),
            ('📅  贷款期限', '30年 / 360期', EP_ORANGE, 30),
        ]
        for i, (lbl, val, color, cy) in enumerate(params):
            a = ease_out_cubic(clamp(t_a * 2.5 - i * 0.25))
            card_rect(ax_top, 8, cy - 8, 84, 14, color, BG_CARD, alpha=a * 0.9)
            ax_top.text(16, cy, lbl, fontsize=13, color=TEXT_GRAY,
                        ha='left', va='center', alpha=a, zorder=6)
            ax_top.text(90, cy, val, fontsize=15, fontweight='bold',
                        color=color, ha='right', va='center', alpha=a, zorder=6)

        clear_ax(ax_bottom)
        ax_bottom.set_xlim(0, 100)
        ax_bottom.set_ylim(0, 100)
        ax_bottom.text(50, 50,
                       '接下来：\n两种还款方式 30年的利息差距\n究竟有多大？',
                       fontsize=16, color=TEXT_GRAY, ha='center', va='center',
                       alpha=ease_out_cubic(clamp(t_a * 2 - 0.8)), linespacing=1.8, zorder=6)

    # ── 阶段B (0.35–0.70)：两条路径分叉 ──
    elif t < 0.70:
        t_b = (t - 0.35) / 0.35

        clear_ax(ax_top)
        ax_top.set_xlim(0, 100)
        ax_top.set_ylim(0, 100)

        alpha0 = ease_out_cubic(clamp(t_b * 3))
        ax_top.text(50, 92, '两种路径，同一终点', fontsize=18, fontweight='bold',
                    color=TEXT_WHITE, ha='center', alpha=alpha0, zorder=6)
        ax_top.text(50, 84, '30年后，谁多付了更多利息？',
                    fontsize=12, color=TEXT_GRAY, ha='center', alpha=alpha0, zorder=6)

        # 起点
        sx, sy = 12, 55
        ax_top.plot(sx, sy, 'o', color=ACCENT_GOLD, markersize=18, zorder=7)
        ax_top.text(sx, 44, '起点\n100万', fontsize=11, color=ACCENT_GOLD,
                    ha='center', va='top', fontweight='bold', alpha=alpha0, zorder=6)

        if t_b > 0.2:
            pt = ease_in_out(clamp((t_b - 0.2) / 0.8))

            # 等额本息（蓝，向上分叉）
            ex = sx + pt * 72
            ey = sy + pt * 22
            ax_top.annotate('', xy=(ex, ey), xytext=(sx, sy),
                            arrowprops=dict(arrowstyle='->', color=EI_BLUE, lw=3.5), zorder=6)

            # 等额本金（橙，向下分叉）
            ox = sx + pt * 72
            oy = sy - pt * 22
            ax_top.annotate('', xy=(ox, oy), xytext=(sx, sy),
                            arrowprops=dict(arrowstyle='->', color=EP_ORANGE, lw=3.5), zorder=6)

            if pt > 0.45:
                la = ease_out_cubic(clamp((pt - 0.45) / 0.55))
                card_rect(ax_top, ex - 2, ey + 2, 42, 16, EI_BLUE, EI_BLUE_DARK, alpha=la * 0.92)
                ax_top.text(ex + 19, ey + 13, '等额本息', fontsize=13,
                            color=TEXT_WHITE, ha='center', fontweight='bold', alpha=la, zorder=7)
                ax_top.text(ex + 19, ey + 5,  f'月供固定 {EI_MONTHLY:.0f}元',
                            fontsize=10, color=EI_BLUE, ha='center', alpha=la, zorder=7)

                card_rect(ax_top, ox - 2, oy - 18, 42, 16, EP_ORANGE, EP_ORANGE_DARK, alpha=la * 0.92)
                ax_top.text(ox + 19, oy - 7,  '等额本金', fontsize=13,
                            color=TEXT_WHITE, ha='center', fontweight='bold', alpha=la, zorder=7)
                ax_top.text(ox + 19, oy - 15, f'首月 {EP_FIRST_MONTH:.0f}元',
                            fontsize=10, color=EP_ORANGE, ha='center', alpha=la, zorder=7)

        clear_ax(ax_bottom)
        ax_bottom.set_xlim(0, 100)
        ax_bottom.set_ylim(0, 100)
        ta2 = ease_out_cubic(clamp((t_b - 0.5) / 0.5))
        ax_bottom.text(50, 55, '■ 绿色=本金  ■ 红色=利息',
                       fontsize=13, color=TEXT_GRAY, ha='center', va='center', alpha=ta2, zorder=6)
        ax_bottom.text(50, 40, '早期利息占大头？\n看下面的动画！',
                       fontsize=16, fontweight='bold', color=ACCENT_GOLD, ha='center', va='center',
                       alpha=ta2, linespacing=1.8, zorder=6)

    # ── 阶段C (0.70–1.00)：淡出过渡 ──
    else:
        t_c  = (t - 0.70) / 0.30
        fade = 1 - ease_in_out(t_c)
        draw_title(alpha=fade)
        clear_ax(ax_top)
        clear_ax(ax_bottom)

# ============================================================
# 场景2：主动画  (5–25s)
# ============================================================
def draw_main(frame):
    t = (frame - F_INTRO_END) / (F_ANIM_END - F_INTRO_END)   # 0→1

    # 当前月份推进策略：
    #   0–10%：第1–12月（慢，逐月感）
    #   10–35%：第12–60月（中速，展示前5年）
    #   35–100%：第60–360月（加速，看全局）
    if t < 0.10:
        cur = max(1, int(ease_in_out(t / 0.10) * 12))
    elif t < 0.35:
        cur = int(12 + ease_in_out((t - 0.10) / 0.25) * 48)
    else:
        cur = int(60 + ease_in_out((t - 0.35) / 0.65) * 300)
    cur = min(cur, TOTAL_MONTHS)

    draw_title()
    _draw_info_cards(cur)
    _draw_bar_chart(cur)
    _draw_cum_lines(cur)
    _draw_progress(t, cur)

def _draw_info_cards(cur):
    """当月数据卡片"""
    clear_ax(ax_info)
    ax_info.set_xlim(0, 100)
    ax_info.set_ylim(0, 100)

    d = LOAN_DATA[cur - 1]
    yr, mo = divmod(cur, 12)
    if mo == 0:
        yr_str = f'第 {yr} 年整'
    else:
        yr_str = f'第 {yr} 年 {mo:02d} 月'

    ax_info.text(50, 88, yr_str, fontsize=14, fontweight='bold',
                 color=ACCENT_GOLD, ha='center', va='center', zorder=6)

    # 等额本息卡
    card_rect(ax_info, 1, 5, 47, 68, EI_BLUE)
    ax_info.text(25, 65, '等额本息', fontsize=11, color=EI_BLUE,
                 ha='center', fontweight='bold', zorder=6)
    ax_info.text(25, 52, f'{d["ei_total"]:.0f}元', fontsize=13,
                 color=TEXT_WHITE, ha='center', fontweight='bold', zorder=6)
    ax_info.text(25, 40, f'本金 {d["ei_principal"]:.0f}',
                 fontsize=9, color=PRINCIPAL_GREEN, ha='center', zorder=6)
    ax_info.text(25, 28, f'利息 {d["ei_interest"]:.0f}',
                 fontsize=9, color=INTEREST_RED, ha='center', zorder=6)
    pct = d['ei_interest'] / d['ei_total'] * 100
    ax_info.text(25, 16, f'利息占比 {pct:.0f}%',
                 fontsize=8, color=TEXT_GRAY, ha='center', zorder=6)

    # 等额本金卡
    card_rect(ax_info, 52, 5, 47, 68, EP_ORANGE)
    ax_info.text(75, 65, '等额本金', fontsize=11, color=EP_ORANGE,
                 ha='center', fontweight='bold', zorder=6)
    ax_info.text(75, 52, f'{d["ep_total"]:.0f}元', fontsize=13,
                 color=TEXT_WHITE, ha='center', fontweight='bold', zorder=6)
    ax_info.text(75, 40, f'本金 {d["ep_principal"]:.0f}',
                 fontsize=9, color=PRINCIPAL_GREEN, ha='center', zorder=6)
    ax_info.text(75, 28, f'利息 {d["ep_interest"]:.0f}',
                 fontsize=9, color=INTEREST_RED, ha='center', zorder=6)
    pct2 = d['ep_interest'] / d['ep_total'] * 100
    ax_info.text(75, 16, f'利息占比 {pct2:.0f}%',
                 fontsize=8, color=TEXT_GRAY, ha='center', zorder=6)

def _draw_bar_chart(cur):
    """月供堆叠柱状图（滑动窗口显示最近≤60个月）"""
    ax_top.clear()
    ax_top.set_facecolor(BG_MID)

    # 窗口：最近60个月
    win_end   = cur
    win_start = max(1, cur - 59)
    months    = list(range(win_start, win_end + 1))
    n         = len(months)

    max_y = LOAN_DATA[0]['ep_total'] * 1.18
    ax_top.set_xlim(0, n + 1)
    ax_top.set_ylim(0, max_y)

    bw = 0.36

    for i, m in enumerate(months):
        d  = LOAN_DATA[m - 1]
        xi = i + 1

        # 等额本息（左柱，蓝边框）
        ax_top.bar(xi - bw / 2, d['ei_principal'], width=bw,
                   color=PRINCIPAL_GREEN, alpha=0.88, zorder=3)
        ax_top.bar(xi - bw / 2, d['ei_interest'], width=bw,
                   bottom=d['ei_principal'], color=INTEREST_RED, alpha=0.88, zorder=3)
        ax_top.bar(xi - bw / 2, d['ei_total'], width=bw,
                   color='none', edgecolor=EI_BLUE, linewidth=1.2, zorder=4)

        # 等额本金（右柱，橙边框）
        ax_top.bar(xi + bw / 2, d['ep_principal'], width=bw,
                   color=PRINCIPAL_GREEN, alpha=0.60, zorder=3)
        ax_top.bar(xi + bw / 2, d['ep_interest'], width=bw,
                   bottom=d['ep_principal'], color=INTEREST_RED, alpha=0.60, zorder=3)
        ax_top.bar(xi + bw / 2, d['ep_total'], width=bw,
                   color='none', edgecolor=EP_ORANGE, linewidth=1.2, zorder=4)

    # 当前月高亮竖线
    ax_top.axvline(x=n, color=ACCENT_GOLD, linewidth=1.5,
                   alpha=0.55, linestyle='--', zorder=2)

    # 标题
    ax_top.text(n / 2 + 0.5, max_y * 0.97,
                f'月供结构（第{win_start}–{win_end}期）',
                fontsize=13, fontweight='bold', color=TEXT_WHITE,
                ha='center', va='top', zorder=6,
                path_effects=[pe.withStroke(linewidth=2, foreground=BG_DARK)])

    # 图例
    legend_handles = [
        mpatches.Patch(facecolor=PRINCIPAL_GREEN, label='本金'),
        mpatches.Patch(facecolor=INTEREST_RED,    label='利息'),
        Line2D([0], [0], color=EI_BLUE,   linewidth=2, label='等额本息'),
        Line2D([0], [0], color=EP_ORANGE, linewidth=2, label='等额本金'),
    ]
    ax_top.legend(handles=legend_handles, loc='upper right',
                  fontsize=8, facecolor=BG_CARD, edgecolor='#334155',
                  labelcolor=TEXT_WHITE, framealpha=0.9)

    # 坐标轴
    ax_top.set_ylabel('月供（元）', fontsize=9, color=TEXT_GRAY)
    ax_top.tick_params(colors=TEXT_GRAY, labelsize=7)
    ax_top.yaxis.set_major_formatter(
        matplotlib.ticker.FuncFormatter(lambda x, _: f'{x/1000:.0f}k'))
    ax_top.set_xticks([])
    for sp in ax_top.spines.values():
        sp.set_edgecolor('#2D3A60')
    ax_top.grid(True, axis='y', alpha=0.12, linestyle='--', color=TEXT_GRAY)

def _draw_cum_lines(cur):
    """累计利息折线图（动态生长）"""
    ax_bottom.clear()
    ax_bottom.set_facecolor(BG_MID)

    months = list(range(1, cur + 1))
    ei_c   = [CUM_EI[i] / 10000 for i in range(cur)]
    ep_c   = [CUM_EP[i] / 10000 for i in range(cur)]
    max_y  = FINAL_EI / 10000 * 1.12

    ax_bottom.set_xlim(0, TOTAL_MONTHS + 12)
    ax_bottom.set_ylim(0, max_y)

    if cur > 1:
        # 差距填充
        ax_bottom.fill_between(months, ei_c, ep_c,
                               alpha=0.22, color=GAP_PINK, zorder=1)

        # 等额本金线（先画，在后）
        glow_line(ax_bottom, months, ep_c, EP_ORANGE, lw=3, glow_lw=10)
        # 等额本息线
        glow_line(ax_bottom, months, ei_c, EI_BLUE,    lw=3, glow_lw=10)

        # 端点圆点
        ax_bottom.plot(cur, ei_c[-1], 'o', color=EI_BLUE,   markersize=9, zorder=7)
        ax_bottom.plot(cur, ep_c[-1], 'o', color=EP_ORANGE, markersize=9, zorder=7)

        # 当前值标注（右侧）
        if cur < TOTAL_MONTHS - 20:
            ax_bottom.text(cur + 4, ei_c[-1],
                           f'{ei_c[-1]:.1f}万', fontsize=10,
                           color=EI_BLUE, va='center', fontweight='bold')
            ax_bottom.text(cur + 4, ep_c[-1],
                           f'{ep_c[-1]:.1f}万', fontsize=10,
                           color=EP_ORANGE, va='center', fontweight='bold')

        # 差额标注气泡
        gap_now = ei_c[-1] - ep_c[-1]
        if gap_now > 0.8 and cur > 15:
            mid_y  = (ei_c[-1] + ep_c[-1]) / 2
            label_x = max(10, cur - 30)
            ax_bottom.text(label_x, mid_y,
                           f'差额\n{gap_now:.1f}万',
                           fontsize=10, color=GAP_PINK, ha='center', va='center',
                           fontweight='bold', zorder=8,
                           bbox=dict(boxstyle='round,pad=0.35', facecolor=BG_DARK,
                                     edgecolor=GAP_PINK, alpha=0.85, linewidth=1.5))

        # 关键节点竖线 + 标注
        for m, label in KEY_MILESTONES.items():
            if m <= cur:
                ax_bottom.axvline(x=m, color=TEXT_DIM, linewidth=0.8,
                                  alpha=0.45, linestyle=':', zorder=2)
                ax_bottom.text(m, max_y * 0.97, label, fontsize=8,
                               color=TEXT_DIM, ha='center', va='top')

    # 标题
    ax_bottom.text(TOTAL_MONTHS / 2, max_y * 0.97, '累计利息走势',
                   fontsize=13, fontweight='bold', color=TEXT_WHITE,
                   ha='center', va='top', zorder=6,
                   path_effects=[pe.withStroke(linewidth=2, foreground=BG_DARK)])

    # 图例
    ei_hdl = Line2D([0], [0], color=EI_BLUE,   linewidth=3, label='等额本息')
    ep_hdl = Line2D([0], [0], color=EP_ORANGE, linewidth=3, label='等额本金')
    ax_bottom.legend(handles=[ei_hdl, ep_hdl], loc='upper left',
                     fontsize=10, facecolor=BG_CARD, edgecolor='#334155',
                     labelcolor=TEXT_WHITE, framealpha=0.9)

    # 坐标轴
    ax_bottom.set_ylabel('累计利息（万元）', fontsize=9, color=TEXT_GRAY)
    ax_bottom.tick_params(colors=TEXT_GRAY, labelsize=7)
    year_ticks  = [60, 120, 180, 240, 300, 360]
    year_labels = ['5年', '10年', '15年', '20年', '25年', '30年']
    ax_bottom.set_xticks(year_ticks)
    ax_bottom.set_xticklabels(year_labels, fontsize=8, color=TEXT_GRAY)
    for sp in ax_bottom.spines.values():
        sp.set_edgecolor('#2D3A60')
    ax_bottom.grid(True, alpha=0.12, linestyle='--', color=TEXT_GRAY)

def _draw_progress(t, cur):
    """底部进度条 + 实时累计数字"""
    clear_ax(ax_foot)
    ax_foot.set_xlim(0, 100)
    ax_foot.set_ylim(0, 100)

    # 进度条背景
    card_rect(ax_foot, 4, 72, 92, 14, '#2D3A60', BG_CARD, alpha=0.8)
    pct = cur / TOTAL_MONTHS
    if pct > 0:
        card_rect(ax_foot, 4, 72, 92 * pct, 14, EI_BLUE, EI_BLUE, alpha=0.75)
    ax_foot.text(50, 79, f'{cur} / 360 期  {pct*100:.0f}%',
                 fontsize=9, color=TEXT_WHITE, ha='center', va='center', zorder=7)

    # 累计数字
    cei = CUM_EI[cur - 1] / 10000
    cep = CUM_EP[cur - 1] / 10000
    gap = cei - cep

    for lbl, val, color, cx in [
        ('等额本息利息', f'{cei:.1f}万', EI_BLUE,   22),
        ('等额本金利息', f'{cep:.1f}万', EP_ORANGE, 50),
        ('当前差额',    f'{gap:.1f}万', GAP_PINK,  78),
    ]:
        ax_foot.text(cx, 57, lbl, fontsize=8,  color=TEXT_GRAY,  ha='center', va='center', zorder=6)
        ax_foot.text(cx, 42, val, fontsize=14, color=color, ha='center', va='center',
                     fontweight='bold', zorder=6)

    # 底部说明
    ax_foot.text(50, 18, '🔵 等额本息  🟠 等额本金  🟢 本金  🔴 利息',
                 fontsize=9, color=TEXT_DIM, ha='center', va='center', zorder=6)

# ============================================================
# 场景3：结论  (25–30s)
# ============================================================
def draw_conclusion(frame):
    t    = (frame - F_ANIM_END) / (F_CONC_END - F_ANIM_END)   # 0→1
    a0   = ease_out_cubic(clamp(t * 3))
    a1   = ease_out_cubic(clamp(t * 3 - 0.5))
    a2   = ease_out_cubic(clamp(t * 3 - 1.2))
    a3   = ease_out_cubic(clamp(t * 4 - 2.5))

    draw_title()

    # ── info：完整30年折线 ──
    clear_ax(ax_info)
    ax_info.set_xlim(0, 100)
    ax_info.set_ylim(0, 100)
    ax_info.text(50, 50, '30年贷款总利息对比',
                 fontsize=13, color=TEXT_WHITE, ha='center', va='center',
                 fontweight='bold', alpha=a0, zorder=6)

    # ── top：完整折线图 ──
    ax_top.clear()
    ax_top.set_facecolor(BG_MID)
    months = list(range(1, TOTAL_MONTHS + 1))
    ei_c   = [CUM_EI[i] / 10000 for i in range(TOTAL_MONTHS)]
    ep_c   = [CUM_EP[i] / 10000 for i in range(TOTAL_MONTHS)]
    max_y  = FINAL_EI / 10000 * 1.12
    ax_top.set_xlim(0, TOTAL_MONTHS + 12)
    ax_top.set_ylim(0, max_y)

    ax_top.fill_between(months, ei_c, ep_c, alpha=0.25 * a1, color=GAP_PINK, zorder=1)
    glow_line(ax_top, months, ep_c, EP_ORANGE, lw=3)
    glow_line(ax_top, months, ei_c, EI_BLUE,   lw=3)

    for m, label in KEY_MILESTONES.items():
        ax_top.axvline(x=m, color=TEXT_DIM, linewidth=0.8, alpha=0.4, linestyle=':')
        ax_top.text(m, max_y * 0.96, label, fontsize=8, color=TEXT_DIM, ha='center', va='top')

    ax_top.text(300, ei_c[-1] - 4, f'等额本息\n{FINAL_EI/10000:.1f}万',
                fontsize=10, color=EI_BLUE, ha='center', fontweight='bold',
                alpha=a1, zorder=7)
    ax_top.text(300, ep_c[-1] - 6, f'等额本金\n{FINAL_EP/10000:.1f}万',
                fontsize=10, color=EP_ORANGE, ha='center', fontweight='bold',
                alpha=a1, zorder=7)

    year_ticks  = [60, 120, 180, 240, 300, 360]
    year_labels = ['5年', '10年', '15年', '20年', '25年', '30年']
    ax_top.set_xticks(year_ticks)
    ax_top.set_xticklabels(year_labels, fontsize=8, color=TEXT_GRAY)
    ax_top.tick_params(colors=TEXT_GRAY, labelsize=7)
    ax_top.set_ylabel('累计利息（万元）', fontsize=9, color=TEXT_GRAY)
    for sp in ax_top.spines.values():
        sp.set_edgecolor('#2D3A60')
    ax_top.grid(True, alpha=0.12, linestyle='--', color=TEXT_GRAY)

    # ── bottom：结论卡片 ──
    clear_ax(ax_bottom)
    ax_bottom.set_xlim(0, 100)
    ax_bottom.set_ylim(0, 100)

    # 名言
    ax_bottom.text(50, 93, '前期多还本金，后期少付利息',
                   fontsize=15, fontweight='bold', color=ACCENT_GOLD,
                   ha='center', va='center', alpha=a0, zorder=6)
    ax_bottom.text(50, 84, '时间是利息的朋友，也是你的敌人',
                   fontsize=11, color=TEXT_GRAY, ha='center', va='center',
                   style='italic', alpha=a0, zorder=6)

    # 等额本息卡
    card_rect(ax_bottom, 4, 63, 92, 16, EI_BLUE, BG_CARD2, alpha=a1 * 0.95)
    ax_bottom.text(14, 74, '等额本息', fontsize=13, color=EI_BLUE,
                   fontweight='bold', va='center', alpha=a1, zorder=7)
    ax_bottom.text(90, 74, f'30年总利息  {FINAL_EI/10000:.1f} 万元',
                   fontsize=13, color=EI_BLUE, ha='right', va='center',
                   fontweight='bold', alpha=a1, zorder=7)

    # 等额本金卡
    card_rect(ax_bottom, 4, 44, 92, 16, EP_ORANGE, BG_CARD2, alpha=a2 * 0.95)
    ax_bottom.text(14, 55, '等额本金', fontsize=13, color=EP_ORANGE,
                   fontweight='bold', va='center', alpha=a2, zorder=7)
    ax_bottom.text(90, 55, f'30年总利息  {FINAL_EP/10000:.1f} 万元',
                   fontsize=13, color=EP_ORANGE, ha='right', va='center',
                   fontweight='bold', alpha=a2, zorder=7)

    # 节省大字卡
    card_rect(ax_bottom, 4, 20, 92, 20, GAP_PINK, BG_DARK, alpha=a3 * 0.3, lw=2.5)
    ax_bottom.text(50, 33, f'💰  节省  {FINAL_GAP/10000:.1f} 万元',
                   fontsize=18, fontweight='bold', color=GAP_PINK,
                   ha='center', va='center', alpha=a3, zorder=7)
    ax_bottom.text(50, 24, '≈ 一辆中配家用轿车！',
                   fontsize=12, color=TEXT_GRAY, ha='center', va='center',
                   alpha=a3, zorder=7)

    # ── foot：月供对比 ──
    clear_ax(ax_foot)
    ax_foot.set_xlim(0, 100)
    ax_foot.set_ylim(0, 100)

    ax_foot.text(50, 88, '月供参考（第1期）',
                 fontsize=11, color=TEXT_GRAY, ha='center', alpha=a1, zorder=6)
    ax_foot.text(26, 70, f'等额本息\n{EI_MONTHLY:.0f}元/月（固定不变）',
                 fontsize=10, color=EI_BLUE, ha='center', va='center',
                 alpha=a1, zorder=6, linespacing=1.6)
    ax_foot.text(74, 70, f'等额本金\n{EP_FIRST_MONTH:.0f}元（首月）\n{EP_LAST_MONTH:.0f}元（末月）',
                 fontsize=10, color=EP_ORANGE, ha='center', va='center',
                 alpha=a1, zorder=6, linespacing=1.6)
    ax_foot.text(50, 35, '选择哪种方式？根据自己的现金流来决定！',
                 fontsize=10, color=ACCENT_GOLD, ha='center', va='center',
                 fontweight='bold', alpha=a2, zorder=6)
    ax_foot.text(50, 18, '资金充裕→等额本金可节省更多利息',
                 fontsize=9, color=TEXT_GRAY, ha='center', va='center',
                 alpha=a2, zorder=6)

# ============================================================
# 动画主函数
# ============================================================
def init():
    for ax in [ax_title, ax_info, ax_top, ax_bottom, ax_foot]:
        ax.clear()
        ax.set_facecolor(BG_DARK)
        ax.axis('off')
    return []

def update(frame):
    if frame < F_INTRO_END:
        draw_intro(frame)
    elif frame < F_ANIM_END:
        draw_main(frame)
    else:
        draw_conclusion(frame)
    return []

# ============================================================
# 渲染输出
# ============================================================
print('\n开始渲染...')
print(f'  分辨率: {int(FIG_W*DPI)} × {int(FIG_H*DPI)}')
print(f'  帧率: {FPS} fps  |  总帧数: {TOTAL_FRAMES}  |  时长: {TOTAL_SECS}s')

ani = FuncAnimation(
    fig, update,
    frames=TOTAL_FRAMES,
    init_func=init,
    blit=False,
    interval=1000 / FPS,
    repeat=False,
)

OUTPUT = Path(
    os.getenv(
        "VIDEO_OUTPUT_FILE",
        str(Path(__file__).resolve().parent / "runtime" / "outputs" / "loan_comparison_flourish.mp4"),
    )
)
OUTPUT.parent.mkdir(parents=True, exist_ok=True)
print(f'  输出: {OUTPUT}')

try:
    writer = FFMpegWriter(
        fps=FPS, bitrate=8000,
        extra_args=[
            '-vcodec', 'libx264',
            '-pix_fmt', 'yuv420p',
            '-preset', 'medium',
            '-crf', '20',
        ],
    )
    ani.save(str(OUTPUT), writer=writer, dpi=DPI,
             savefig_kwargs={'facecolor': BG_DARK, 'edgecolor': 'none'})
    print(f'\n✅  渲染完成！')
    print(f'   文件: {OUTPUT}')
except Exception as exc:
    import traceback
    print(f'\n❌  渲染失败: {exc}')
    traceback.print_exc()
finally:
    plt.close()

print('\n' + '=' * 55)
print('数据汇总')
print('=' * 55)
print(f'等额本息  月供: {EI_MONTHLY:.0f}元  30年总利息: {FINAL_EI/10000:.1f}万元')
print(f'等额本金  首月: {EP_FIRST_MONTH:.0f}元  30年总利息: {FINAL_EP/10000:.1f}万元')
print(f'节省利息: {FINAL_GAP/10000:.1f}万元（选等额本金）')
print('=' * 55)
