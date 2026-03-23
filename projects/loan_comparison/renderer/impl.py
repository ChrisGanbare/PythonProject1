"""
贷款还款方式对比 - 电影级数据可视化动画
等额本息 vs 等额本金 | Flourish风格 | 抖音/B站竖屏9:16
时长: 30秒
"""

import json
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.patheffects as pe
from matplotlib import ticker
from matplotlib.animation import FuncAnimation, FFMpegWriter
from matplotlib.patches import FancyBboxPatch
from matplotlib.lines import Line2D
from matplotlib.gridspec import GridSpec
import warnings
import shutil
import os
import sys
from pathlib import Path

_WORKSPACE_ROOT = Path(__file__).resolve().parents[3]
_PROJECTS_ROOT = Path(__file__).resolve().parents[2]
for _root in [str(_WORKSPACE_ROOT), str(_PROJECTS_ROOT)]:
    if _root not in sys.path:
        sys.path.insert(0, str(_root))

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
from shared.content.scene_pacing import get_scene_pacing_profile
from shared.content.render_timeline import RenderTimeline, TimelineSegment
from shared.platform.presets import build_scene_copy_band_tokens
from shared.visualization.png_frame_cache import (
    PngCachingFFMpegWriter,
    all_frames_cached,
    encode_video_from_png_sequence_ffmpeg,
    frame_png_path,
)
from loan_comparison.renderer.copy_metrics import build_loan_copy_metrics

warnings.filterwarnings('ignore')

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
_DEFAULT_EI_MONTHLY = (
    LOAN_AMOUNT * MONTHLY_RATE * (1 + MONTHLY_RATE) ** TOTAL_MONTHS /
    ((1 + MONTHLY_RATE) ** TOTAL_MONTHS - 1)
)
_DEFAULT_EP_PRINCIPAL = LOAN_AMOUNT / TOTAL_MONTHS
_DEFAULT_FINAL_EI = _DEFAULT_EI_MONTHLY * TOTAL_MONTHS - LOAN_AMOUNT
_DEFAULT_FINAL_EP = LOAN_AMOUNT * MONTHLY_RATE * (TOTAL_MONTHS + 1) / 2
_DEFAULT_EP_FIRST = _DEFAULT_EP_PRINCIPAL + LOAN_AMOUNT * MONTHLY_RATE
_DEFAULT_EP_LAST = _DEFAULT_EP_PRINCIPAL * (1 + MONTHLY_RATE)
COPY_METRICS = build_loan_copy_metrics(
    loan_amount=LOAN_AMOUNT,
    annual_rate=ANNUAL_RATE,
    loan_years=LOAN_YEARS,
    total_months=TOTAL_MONTHS,
    final_equal_interest=_DEFAULT_FINAL_EI,
    final_equal_principal=_DEFAULT_FINAL_EP,
    equal_interest_monthly=_DEFAULT_EI_MONTHLY,
    equal_principal_first_month=_DEFAULT_EP_FIRST,
    equal_principal_last_month=_DEFAULT_EP_LAST,
)

# ============================================================
# 配色方案（深色Flourish风格）
# ============================================================
# [NEW] AI Director Style Injection
THEME_CONFIG = json.loads(os.getenv("VIDEO_THEME_CONFIG", "{}"))
THEME_COLORS = THEME_CONFIG.get("theme_colors", {})
THEME_FONTS = THEME_CONFIG.get("font_config", {})

# Override defaults if theme config is present
BG_DARK    = THEME_COLORS.get("bg_dark", '#0D0D1A')
BG_MID     = '#12122A' # Pending Director support for mid/card tones
BG_CARD    = '#1C1C3A'
BG_CARD2   = '#1A2040'

EI_BLUE        = THEME_COLORS.get("primary_blue", '#4F9EFF')   # 等额本息蓝
EI_BLUE_DARK   = '#1E3A8A'
EP_ORANGE      = THEME_COLORS.get("secondary_orange", '#FF7F35')   # 等额本金橙
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
VIDEO_WIDTH_PX = int(os.getenv("VIDEO_WIDTH", "1080"))
VIDEO_HEIGHT_PX = int(os.getenv("VIDEO_HEIGHT", "1920"))
DPI          = int(os.getenv("VIDEO_DPI", "100"))
FIG_W        = VIDEO_WIDTH_PX / DPI
FIG_H        = VIDEO_HEIGHT_PX / DPI
FPS          = int(os.getenv("VIDEO_FPS", "30"))
TOTAL_SECS   = int(os.getenv("VIDEO_DURATION", "30"))
TOTAL_FRAMES = FPS * TOTAL_SECS
VIDEO_BITRATE = int(os.getenv("VIDEO_BITRATE", "8000"))
VIDEO_PRESET = os.getenv("VIDEO_PRESET", "medium")
VIDEO_CRF = int(os.getenv("VIDEO_CRF", "20"))

RENDER_EXPRESSION = json.loads(os.getenv("VIDEO_RENDER_EXPRESSION", "{}") or "{}")
VIDEO_RENDER_FINGERPRINT = os.getenv("VIDEO_RENDER_FINGERPRINT", "").strip()
VIDEO_FRAME_CACHE_DIR = os.getenv("VIDEO_FRAME_CACHE_DIR", "").strip()
_CURRENT_ANIM_FRAME = 0


def _using_frame_cache() -> bool:
    return bool(VIDEO_FRAME_CACHE_DIR) and not os.getenv("VIDEO_FRAME_CACHE_DISABLE", "").strip()


# 场景边界（帧号）
CONTENT_VARIANT = RENDER_EXPRESSION.get("variant", "standard")
TIMELINE = RENDER_EXPRESSION.get("timeline", {}) or {}
try:
    TIMELINE_MODEL = RenderTimeline.model_validate(TIMELINE) if TIMELINE else None
except Exception:
    TIMELINE_MODEL = None
TIMELINE_PHASES = {
    segment.get("role"): segment
    for segment in TIMELINE.get("phases", [])
    if isinstance(segment, dict) and segment.get("role")
}
CURRENT_PHASE_ROLE = "intro"
CURRENT_SCENE_ID = ""
CURRENT_SCENE_SEGMENT = None
LAST_LOGGED_SCENE_ID = ""

def _resolve_phase_frames() -> tuple[int, int, int]:
    intro_phase = TIMELINE_PHASES.get("intro")
    main_phase = TIMELINE_PHASES.get("main")
    conclusion_phase = TIMELINE_PHASES.get("conclusion")

    if intro_phase and main_phase and conclusion_phase:
        intro_end = int(intro_phase.get("end_frame", 0))
        main_end = int(main_phase.get("end_frame", 0))
        conc_end = int(conclusion_phase.get("end_frame", TOTAL_FRAMES))

        intro_end = max(1, min(intro_end, TOTAL_FRAMES - 2 if TOTAL_FRAMES > 2 else TOTAL_FRAMES))
        main_end = max(intro_end + 1, min(main_end, TOTAL_FRAMES - 1 if TOTAL_FRAMES > 1 else TOTAL_FRAMES))
        conc_end = TOTAL_FRAMES if conc_end <= 0 else min(TOTAL_FRAMES, conc_end)
        return intro_end, main_end, conc_end

    if CONTENT_VARIANT == "short":
        intro_ratio = 0.16
        conclusion_ratio = 0.20
    else:
        intro_ratio = 0.20
        conclusion_ratio = 0.18

    intro_seconds = max(3.0, min(6.0, TOTAL_SECS * intro_ratio))
    conclusion_seconds = max(4.0, min(8.0, TOTAL_SECS * conclusion_ratio))
    intro_end = int(intro_seconds * FPS)
    main_end = max(intro_end + 1, int((TOTAL_SECS - conclusion_seconds) * FPS))
    return intro_end, main_end, TOTAL_FRAMES


def _resolve_phase_role(frame: int) -> str:
    if TIMELINE_MODEL is not None:
        phase = TIMELINE_MODEL.get_phase_for_frame(frame)
        if phase is not None and phase.role:
            return phase.role
    if frame < F_INTRO_END:
        return 'intro'
    if frame < F_ANIM_END:
        return 'main'
    return 'conclusion'


def _resolve_scene_segment(frame: int) -> TimelineSegment | None:
    if TIMELINE_MODEL is None:
        return None
    return TIMELINE_MODEL.get_scene_for_frame(frame)


def _resolve_scene_id(frame: int) -> str:
    scene = _resolve_scene_segment(frame)
    if scene is None:
        return ''
    if getattr(scene, 'scene_id', None):
        return str(scene.scene_id)
    if scene.scene_ids:
        return str(scene.scene_ids[0])
    return ''


def _truncate_copy(text: str | None, limit: int = 40) -> str:
    value = ' '.join(str(text or '').split())
    if len(value) <= limit:
        return value
    return value[: max(0, limit - 1)].rstrip() + '…'


def _scene_identifier(segment: TimelineSegment | None = None) -> str:
    active_segment = segment or CURRENT_SCENE_SEGMENT
    if active_segment is not None:
        if getattr(active_segment, 'scene_id', None):
            return str(active_segment.scene_id)
        if active_segment.scene_ids:
            return str(active_segment.scene_ids[0])
    return CURRENT_SCENE_ID


def _scene_value(field_name: str, segment: TimelineSegment | None = None) -> str:
    active_segment = segment or CURRENT_SCENE_SEGMENT
    if active_segment is None:
        return ''
    value = getattr(active_segment, field_name, None)
    return str(value).strip() if value is not None else ''


def _current_scene_narration(fallback: str = '', limit: int | None = None) -> str:
    value = _scene_value('narration') or fallback
    return _truncate_copy(value, limit) if limit is not None else value


def _current_scene_visual_prompt(fallback: str = '', limit: int | None = None) -> str:
    value = _scene_value('visual_prompt') or fallback
    return _truncate_copy(value, limit) if limit is not None else value


def _current_scene_pacing_token(default: str = 'steady') -> str:
    value = _scene_value('pacing_token').lower()
    return value or default


def _current_scene_mood(default: str = 'neutral') -> str:
    value = _scene_value('mood').lower()
    return value or default


def _scene_progress(frame: int, segment: TimelineSegment | None = None) -> float:
    active_segment = segment or CURRENT_SCENE_SEGMENT
    if active_segment is None:
        return 0.0
    start_frame = int(active_segment.start_frame)
    duration_frames = max(1, int(active_segment.duration_frames or (active_segment.end_frame - start_frame)))
    if duration_frames <= 1:
        return 1.0
    return clamp((frame - start_frame) / max(duration_frames - 1, 1))


def _scene_pacing_profile(segment: TimelineSegment | None = None) -> dict[str, float | str]:
    active_segment = segment or CURRENT_SCENE_SEGMENT
    token = (_scene_value('pacing_token', active_segment).lower() if active_segment is not None else '') or 'steady'
    return get_scene_pacing_profile(token).to_dict()


def _scene_pacing_multiplier(segment: TimelineSegment | None = None) -> float:
    return float(_scene_pacing_profile(segment)['speed'])


def _scene_window_months() -> int:
    base_window = max(12, COMPARISON_WINDOW_MONTHS)
    window_scale = float(_scene_pacing_profile()['window'])
    return max(12, min(TOTAL_MONTHS, int(round(base_window * window_scale))))


def _current_scene_label() -> str:
    aliases = {
        'main': '主对比',
        'intro': '开场钩子',
        'hook': '开场钩子',
        'setup': '建立对比',
        'climax': '差额拉开',
        'conclusion': '结论落点',
        'outro': '结论落点',
        'cta': '结论落点',
    }
    explicit_label = _scene_value('scene_label').lower()
    if explicit_label:
        for token, label in aliases.items():
            if token in explicit_label:
                return label
        return explicit_label.title()
    scene_id = _scene_identifier().lower()
    if not scene_id:
        return ''
    for token, label in aliases.items():
        if token in scene_id:
            return label
    normalized = scene_id.replace('scene_', '').replace('_', ' ').strip()
    return normalized.title()


def _current_scene_copy_band() -> dict[str, str]:
    label = _current_scene_label() or CURRENT_PHASE_ROLE.title()
    headline = _current_scene_narration('', 30) or _current_scene_footer_text() or SUMMARY_TEXT
    detail = _current_scene_visual_prompt('', 44)
    if not detail:
        detail = VISUAL_FOCUS or _current_scene_footer_text() or SUMMARY_TEXT
    return {
        'label': label,
        'headline': headline,
        'detail': detail,
        'token': _current_scene_pacing_token(),
    }


def _resolve_scene_copy_band_tokens() -> dict[str, object]:
    configured = RENDER_EXPRESSION.get('scene_copy_band', {})
    if isinstance(configured, dict) and configured.get('full') and configured.get('compact'):
        return configured

    return build_scene_copy_band_tokens(
        platform=str(SAFE_AREA.get('platform', 'custom')),
        width=VIDEO_WIDTH_PX,
        height=VIDEO_HEIGHT_PX,
        safe_top=int(SAFE_AREA.get('top_px', 0)),
        safe_bottom=int(SAFE_AREA.get('bottom_px', 0)),
        safe_left=int(SAFE_AREA.get('left_px', 0)),
        safe_right=int(SAFE_AREA.get('right_px', 0)),
        orientation=str(SAFE_AREA.get('orientation', '')) or None,
    )


def _scene_copy_band_layout(compact: bool = False) -> dict[str, float | int]:
    mode_key = 'compact' if compact else 'full'
    payload = SCENE_COPY_BAND_TOKENS.get(mode_key, {}) if isinstance(SCENE_COPY_BAND_TOKENS, dict) else {}
    if not isinstance(payload, dict):
        return {}
    return payload


def _scene_copy_band_style(compact: bool = False) -> dict[str, float | str]:
    configured = SCENE_COPY_BAND_TOKENS if isinstance(SCENE_COPY_BAND_TOKENS, dict) else {}
    return {
        'background_color': str(configured.get('background_color', BG_CARD2)),
        'border_color': str(configured.get('border_color', CARD_BORDER_COLOR)),
        'label_color': str(configured.get('label_color', CARD_ACCENT_COLOR)),
        'accent_color': str(configured.get('accent_color', CTA_COLOR)),
        'headline_color': str(configured.get('headline_color', TEXT_WHITE)),
        'detail_color': str(configured.get('detail_color', CARD_BODY_COLOR)),
        'border_width': float(configured.get('border_width', CARD_BORDER_WIDTH)),
        'fill_alpha': float(configured.get('compact_fill_alpha' if compact else 'full_fill_alpha', CARD_FILL_ALPHA)),
    }


def _scene_band_accent_color() -> str:
    style = _scene_copy_band_style(compact=False)
    token = _current_scene_pacing_token()
    if token in {'hook_reveal', 'conclusion_cta'}:
        return str(style['accent_color'])
    if token in {'compare_surge'}:
        return THEME_SECONDARY
    return str(style['label_color'])


def _draw_scene_copy_band(alpha: float = 1.0, compact: bool = False) -> None:
    payload = _current_scene_copy_band()
    clear_ax(ax_info)
    ax_info.set_xlim(0, 100)
    ax_info.set_ylim(0, 100)

    style = _scene_copy_band_style(compact)
    accent_color = _scene_band_accent_color()
    layout = _scene_copy_band_layout(compact)
    card_x = float(layout.get('x', 3 if compact else 1))
    card_y = float(layout.get('y', 66 if compact else 10))
    card_w = float(layout.get('w', 94 if compact else 98))
    card_h = float(layout.get('h', 26 if compact else 80))
    label_y = float(layout.get('label_y', 84 if compact else 74))
    headline_y = float(layout.get('headline_y', 79 if compact else 52))
    detail_y = float(layout.get('detail_y', 72 if compact else 28))
    headline_scale = float(layout.get('headline_scale', 0.98 if compact else 1.0))
    detail_scale = float(layout.get('detail_scale', 0.92 if compact else 1.0))
    label_x = card_x + 3

    card_rect(
        ax_info,
        card_x,
        card_y,
        card_w,
        card_h,
        str(style['border_color']),
        str(style['background_color']),
        alpha=min(1.0, float(style['fill_alpha']) * alpha),
        lw=max(1.0, float(style['border_width'])),
    )

    headline_size = max(9, int((BODY_FONT_SIZE if compact else SUBTITLE_FONT_SIZE) * headline_scale))
    detail_size = max(8, int((CAPTION_FONT_SIZE if compact else BODY_FONT_SIZE) * detail_scale))

    ax_info.text(label_x, label_y, payload['label'],
                 fontsize=max(7, CAPTION_FONT_SIZE - 1), color=accent_color,
                 ha='left', va='center', fontweight=SUBTITLE_FONT_WEIGHT, alpha=alpha, zorder=7)
    ax_info.text(50, headline_y, payload['headline'],
                 fontsize=headline_size, color=str(style['headline_color']),
                 ha='center', va='center', fontweight=SUBTITLE_FONT_WEIGHT, alpha=alpha, zorder=7)
    ax_info.text(50, detail_y, payload['detail'],
                 fontsize=detail_size, color=str(style['detail_color']),
                 ha='center', va='center', alpha=alpha, zorder=7,
                 linespacing=BODY_LINE_HEIGHT)


def _print_scene_schedule_logs() -> None:
    if TIMELINE_MODEL is None:
        return
    print('\n场景调度日志')
    print('-' * 55)
    for line in TIMELINE_MODEL.scene_schedule_log_lines():
        print(line)
    print('-' * 55)


def _log_scene_transition(frame: int) -> None:
    scene_id = _scene_identifier()
    if not scene_id:
        return
    scene_label = _current_scene_label()
    token = _current_scene_pacing_token()
    narration = _current_scene_narration('', 24)
    print(
        'scene_transition'
        f' :: frame={frame}'
        f' :: phase={CURRENT_PHASE_ROLE}'
        f' :: scene_id={scene_id}'
        f' :: label={scene_label}'
        f' :: token={token}'
        f' :: narration={narration}'
    )


def _current_scene_matches(*tokens: str) -> bool:
    normalized = _scene_identifier().lower()
    return bool(normalized) and any(token in normalized for token in tokens)


def _current_scene_footer_text() -> str:
    scene_copy = _current_scene_narration('', 26) or _current_scene_visual_prompt('', 26)
    if scene_copy:
        return scene_copy
    if _current_scene_matches('hook', 'intro'):
        return HOOK_TEXT
    if _current_scene_matches('setup'):
        return SUMMARY_TEXT
    if _current_scene_matches('climax'):
        return ACCENT_LABEL
    if _current_scene_matches('conclusion', 'ending', 'outro', 'cta'):
        return CONCLUSION_BODY
    return ''


def _current_scene_chart_title(default_title: str) -> str:
    scene_focus = _current_scene_visual_prompt('', 14) or _current_scene_narration('', 14)
    if scene_focus:
        return f'{default_title} · {scene_focus}'
    if _current_scene_matches('setup'):
        return f'{default_title} · 建立对比基线'
    if _current_scene_matches('climax'):
        return f'{default_title} · 差额拉开'
    return default_title


def _resolve_current_month(frame: int) -> int:
    segment = CURRENT_SCENE_SEGMENT
    if segment is not None and segment.role == 'main':
        profile = _scene_pacing_profile(segment)
        progress = ease_in_out(clamp(_scene_progress(frame, segment) * float(profile['speed'])))
        scene_id = _scene_identifier(segment).lower()
        pivot_month = max(24, min(TOTAL_MONTHS, _scene_window_months()))
        token = str(profile['token'])
        if token == 'compare_build' or 'setup' in scene_id:
            start_month, end_month = 1, pivot_month
        elif token == 'compare_surge' or 'climax' in scene_id:
            start_month, end_month = min(TOTAL_MONTHS, pivot_month), TOTAL_MONTHS
        else:
            start_month, end_month = 1, TOTAL_MONTHS
        if end_month <= start_month:
            end_month = min(TOTAL_MONTHS, start_month + 1)
        return max(1, min(TOTAL_MONTHS, int(round(start_month + (end_month - start_month) * progress))))

    t = (frame - F_INTRO_END) / max(F_ANIM_END - F_INTRO_END, 1)
    if t < 0.10:
        cur = max(1, int(ease_in_out(t / 0.10) * 12))
    elif t < 0.35:
        cur = int(12 + ease_in_out((t - 0.10) / 0.25) * 48)
    else:
        cur = int(60 + ease_in_out((t - 0.35) / 0.65) * 300)
    return min(cur, TOTAL_MONTHS)

F_INTRO_END, F_ANIM_END, F_CONC_END = _resolve_phase_frames()

TITLE_TEXT = RENDER_EXPRESSION.get("title_text", "等额本息 vs 等额本金")
HOOK_TEXT = RENDER_EXPRESSION.get("hook_text", str(COPY_METRICS["hook_text"]))
SUMMARY_TEXT = RENDER_EXPRESSION.get("summary_text", str(COPY_METRICS["summary_text"]))
CONCLUSION_TITLE = RENDER_EXPRESSION.get("conclusion_title", str(COPY_METRICS["conclusion_title"]))
CONCLUSION_BODY = RENDER_EXPRESSION.get("conclusion_body", str(COPY_METRICS["conclusion_body"]))
ACCENT_LABEL = RENDER_EXPRESSION.get("accent_label", str(COPY_METRICS["accent_label"]))
THEME = RENDER_EXPRESSION.get("theme", {})
TYPOGRAPHY = RENDER_EXPRESSION.get("typography", {})
CARD_STYLE = RENDER_EXPRESSION.get("card", {})
LAYOUT_HINTS = RENDER_EXPRESSION.get("layout", {})
SCENE_BEHAVIOR = RENDER_EXPRESSION.get("scene_behavior", {})
SAFE_AREA = RENDER_EXPRESSION.get("safe_area", {})
VISUAL_FOCUS = RENDER_EXPRESSION.get("visual_focus", "")
SCENE_COPY_BAND_TOKENS = _resolve_scene_copy_band_tokens()
if THEME_FONTS:
    TYPOGRAPHY = {
        **TYPOGRAPHY,
        "font_family": THEME_FONTS.get("title") or TYPOGRAPHY.get("font_family") or "Microsoft YaHei",
        "numeric_font_family": THEME_FONTS.get("body") or TYPOGRAPHY.get("numeric_font_family") or "Arial",
    }
RENDERER_THEME = resolve_renderer_theme_card(
    THEME,
    CARD_STYLE,
    {
        "accent_color": ACCENT_GOLD,
        "secondary_color": GAP_PINK,
        "background_color": BG_DARK,
        "panel_color": BG_MID,
        "panel_alt_color": BG_CARD2,
        "title_color": TEXT_WHITE,
        "muted_text_color": TEXT_GRAY,
        "body_color": TEXT_DIM,
        "card_border_color": "#2D3A60",
        "card_border_width": 1.8,
        "card_boxstyle": "round,pad=0.4",
        "card_fill_alpha": 0.92,
    },
)
THEME_ACCENT = RENDERER_THEME.accent_color
THEME_SECONDARY = RENDERER_THEME.secondary_color
BG_DARK = RENDERER_THEME.background_color
BG_MID = RENDERER_THEME.panel_color
BG_CARD = RENDERER_THEME.card_background_color
BG_CARD2 = RENDERER_THEME.panel_alt_color
TEXT_WHITE = RENDERER_THEME.title_color
TEXT_GRAY = RENDERER_THEME.muted_text_color
TEXT_DIM = RENDERER_THEME.body_color
CTA_COLOR = RENDERER_THEME.cta_color
CARD_BORDER_COLOR = RENDERER_THEME.card_border_color
CARD_BORDER_WIDTH = RENDERER_THEME.card_border_width
CARD_BOXSTYLE = RENDERER_THEME.card_boxstyle
CARD_FILL_ALPHA = RENDERER_THEME.card_fill_alpha
CARD_TITLE_COLOR = RENDERER_THEME.card_title_color
CARD_BODY_COLOR = RENDERER_THEME.card_body_color
CARD_ACCENT_COLOR = RENDERER_THEME.card_accent_color
CARD_BADGE_BG = RENDERER_THEME.card_badge_background_color
SCALES = resolve_scale_tokens(TYPOGRAPHY)
TITLE_SCALE = SCALES["title_scale"]
SUMMARY_SCALE = SCALES["summary_scale"]
ACCENT_SCALE = SCALES["accent_scale"]
CONCLUSION_SCALE = SCALES["conclusion_scale"]
FONT_NAME = initialize_renderer_typography(TYPOGRAPHY)
FONT_SIZES = resolve_font_sizes(
    TYPOGRAPHY,
    {
        "title": FontSizeSpec("title_size", 0.36, 18),
        "subtitle": FontSizeSpec("subtitle_size", 0.44, 12),
        "body": FontSizeSpec("body_size", 0.55, 10),
        "caption": FontSizeSpec("caption_size", 0.56, 8),
        "conclusion_title": FontSizeSpec("subtitle_size", 0.58, 16, scale_key="conclusion_scale"),
        "conclusion_body": FontSizeSpec("body_size", 0.60, 11),
    },
    scales=SCALES,
)
TITLE_FONT_SIZE = FONT_SIZES["title"]
SUBTITLE_FONT_SIZE = FONT_SIZES["subtitle"]
BODY_FONT_SIZE = FONT_SIZES["body"]
CAPTION_FONT_SIZE = FONT_SIZES["caption"]
CONCLUSION_TITLE_SIZE = FONT_SIZES["conclusion_title"]
CONCLUSION_BODY_SIZE = FONT_SIZES["conclusion_body"]
WEIGHTS = resolve_font_weights(TYPOGRAPHY)
TITLE_FONT_WEIGHT = WEIGHTS["title_weight"]
SUBTITLE_FONT_WEIGHT = WEIGHTS["subtitle_weight"]
BODY_FONT_WEIGHT = WEIGHTS["body_weight"]
CAPTION_FONT_WEIGHT = WEIGHTS["caption_weight"]
LINE_HEIGHTS = resolve_line_heights(TYPOGRAPHY, {"title_line_height": 1.2, "body_line_height": 1.5, "caption_line_height": 1.28})
TITLE_LINE_HEIGHT = LINE_HEIGHTS["title_line_height"]
BODY_LINE_HEIGHT = LINE_HEIGHTS["body_line_height"]
CAPTION_LINE_HEIGHT = LINE_HEIGHTS["caption_line_height"]
LEGEND_FONT_SIZE = max(8, CAPTION_FONT_SIZE - 1)
AXIS_LABEL_FONT_SIZE = max(9, CAPTION_FONT_SIZE)
HOOK_LAYOUT = LAYOUT_HINTS.get("hook_layout", "stacked")
CHART_FOCUS = LAYOUT_HINTS.get("chart_focus", "balanced")
CONCLUSION_LAYOUT = LAYOUT_HINTS.get("conclusion_layout", "summary-band")
HOOK_MODE = SCENE_BEHAVIOR.get("hook_mode", "context-lead")
HOOK_SUPPORT_DENSITY = SCENE_BEHAVIOR.get("hook_support_density", "balanced")
SETUP_DENSITY = SCENE_BEHAVIOR.get("setup_density", "balanced")
COMPARISON_WINDOW_MONTHS = int(SCENE_BEHAVIOR.get("comparison_window_months", 60))
SHOW_REFERENCE_GUIDES = bool(SCENE_BEHAVIOR.get("show_reference_guides", True))
CONCLUSION_MODE = SCENE_BEHAVIOR.get("conclusion_mode", "summary-band")
CONCLUSION_REVEAL_ORDER = list(SCENE_BEHAVIOR.get("conclusion_reveal_order", ["headline", "body", "badge", "footer"]))
CONCLUSION_CARD_SCALE = float(SCENE_BEHAVIOR.get("conclusion_card_scale", 1.0))
FIGURE_BOUNDS = resolve_figure_bounds(
    SAFE_AREA,
    FigureBoundsConfig(
        default_left=0.06,
        default_right=0.94,
        default_top=0.97,
        default_bottom=0.03,
        left_scale=0.7,
        right_scale=0.7,
        top_scale=0.38,
        bottom_scale=0.42,
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
FIG_LEFT, FIG_RIGHT, FIG_TOP, FIG_BOTTOM = (
    FIGURE_BOUNDS.left,
    FIGURE_BOUNDS.right,
    FIGURE_BOUNDS.top,
    FIGURE_BOUNDS.bottom,
)

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
if VIDEO_RENDER_FINGERPRINT:
    print(f"  reproducibility fingerprint: {VIDEO_RENDER_FINGERPRINT[:24]}…")
if VIDEO_FRAME_CACHE_DIR:
    print(f"  frame cache dir (PNG resume / skip): {VIDEO_FRAME_CACHE_DIR}")
LOAN_DATA, EI_MONTHLY, EP_FIXED_PRIN = calculate_loan_data()

CUM_EI   = [d['cum_ei']  for d in LOAN_DATA]
CUM_EP   = [d['cum_ep']  for d in LOAN_DATA]
GAP_LIST = [d['gap']     for d in LOAN_DATA]
FINAL_EI  = CUM_EI[-1]
FINAL_EP  = CUM_EP[-1]
FINAL_GAP = FINAL_EI - FINAL_EP
EP_FIRST_MONTH = LOAN_DATA[0]['ep_total']
EP_LAST_MONTH  = LOAN_DATA[-1]['ep_total']
COPY_METRICS = build_loan_copy_metrics(
    loan_amount=LOAN_AMOUNT,
    annual_rate=ANNUAL_RATE,
    loan_years=LOAN_YEARS,
    total_months=TOTAL_MONTHS,
    final_equal_interest=FINAL_EI,
    final_equal_principal=FINAL_EP,
    equal_interest_monthly=EI_MONTHLY,
    equal_principal_first_month=EP_FIRST_MONTH,
    equal_principal_last_month=EP_LAST_MONTH,
)

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

if CHART_FOCUS == 'single-compare':
    chart_height_ratios = [0.9, 0.75, 3.3, 2.7, 1.35]
elif CHART_FOCUS == 'trend-gap':
    chart_height_ratios = [0.9, 0.75, 2.7, 3.3, 1.35]
else:
    chart_height_ratios = [0.9, 0.75, 3.0, 3.0, 1.35]

if SETUP_DENSITY == 'full-context':
    chart_height_ratios[2] += 0.2
    chart_height_ratios[3] += 0.2
if CONCLUSION_MODE == 'cta-spotlight':
    chart_height_ratios[3] += 0.15
    chart_height_ratios[4] += 0.05

gs = GridSpec(
    5, 1, figure=fig,
    height_ratios=chart_height_ratios,
    hspace=0.08,
    left=FIG_LEFT, right=FIG_RIGHT,
    top=FIG_TOP, bottom=FIG_BOTTOM,
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

def card_rect(ax, x, y, w, h, edge_color, face_color=BG_CARD, alpha=0.92, lw=None):
    resolved_lw = CARD_BORDER_WIDTH if lw is None else lw
    r = FancyBboxPatch((x, y), w, h, boxstyle=CARD_BOXSTYLE,
                       facecolor=face_color, edgecolor=edge_color,
                       linewidth=resolved_lw, alpha=min(alpha, CARD_FILL_ALPHA), zorder=5)
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

    card_rect(ax_title, 1, 10, 98, 80, CARD_BORDER_COLOR, BG_CARD, alpha=alpha * 0.9)

    ax_title.text(50, 82, TITLE_TEXT,
                  fontsize=max(18, int(TITLE_FONT_SIZE * TITLE_SCALE)), fontweight=TITLE_FONT_WEIGHT, color=TEXT_WHITE,
                  ha='center', va='center', alpha=alpha, zorder=6)
    ax_title.text(50, 69, HOOK_TEXT,
                  fontsize=max(9, BODY_FONT_SIZE), color=CARD_BODY_COLOR,
                  ha='center', va='center', alpha=alpha * 0.95, zorder=6)

    ax_title.text(28, 54, '等额本息', fontsize=SUBTITLE_FONT_SIZE, fontweight=SUBTITLE_FONT_WEIGHT,
                  color=EI_BLUE, ha='center', va='center', alpha=alpha, zorder=6)
    ax_title.text(50, 54, 'vs', fontsize=CAPTION_FONT_SIZE + 3, color=TEXT_GRAY,
                  ha='center', va='center', alpha=alpha, zorder=6)
    ax_title.text(72, 54, '等额本金', fontsize=SUBTITLE_FONT_SIZE, fontweight=SUBTITLE_FONT_WEIGHT,
                  color=EP_ORANGE, ha='center', va='center', alpha=alpha, zorder=6)

    ax_title.plot([5, 95], [38, 38], color='#334155', linewidth=0.8, alpha=0.5 * alpha)

    for label, value, cx in [
        ('贷款', str(COPY_METRICS['loan_amount_short']), 22),
        ('利率', f"{COPY_METRICS['annual_rate_label']}/年", 50),
        ('期限', f"{LOAN_YEARS}年", 78),
    ]:
        ax_title.text(cx, 32, label, fontsize=CAPTION_FONT_SIZE, color=TEXT_GRAY,
                      ha='center', va='center', alpha=alpha, zorder=6)
        ax_title.text(cx, 20, value, fontsize=BODY_FONT_SIZE + 1, fontweight=SUBTITLE_FONT_WEIGHT,
                        color=THEME_ACCENT, ha='center', va='center', alpha=alpha, zorder=6)

# ============================================================
# 场景1：开场介绍  (0–5s)
# ============================================================
def draw_intro(frame):
    t = frame / max(F_INTRO_END, 1)   # 0→1
    scene_profile = _scene_pacing_profile()
    scene_speed = float(scene_profile['speed'])
    scene_narration = _current_scene_narration(HOOK_TEXT, 30)
    scene_prompt = _current_scene_visual_prompt(SUMMARY_TEXT, 42)

    draw_title(alpha=ease_out_cubic(clamp(t * 4)))

    _draw_scene_copy_band(alpha=ease_out_cubic(clamp(t * 4 * float(scene_profile['reveal']))), compact=False)
    clear_ax(ax_foot)

    # ── 阶段A (t<0.35)：贷款参数卡片 ──
    if t < 0.35:
        t_a = t / 0.35
        clear_ax(ax_top)
        ax_top.set_xlim(0, 100)
        ax_top.set_ylim(0, 100)

        intro_title = scene_narration if HOOK_MODE == 'hero-spotlight' else (scene_prompt or ('您的贷款条件' if HOOK_LAYOUT != 'hero' else scene_narration))
        intro_font = max(17, int(((TITLE_FONT_SIZE + 1) if HOOK_MODE == 'hero-spotlight' else (TITLE_FONT_SIZE - 1 if HOOK_LAYOUT == 'hero' else TITLE_FONT_SIZE)) * TITLE_SCALE))
        intro_y = 88 if HOOK_MODE == 'hero-spotlight' else 90
        ax_top.text(50, intro_y, intro_title, fontsize=intro_font, fontweight=TITLE_FONT_WEIGHT,
                    color=TEXT_WHITE, ha='center', va='center',
                    alpha=ease_out_cubic(clamp(t_a * 3 * scene_speed)), zorder=6)

        params = [
            ('💰  贷款金额', str(COPY_METRICS['loan_amount_full']), EI_BLUE, 70),
            ('📈  年利率', str(COPY_METRICS['annual_rate_label']), ACCENT_GOLD, 50),
            ('📅  贷款期限', str(COPY_METRICS['term_label']), EP_ORANGE, 30),
        ]
        if HOOK_SUPPORT_DENSITY == 'sparse':
            params = [params[0], params[-1]]
        elif HOOK_SUPPORT_DENSITY == 'balanced' and HOOK_MODE == 'hero-spotlight':
            params = [params[0], params[1]]
        for i, (lbl, val, color, cy) in enumerate(params):
            a = ease_out_cubic(clamp(t_a * 2.5 - i * 0.25))
            card_rect(ax_top, 8, cy - 8, 84, 14, color, BG_CARD, alpha=a * 0.9)
            ax_top.text(16, cy, lbl, fontsize=SUBTITLE_FONT_SIZE - 1, color=TEXT_GRAY,
                        ha='left', va='center', alpha=a, zorder=6)
            ax_top.text(90, cy, val, fontsize=SUBTITLE_FONT_SIZE + 1, fontweight=SUBTITLE_FONT_WEIGHT,
                        color=color, ha='right', va='center', alpha=a, zorder=6)

        clear_ax(ax_bottom)
        ax_bottom.set_xlim(0, 100)
        ax_bottom.set_ylim(0, 100)
        intro_message = scene_prompt if HOOK_MODE == 'hero-spotlight' else (scene_prompt or (f'接下来：\n两种还款方式 {LOAN_YEARS}年的利息差距\n究竟有多大？' if HOOK_LAYOUT != 'hero' else scene_narration))
        ax_bottom.text(50, 50,
                       intro_message,
                       fontsize=max(14, int(((BODY_FONT_SIZE + 6) if HOOK_MODE == 'hero-spotlight' else (BODY_FONT_SIZE + 4)) * SUMMARY_SCALE)), color=CARD_BODY_COLOR, ha='center', va='center',
                       alpha=ease_out_cubic(clamp(t_a * 2 * scene_speed - 0.8)), linespacing=BODY_LINE_HEIGHT, zorder=6)

    # ── 阶段B (0.35–0.70)：两条路径分叉 ──
    elif t < 0.70:
        t_b = (t - 0.35) / 0.35

        clear_ax(ax_top)
        ax_top.set_xlim(0, 100)
        ax_top.set_ylim(0, 100)

        alpha0 = ease_out_cubic(clamp(t_b * 3))
        setup_title = _current_scene_narration(SUMMARY_TEXT if HOOK_MODE == 'hero-spotlight' else '两种路径，同一终点', 30)
        ax_top.text(50, 92, setup_title, fontsize=max(16, int(TITLE_FONT_SIZE * TITLE_SCALE)), fontweight=TITLE_FONT_WEIGHT,
                    color=TEXT_WHITE, ha='center', alpha=alpha0, zorder=6)
        setup_subtitle = _current_scene_visual_prompt(
            '全周期关键路径一眼看清' if SETUP_DENSITY == 'full-context' else (str(COPY_METRICS['footer_question']) if HOOK_LAYOUT != 'hero' else scene_narration),
            40,
        )
        ax_top.text(50, 84, setup_subtitle,
                    fontsize=max(10, int((BODY_FONT_SIZE + 1) * SUMMARY_SCALE)), color=TEXT_GRAY, ha='center', alpha=alpha0, zorder=6)

        # 起点
        sx, sy = 12, 55
        ax_top.plot(sx, sy, 'o', color=CTA_COLOR, markersize=18, zorder=7)
        ax_top.text(sx, 44, f"起点\n{COPY_METRICS['start_point_label']}", fontsize=BODY_FONT_SIZE, color=CTA_COLOR,
                    ha='center', va='top', fontweight=SUBTITLE_FONT_WEIGHT, alpha=alpha0, zorder=6,
                    linespacing=CAPTION_LINE_HEIGHT)

        branch_start = max(0.06, (0.10 if HOOK_MODE == 'hero-spotlight' else 0.2) / max(0.80, scene_speed * float(scene_profile['branch_delay'])))
        if t_b > branch_start:
            pt = ease_in_out(clamp((t_b - branch_start) / (1 - branch_start)))

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
                ax_top.text(ex + 19, ey + 13, '等额本息', fontsize=SUBTITLE_FONT_SIZE - 1,
                            color=TEXT_WHITE, ha='center', fontweight=SUBTITLE_FONT_WEIGHT, alpha=la, zorder=7)
                ax_top.text(ex + 19, ey + 5,  f'月供固定 {EI_MONTHLY:.0f}元',
                            fontsize=CAPTION_FONT_SIZE + 1, color=EI_BLUE, ha='center', alpha=la, zorder=7)

                card_rect(ax_top, ox - 2, oy - 18, 42, 16, EP_ORANGE, EP_ORANGE_DARK, alpha=la * 0.92)
                ax_top.text(ox + 19, oy - 7,  '等额本金', fontsize=SUBTITLE_FONT_SIZE - 1,
                            color=TEXT_WHITE, ha='center', fontweight=SUBTITLE_FONT_WEIGHT, alpha=la, zorder=7)
                ax_top.text(ox + 19, oy - 15, f'首月 {EP_FIRST_MONTH:.0f}元',
                            fontsize=CAPTION_FONT_SIZE + 1, color=EP_ORANGE, ha='center', alpha=la, zorder=7)

        clear_ax(ax_bottom)
        ax_bottom.set_xlim(0, 100)
        ax_bottom.set_ylim(0, 100)
        ta2 = ease_out_cubic(clamp((t_b - 0.5) / 0.5))
        ax_bottom.text(50, 55, '■ 绿色=本金  ■ 红色=利息',
                       fontsize=SUBTITLE_FONT_SIZE - 1, color=TEXT_GRAY, ha='center', va='center', alpha=ta2, zorder=6)
        ax_bottom.text(50, 40, '早期利息占大头？\n看下面的动画！',
                       fontsize=TITLE_FONT_SIZE - 2, fontweight=TITLE_FONT_WEIGHT, color=CTA_COLOR, ha='center', va='center',
                       alpha=ta2, linespacing=TITLE_LINE_HEIGHT, zorder=6)

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
    t = (frame - F_INTRO_END) / max(F_ANIM_END - F_INTRO_END, 1)   # 0→1
    cur = _resolve_current_month(frame)

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

    headline = _current_scene_narration(SUMMARY_TEXT, 24)
    ax_info.text(50, 90, headline, fontsize=max(11, BODY_FONT_SIZE + 1), fontweight=SUBTITLE_FONT_WEIGHT,
                 color=TEXT_WHITE, ha='center', va='center', zorder=6)
    ax_info.text(50, 80, yr_str, fontsize=SUBTITLE_FONT_SIZE + 1, fontweight=SUBTITLE_FONT_WEIGHT,
                 color=CTA_COLOR, ha='center', va='center', zorder=6)

    card_rect(ax_info, 1, 8, 47, 58, EI_BLUE)
    ax_info.text(25, 58, '等额本息', fontsize=BODY_FONT_SIZE + 1, color=EI_BLUE,
                 ha='center', fontweight=SUBTITLE_FONT_WEIGHT, zorder=6)
    ax_info.text(25, 43, f'{d["ei_total"]:.0f}元', fontsize=SUBTITLE_FONT_SIZE + 2,
                 color=TEXT_WHITE, ha='center', fontweight=SUBTITLE_FONT_WEIGHT, zorder=6)
    ax_info.text(25, 29, f'本金 {d["ei_principal"]:.0f}',
                 fontsize=CAPTION_FONT_SIZE + 1, color=PRINCIPAL_GREEN, ha='center', zorder=6)
    ax_info.text(25, 19, f'利息 {d["ei_interest"]:.0f}',
                 fontsize=CAPTION_FONT_SIZE + 1, color=INTEREST_RED, ha='center', zorder=6)
    pct = d['ei_interest'] / d['ei_total'] * 100
    ax_info.text(25, 10, f'利息占比 {pct:.0f}%',
                 fontsize=CAPTION_FONT_SIZE, color=TEXT_GRAY, ha='center', zorder=6)

    card_rect(ax_info, 52, 8, 47, 58, EP_ORANGE)
    ax_info.text(75, 58, '等额本金', fontsize=BODY_FONT_SIZE + 1, color=EP_ORANGE,
                 ha='center', fontweight=SUBTITLE_FONT_WEIGHT, zorder=6)
    ax_info.text(75, 43, f'{d["ep_total"]:.0f}元', fontsize=SUBTITLE_FONT_SIZE + 2,
                 color=TEXT_WHITE, ha='center', fontweight=SUBTITLE_FONT_WEIGHT, zorder=6)
    ax_info.text(75, 29, f'本金 {d["ep_principal"]:.0f}',
                 fontsize=CAPTION_FONT_SIZE + 1, color=PRINCIPAL_GREEN, ha='center', zorder=6)
    ax_info.text(75, 19, f'利息 {d["ep_interest"]:.0f}',
                 fontsize=CAPTION_FONT_SIZE + 1, color=INTEREST_RED, ha='center', zorder=6)
    pct2 = d['ep_interest'] / d['ep_total'] * 100
    ax_info.text(75, 10, f'利息占比 {pct2:.0f}%',
                 fontsize=CAPTION_FONT_SIZE, color=TEXT_GRAY, ha='center', zorder=6)

def _draw_bar_chart(cur):
    """月供堆叠柱状图（滑动窗口显示最近≤60个月）"""
    ax_top.clear()
    ax_top.set_facecolor(BG_MID)

    # 窗口：根据场景行为展示最近若干个月；移动端限制柱数，避免信息糊成一片
    win_end = cur
    win_start = max(1, cur - (_scene_window_months() - 1))
    months = list(range(win_start, win_end + 1))
    max_display_points = 24
    if len(months) > max_display_points:
        stride = max(1, int(round(len(months) / max_display_points)))
        sampled = months[::stride]
        if sampled[-1] != months[-1]:
            sampled.append(months[-1])
        months = sampled
    n = len(months)

    max_y = LOAN_DATA[0]['ep_total'] * 1.18
    ax_top.set_xlim(0, n + 1)
    ax_top.set_ylim(0, max_y)

    bw = 0.56 if n <= 18 else 0.44

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
                   alpha=0.55 if SETUP_DENSITY != 'focused' else 0.70, linestyle='--', zorder=2)

    # 标题
    ax_top.text(n / 2 + 0.5, max_y * 0.97,
                f'月供结构（第{win_start}–{win_end}期）',
                fontsize=SUBTITLE_FONT_SIZE, fontweight=SUBTITLE_FONT_WEIGHT, color=TEXT_WHITE,
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
                  fontsize=LEGEND_FONT_SIZE, facecolor=BG_CARD, edgecolor=CARD_BORDER_COLOR,
                  labelcolor=TEXT_WHITE, framealpha=0.9)

    # 坐标轴
    ax_top.set_ylabel('月供（元）', fontsize=AXIS_LABEL_FONT_SIZE, color=TEXT_GRAY)
    ax_top.tick_params(colors=TEXT_GRAY, labelsize=CAPTION_FONT_SIZE - 1)
    ax_top.yaxis.set_major_formatter(
        ticker.FuncFormatter(lambda x, _: f'{x/1000:.0f}k'))
    if SETUP_DENSITY == 'full-context' and n >= 12:
        tick_positions = [idx + 1 for idx, m in enumerate(months) if m % 12 == 0]
        tick_labels = [f'{m//12}年' for m in months if m % 12 == 0]
        ax_top.set_xticks(tick_positions)
        ax_top.set_xticklabels(tick_labels, fontsize=CAPTION_FONT_SIZE - 1, color=TEXT_GRAY)
    else:
        ax_top.set_xticks([])
    for sp in ax_top.spines.values():
        sp.set_edgecolor(CARD_BORDER_COLOR)
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
                           fontsize=BODY_FONT_SIZE, color=THEME_SECONDARY, ha='center', va='center',
                           fontweight=SUBTITLE_FONT_WEIGHT, zorder=8,
                           bbox=dict(boxstyle='round,pad=0.35', facecolor=BG_DARK,
                                     edgecolor=THEME_SECONDARY, alpha=0.85, linewidth=1.5))

        # 关键节点竖线 + 标注
        if SHOW_REFERENCE_GUIDES:
            for m, label in KEY_MILESTONES.items():
                if m <= cur:
                    ax_bottom.axvline(x=m, color=TEXT_DIM, linewidth=0.8,
                                      alpha=0.45, linestyle=':', zorder=2)
                    ax_bottom.text(m, max_y * 0.97, label, fontsize=8,
                                   color=TEXT_DIM, ha='center', va='top')

    # 标题
    ax_bottom.text(TOTAL_MONTHS / 2, max_y * 0.97, _current_scene_chart_title('累计利息走势'),
                   fontsize=SUBTITLE_FONT_SIZE, fontweight=SUBTITLE_FONT_WEIGHT, color=TEXT_WHITE,
                   ha='center', va='top', zorder=6,
                   path_effects=[pe.withStroke(linewidth=2, foreground=BG_DARK)])

    # 图例
    ei_hdl = Line2D([0], [0], color=EI_BLUE,   linewidth=3, label='等额本息')
    ep_hdl = Line2D([0], [0], color=EP_ORANGE, linewidth=3, label='等额本金')
    ax_bottom.legend(handles=[ei_hdl, ep_hdl], loc='upper left',
                     fontsize=BODY_FONT_SIZE, facecolor=BG_CARD, edgecolor=CARD_BORDER_COLOR,
                     labelcolor=TEXT_WHITE, framealpha=0.9)

    # 坐标轴
    ax_bottom.set_ylabel('累计利息（万元）', fontsize=AXIS_LABEL_FONT_SIZE, color=TEXT_GRAY)
    ax_bottom.tick_params(colors=TEXT_GRAY, labelsize=CAPTION_FONT_SIZE - 1)
    year_ticks  = [60, 120, 180, 240, 300, 360]
    year_labels = ['5年', '10年', '15年', '20年', '25年', '30年']
    ax_bottom.set_xticks(year_ticks)
    ax_bottom.set_xticklabels(year_labels, fontsize=CAPTION_FONT_SIZE - 1, color=TEXT_GRAY)
    for sp in ax_bottom.spines.values():
        sp.set_edgecolor(CARD_BORDER_COLOR)
    ax_bottom.grid(True, alpha=0.12, linestyle='--', color=TEXT_GRAY)

def _draw_progress(t, cur):
    """底部进度条 + 实时累计数字"""
    clear_ax(ax_foot)
    ax_foot.set_xlim(0, 100)
    ax_foot.set_ylim(0, 100)

    # 进度条背景
    card_rect(ax_foot, 4, 72, 92, 14, CARD_BORDER_COLOR, BG_CARD, alpha=0.8)
    pct = cur / TOTAL_MONTHS
    if pct > 0:
        card_rect(ax_foot, 4, 72, 92 * pct, 14, EI_BLUE, EI_BLUE, alpha=0.75)
    scene_label = _current_scene_label()
    if scene_label:
        ax_foot.text(6, 92, scene_label, fontsize=max(7, CAPTION_FONT_SIZE - 1),
                     color=TEXT_GRAY, ha='left', va='center', zorder=7)
    ax_foot.text(50, 79, f'{cur} / {TOTAL_MONTHS} 期  {pct*100:.0f}%',
                 fontsize=CAPTION_FONT_SIZE + 1, color=TEXT_WHITE, ha='center', va='center', zorder=7)

    # 累计数字
    cei = CUM_EI[cur - 1] / 10000
    cep = CUM_EP[cur - 1] / 10000
    gap = cei - cep

    for lbl, val, color, cx in [
        ('等额本息利息', f'{cei:.1f}万', EI_BLUE,   22),
        ('等额本金利息', f'{cep:.1f}万', EP_ORANGE, 50),
        ('当前差额',    f'{gap:.1f}万', GAP_PINK,  78),
    ]:
        ax_foot.text(cx, 57, lbl, fontsize=CAPTION_FONT_SIZE - 1,  color=TEXT_GRAY,  ha='center', va='center', zorder=6)
        ax_foot.text(cx, 42, val, fontsize=SUBTITLE_FONT_SIZE, color=color, ha='center', va='center',
                     fontweight=SUBTITLE_FONT_WEIGHT, zorder=6)

    # 底部说明
    footer_hint = _current_scene_footer_text()
    footer_text = '🔵 等额本息  🟠 等额本金  🟢 本金  🔴 利息'
    if footer_hint:
        footer_text = f'{footer_hint}｜{footer_text}'
    ax_foot.text(50, 18, footer_text,
                 fontsize=max(8, CAPTION_FONT_SIZE - 1), color=TEXT_DIM, ha='center', va='center', zorder=6)

# ============================================================
# 场景3：结论  (25–30s)
# ============================================================
def draw_conclusion(frame):
    t    = (frame - F_ANIM_END) / max(F_CONC_END - F_ANIM_END, 1)   # 0→1
    scene_profile = _scene_pacing_profile()
    scene_speed = float(scene_profile['speed'])
    scene_narration = _current_scene_narration(CONCLUSION_BODY, 36)
    scene_prompt = _current_scene_visual_prompt(VISUAL_FOCUS or SUMMARY_TEXT, 42)
    reveal_offsets = {
        name: idx * 0.35 for idx, name in enumerate(CONCLUSION_REVEAL_ORDER)
    }
    reveal_speed = scene_speed * float(scene_profile['reveal'])
    a0   = ease_out_cubic(clamp(t * 3 * reveal_speed - reveal_offsets.get('headline', 0.0)))
    a1   = ease_out_cubic(clamp(t * 3 * reveal_speed - reveal_offsets.get('comparison_rows', 0.5)))
    a2   = ease_out_cubic(clamp(t * 3 * reveal_speed - reveal_offsets.get('body', 1.2)))
    a3   = ease_out_cubic(clamp(t * 4 * reveal_speed - (2.2 if CONCLUSION_MODE == 'cta-spotlight' else 2.5)))

    draw_title()

    # ── info：完整30年折线 ──
    _draw_scene_copy_band(alpha=a0, compact=False)

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
                fontsize=BODY_FONT_SIZE, color=EI_BLUE, ha='center', fontweight=SUBTITLE_FONT_WEIGHT,
                alpha=a1, zorder=7)
    ax_top.text(300, ep_c[-1] - 6, f'等额本金\n{FINAL_EP/10000:.1f}万',
                fontsize=BODY_FONT_SIZE, color=EP_ORANGE, ha='center', fontweight=SUBTITLE_FONT_WEIGHT,
                alpha=a1, zorder=7)

    year_ticks  = [60, 120, 180, 240, 300, 360]
    year_labels = ['5年', '10年', '15年', '20年', '25年', '30年']
    ax_top.set_xticks(year_ticks)
    ax_top.set_xticklabels(year_labels, fontsize=CAPTION_FONT_SIZE - 1, color=TEXT_GRAY)
    ax_top.tick_params(colors=TEXT_GRAY, labelsize=CAPTION_FONT_SIZE - 1)
    ax_top.set_ylabel('累计利息（万元）', fontsize=CAPTION_FONT_SIZE, color=TEXT_GRAY)
    for sp in ax_top.spines.values():
        sp.set_edgecolor(CARD_BORDER_COLOR)
    ax_top.grid(True, alpha=0.12, linestyle='--', color=TEXT_GRAY)

    # ── bottom：结论卡片 ──
    clear_ax(ax_bottom)
    ax_bottom.set_xlim(0, 100)
    ax_bottom.set_ylim(0, 100)

    # 名言
    ax_bottom.text(50, 93, scene_narration,
                   fontsize=max(14, int((SUBTITLE_FONT_SIZE + 1) * TITLE_SCALE)), fontweight=TITLE_FONT_WEIGHT, color=CTA_COLOR,
                   ha='center', va='center', alpha=a0, zorder=6)
    ax_bottom.text(50, 84, scene_prompt,
                   fontsize=max(10, int((BODY_FONT_SIZE + 1) * SUMMARY_SCALE)), color=CARD_BODY_COLOR, ha='center', va='center',
                   style='italic', alpha=a0, zorder=6, linespacing=BODY_LINE_HEIGHT)

    # 等额本息卡
    card_rect(ax_bottom, 4, 63, 92, 16, EI_BLUE, BG_CARD2, alpha=a1 * 0.95)
    ax_bottom.text(14, 74, '等额本息', fontsize=SUBTITLE_FONT_SIZE - 1, color=EI_BLUE,
                   fontweight=SUBTITLE_FONT_WEIGHT, va='center', alpha=a1, zorder=7)
    ax_bottom.text(90, 74, f"{COPY_METRICS['full_interest_label']}  {FINAL_EI/10000:.1f} 万元",
                   fontsize=SUBTITLE_FONT_SIZE - 1, color=EI_BLUE, ha='right', va='center',
                   fontweight=SUBTITLE_FONT_WEIGHT, alpha=a1, zorder=7)

    # 等额本金卡
    card_rect(ax_bottom, 4, 44, 92, 16, EP_ORANGE, BG_CARD2, alpha=a2 * 0.95)
    ax_bottom.text(14, 55, '等额本金', fontsize=SUBTITLE_FONT_SIZE - 1, color=EP_ORANGE,
                   fontweight=SUBTITLE_FONT_WEIGHT, va='center', alpha=a2, zorder=7)
    ax_bottom.text(90, 55, f"{COPY_METRICS['full_interest_label']}  {FINAL_EP/10000:.1f} 万元",
                   fontsize=SUBTITLE_FONT_SIZE - 1, color=EP_ORANGE, ha='right', va='center',
                   fontweight=SUBTITLE_FONT_WEIGHT, alpha=a2, zorder=7)

    ax_bottom.text(50, 38, f"少付 {COPY_METRICS['interest_gap_wan_label']} ｜ 约省 {COPY_METRICS['interest_gap_pct_label']}",
                   fontsize=max(10, BODY_FONT_SIZE + 1), color=THEME_SECONDARY, ha='center', va='center',
                   fontweight=SUBTITLE_FONT_WEIGHT, alpha=max(a2, a3), zorder=7)

    # 节省大字卡
    spotlight = CONCLUSION_MODE == 'cta-spotlight' or CONCLUSION_LAYOUT == 'spotlight-card'
    base_y = 15 if spotlight else 20
    base_h = 26 if spotlight else 20
    highlight_y = base_y
    highlight_h = max(20, int(base_h * CONCLUSION_CARD_SCALE))
    title_y = highlight_y + highlight_h - 7
    body_y = highlight_y + max(7, highlight_h - 17)
    card_rect(ax_bottom, 4, highlight_y, 92, highlight_h, CARD_ACCENT_COLOR, BG_CARD, alpha=a3 * 0.45, lw=max(2.5, CARD_BORDER_WIDTH))
    ax_bottom.text(50, title_y, CONCLUSION_TITLE,
                   fontsize=max(16, CONCLUSION_TITLE_SIZE), fontweight=TITLE_FONT_WEIGHT, color=CARD_TITLE_COLOR,
                   ha='center', va='center', alpha=a3, zorder=7)
    ax_bottom.text(50, body_y, scene_narration,
                   fontsize=max(11, CONCLUSION_BODY_SIZE), color=CARD_BODY_COLOR, ha='center', va='center',
                   alpha=a3, zorder=7)

    # ── foot：月供对比 ──
    clear_ax(ax_foot)
    ax_foot.set_xlim(0, 100)
    ax_foot.set_ylim(0, 100)

    scene_label = _current_scene_label()
    if scene_label:
        ax_foot.text(6, 92, scene_label, fontsize=max(7, CAPTION_FONT_SIZE - 1),
                     color=TEXT_GRAY, ha='left', va='center', zorder=6)
    ax_foot.text(50, 88, str(COPY_METRICS['monthly_reference_label']),
                 fontsize=BODY_FONT_SIZE, color=TEXT_GRAY, ha='center', alpha=a1, zorder=6)
    ax_foot.text(26, 70, f"等额本息\n{COPY_METRICS['equal_interest_monthly_label']}",
                 fontsize=BODY_FONT_SIZE, color=EI_BLUE, ha='center', va='center',
                 alpha=a1, zorder=6, linespacing=BODY_LINE_HEIGHT)
    ax_foot.text(74, 70, f"等额本金\n{COPY_METRICS['equal_principal_monthly_label']}",
                 fontsize=BODY_FONT_SIZE, color=EP_ORANGE, ha='center', va='center',
                 alpha=a1, zorder=6, linespacing=BODY_LINE_HEIGHT)
    ax_foot.text(50, 35, ACCENT_LABEL,
                 fontsize=max(9, int((CAPTION_FONT_SIZE + 1) * ACCENT_SCALE)), color=CTA_COLOR, ha='center', va='center',
                 fontweight=SUBTITLE_FONT_WEIGHT, alpha=a2, zorder=6)
    footer_message = scene_prompt or VISUAL_FOCUS or '资金充裕→等额本金可节省更多利息'
    if CONCLUSION_MODE == 'cta-spotlight':
        footer_message = f'{ACCENT_LABEL}｜{footer_message}'
    ax_foot.text(50, 18, footer_message,
                 fontsize=CAPTION_FONT_SIZE, color=TEXT_GRAY, ha='center', va='center',
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
    global CURRENT_PHASE_ROLE, CURRENT_SCENE_ID, CURRENT_SCENE_SEGMENT, LAST_LOGGED_SCENE_ID
    global _CURRENT_ANIM_FRAME
    _CURRENT_ANIM_FRAME = frame
    if _using_frame_cache() and frame_png_path(Path(VIDEO_FRAME_CACHE_DIR), frame).is_file():
        return []
    CURRENT_PHASE_ROLE = _resolve_phase_role(frame)
    CURRENT_SCENE_SEGMENT = _resolve_scene_segment(frame)
    CURRENT_SCENE_ID = _resolve_scene_id(frame)

    if CURRENT_SCENE_ID and CURRENT_SCENE_ID != LAST_LOGGED_SCENE_ID:
        _log_scene_transition(frame)
        LAST_LOGGED_SCENE_ID = CURRENT_SCENE_ID

    if CURRENT_PHASE_ROLE == 'intro':
        draw_intro(frame)
    elif CURRENT_PHASE_ROLE == 'main':
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
_print_scene_schedule_logs()

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
    _cache_path = Path(VIDEO_FRAME_CACHE_DIR) if VIDEO_FRAME_CACHE_DIR else None
    _kwargs = {'facecolor': BG_DARK, 'edgecolor': 'none'}
    if _using_frame_cache() and _cache_path and all_frames_cached(_cache_path, TOTAL_FRAMES):
        encode_video_from_png_sequence_ffmpeg(
            OUTPUT,
            _cache_path,
            TOTAL_FRAMES,
            FPS,
            bitrate=VIDEO_BITRATE,
            preset=VIDEO_PRESET,
            crf=VIDEO_CRF,
        )
        print('\n[OK] 全量帧缓存命中，已跳过 matplotlib 逐帧绘制')
    elif _using_frame_cache() and _cache_path:
        writer = PngCachingFFMpegWriter(
            fps=FPS,
            bitrate=VIDEO_BITRATE,
            cache_dir=str(_cache_path),
            frame_getter=lambda: _CURRENT_ANIM_FRAME,
            extra_args=[
                '-vcodec', 'libx264',
                '-pix_fmt', 'yuv420p',
                '-preset', VIDEO_PRESET,
                '-crf', str(VIDEO_CRF),
            ],
        )
        ani.save(str(OUTPUT), writer=writer, dpi=DPI, savefig_kwargs=_kwargs)
        print(f'\n[OK] 渲染完成')
    else:
        writer = FFMpegWriter(
            fps=FPS, bitrate=VIDEO_BITRATE,
            extra_args=[
                '-vcodec', 'libx264',
                '-pix_fmt', 'yuv420p',
                '-preset', VIDEO_PRESET,
                '-crf', str(VIDEO_CRF),
            ],
        )
        ani.save(str(OUTPUT), writer=writer, dpi=DPI, savefig_kwargs=_kwargs)
        print(f'\n[OK] 渲染完成')
    print(f'文件: {OUTPUT}')
except Exception as exc:
    import traceback
    print(f'\n[ERROR] 渲染失败: {exc}')
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
