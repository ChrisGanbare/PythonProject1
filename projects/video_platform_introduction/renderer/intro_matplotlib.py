"""
Matplotlib-based fallback renderer for the video platform introduction project.
Used when Manim is not installed.  Produces a simple slide-style MP4 without
any external dependencies beyond matplotlib and ffmpeg.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.figure import Figure
import numpy as np

from shared.config.settings import get_quality_preset
from shared.content.typography import apply_matplotlib_typography
from shared.platform.presets import get_platform_preset
from shared.visualization.render_cache import render_cache_dir


# ---------------------------------------------------------------------------
# Palette & typography helpers
# ---------------------------------------------------------------------------

_BG_COLOR = "#0d1117"
_ACCENT = "#58a6ff"
_TEXT_PRIMARY = "#e6edf3"
_TEXT_SECONDARY = "#8b949e"
_HIGHLIGHT = "#1f6feb"


def _make_fig(width_px: int = 1920, height_px: int = 1080, dpi: int = 96) -> Figure:
    w = width_px / dpi
    h = height_px / dpi
    fig = plt.figure(figsize=(w, h), dpi=dpi, facecolor=_BG_COLOR)
    return fig


def _clear_axes(fig: Figure) -> plt.Axes:
    fig.clf()
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.set_facecolor(_BG_COLOR)
    ax.axis("off")
    return ax


def _draw_grid(ax: plt.Axes, alpha: float = 0.06) -> None:
    """Subtle background grid for tech aesthetic."""
    for x in np.linspace(0, 1, 20):
        ax.axvline(x, color=_ACCENT, alpha=alpha, linewidth=0.5)
    for y in np.linspace(0, 1, 12):
        ax.axhline(y, color=_ACCENT, alpha=alpha, linewidth=0.5)


def _draw_accent_bar(ax: plt.Axes, y: float = 0.54, width: float = 0.08) -> None:
    rect = mpatches.FancyBboxPatch(
        (0.5 - width / 2, y), width, 0.004,
        boxstyle="round,pad=0", linewidth=0,
        facecolor=_ACCENT,
    )
    ax.add_patch(rect)


# ---------------------------------------------------------------------------
# Slide builders
# ---------------------------------------------------------------------------

def _slide_title(fig: Figure, title: str, subtitle: str) -> None:
    ax = _clear_axes(fig)
    _draw_grid(ax)
    # Corner decoration
    for corner_x, corner_y in [(0.02, 0.95), (0.98, 0.95), (0.02, 0.05), (0.98, 0.05)]:
        ax.plot(corner_x, corner_y, "s", color=_ACCENT, markersize=6, alpha=0.7)
    # Title
    ax.text(0.5, 0.60, title, ha="center", va="center",
            color=_TEXT_PRIMARY, fontsize=40, fontweight="bold",
            transform=ax.transAxes)
    _draw_accent_bar(ax, y=0.52)
    ax.text(0.5, 0.44, subtitle, ha="center", va="center",
            color=_TEXT_SECONDARY, fontsize=18,
            transform=ax.transAxes)


def _slide_features(fig: Figure, heading: str, features: list[str]) -> None:
    ax = _clear_axes(fig)
    _draw_grid(ax)
    ax.text(0.5, 0.82, heading, ha="center", va="center",
            color=_ACCENT, fontsize=28, fontweight="bold",
            transform=ax.transAxes)
    _draw_accent_bar(ax, y=0.75, width=0.12)
    y_start = 0.65
    step = 0.10
    for i, feat in enumerate(features[:6]):
        y = y_start - i * step
        ax.plot(0.22, y + 0.01, "o", color=_ACCENT, markersize=7, transform=ax.transAxes)
        ax.text(0.25, y, feat, ha="left", va="center",
                color=_TEXT_PRIMARY, fontsize=20,
                transform=ax.transAxes)


def _slide_closing(fig: Figure, text: str) -> None:
    ax = _clear_axes(fig)
    _draw_grid(ax)
    # Glowing circle
    for radius, alpha in [(0.22, 0.04), (0.18, 0.07), (0.13, 0.12), (0.08, 0.20)]:
        circle = plt.Circle((0.5, 0.5), radius, color=_ACCENT,
                             alpha=alpha, transform=ax.transAxes)
        ax.add_patch(circle)
    ax.text(0.5, 0.50, text, ha="center", va="center",
            color=_TEXT_PRIMARY, fontsize=36, fontweight="bold",
            transform=ax.transAxes)


# ---------------------------------------------------------------------------
# Public render entry
# ---------------------------------------------------------------------------

def render_intro_matplotlib(
    output_dir: Path,
    quality: str = "draft",
    screenplay: dict[str, Any] | None = None,
    *,
    platform: str = "douyin",
    video_duration: int = 30,
    fps: int | None = None,
) -> Path:
    """
    Render an introduction video using matplotlib + ffmpeg.
    Returns the path to the output .mp4 file.
    """
    # ---- resolve content from screenplay ----
    title_text = "视频自动化创作平台"
    subtitle_text = "Automated Video Creation Platform"
    features_list = [
        "1. 数据驱动 (Data Driven)",
        "2. 自动排版 (Auto Layout)",
        "3. 多平台适配 (Multi-Platform)",
        "4. 批量生成 (Batch Processing)",
    ]
    conclusion_text = "感谢观看"

    if screenplay:
        scenes = screenplay.get("scenes", [])
        if len(scenes) >= 1:
            s0 = scenes[0]
            visuals = s0.get("visuals", [])
            if visuals and visuals[0].get("type") == "text":
                title_text = visuals[0].get("content", title_text)
            if s0.get("narration"):
                nar = s0["narration"]
                subtitle_text = (nar[:40] + "…") if len(nar) > 40 else nar
        if len(scenes) >= 2:
            s1 = scenes[1]
            bullets = [
                v.get("content", "")
                for v in s1.get("visuals", [])
                if v.get("type") == "text" and v.get("content")
            ]
            if bullets:
                features_list = bullets[:6]
        if len(scenes) >= 3:
            last_text = scenes[-1].get("narration") or scenes[-1].get("title", conclusion_text)
            conclusion_text = last_text[:20] if last_text else conclusion_text

    # ---- quality presets ----
    quality_aliases = {
        "low": "preview",
        "medium": "draft",
        "high": "final",
    }
    resolved_quality = quality_aliases.get(quality, quality)
    quality_preset = get_quality_preset(resolved_quality)
    platform_preset = get_platform_preset(platform)
    apply_matplotlib_typography()

    w = platform_preset.width
    h = platform_preset.height
    dpi = int(quality_preset["dpi"])
    out_fps = int(fps or platform_preset.fps)
    total_duration = max(float(video_duration), 6.0)
    slide_durations = [total_duration * 0.32, total_duration * 0.38, total_duration * 0.30]

    output_dir.mkdir(parents=True, exist_ok=True)
    fingerprint_payload = {
        "platform": platform_preset.name,
        "quality": resolved_quality,
        "video_duration": int(video_duration),
        "fps": out_fps,
        "title": title_text,
        "subtitle": subtitle_text,
        "features": features_list,
        "conclusion": conclusion_text,
    }
    fingerprint = hashlib.sha256(
        json.dumps(fingerprint_payload, ensure_ascii=False, sort_keys=True).encode("utf-8")
    ).hexdigest()
    frames_dir = render_cache_dir("video_platform_introduction", fingerprint)
    frames_dir.mkdir(parents=True, exist_ok=True)

    fig = _make_fig(w, h, dpi)

    # Each slide: (builder_fn, *args), hold_seconds
    slides: list[tuple[Any, float]] = [
        ((_slide_title, fig, title_text, subtitle_text), slide_durations[0]),
        ((_slide_features, fig, "核心功能", features_list), slide_durations[1]),
        ((_slide_closing, fig, conclusion_text), slide_durations[2]),
    ]

    # Render frames
    frame_idx = 0
    for (builder_args, duration) in slides:
        fn, *args = builder_args
        fn(*args)
        n_frames = max(1, int(round(duration * out_fps)))
        for _ in range(n_frames):
            frame_path = frames_dir / f"frame_{frame_idx:05d}.png"
            if not frame_path.exists():
                fig.savefig(str(frame_path), dpi=dpi, facecolor=_BG_COLOR, pad_inches=0)
            frame_idx += 1

    plt.close(fig)

    # Assemble with ffmpeg
    output_video = output_dir / f"IntroductionScene_{platform_preset.name}_{resolved_quality}.mp4"
    _ffmpeg_assemble(
        frames_dir,
        output_video,
        out_fps,
        width=w,
        height=h,
        bitrate=int(quality_preset["bitrate"]),
        preset=str(quality_preset["preset"]),
        crf=int(quality_preset["crf"]),
    )

    return output_video


def _ffmpeg_assemble(
    frames_dir: Path,
    output: Path,
    fps: int,
    *,
    width: int,
    height: int,
    bitrate: int,
    preset: str,
    crf: int,
) -> None:
    import subprocess

    pattern = str(frames_dir / "frame_%05d.png")
    cmd = [
        "ffmpeg", "-y",
        "-hide_banner",
        "-loglevel", "error",
        "-framerate", str(fps),
        "-i", pattern,
        "-c:v", "libx264",
        "-preset", preset,
        "-b:v", f"{bitrate}k",
        "-vf", f"scale={width}:{height}:flags=lanczos,format=yuv420p",
        "-pix_fmt", "yuv420p",
        "-crf", str(crf),
        "-movflags", "+faststart",
        str(output),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        # ffmpeg not on PATH — try with python's shutil.which fallback
        raise RuntimeError(
            f"ffmpeg失败 (exit {result.returncode}).\n"
            f"请确认 ffmpeg 已安装并在 PATH 中。\n"
            f"详情: {result.stderr[-400:]}"
        )
