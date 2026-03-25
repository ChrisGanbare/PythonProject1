"""Minimal runnable renderer for my_tutor.

Replace the chart drawing logic in `_draw_frame()` with your own visualization.
All other infrastructure (platform presets, quality presets, ffmpeg pipeline,
checkpoint-resume, tqdm progress) is ready to use as-is.
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patheffects as pe
import numpy as np
from tqdm import tqdm

from shared.config.settings import settings

# ── Platform presets ─────────────────────────────────────────────────────────
_PLATFORM_PRESETS: dict[str, dict] = {
    "douyin":             {"width": 1080, "height": 1920, "fps": 30},
    "bilibili_landscape": {"width": 1920, "height": 1080, "fps": 60},
    "bilibili_portrait":  {"width": 1080, "height": 1920, "fps": 60},
    "xiaohongshu":        {"width": 1080, "height": 1350, "fps": 30},
}

# ── Quality presets ──────────────────────────────────────────────────────────
_QUALITY_PRESETS: dict[str, dict] = {
    "preview": {"dpi": 72,  "crf": 28, "total_frames": 30},
    "draft":   {"dpi": 108, "crf": 23, "total_frames": 90},
    "final":   {"dpi": 144, "crf": 18, "total_frames": 180},
}


def describe_viz_backend() -> dict[str, str]:
    return {"project": "my_tutor", "renderer": "matplotlib+ffmpeg"}


# ── Frame drawing ─────────────────────────────────────────────────────────────
def _draw_frame(frame_idx: int, total_frames: int, width: int, height: int, dpi: int) -> plt.Figure:
    """Draw a single frame.  Replace this function with your chart logic."""
    fig, ax = plt.subplots(figsize=(width / dpi, height / dpi), dpi=dpi)
    fig.patch.set_facecolor("#0d1117")
    ax.set_facecolor("#0d1117")
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")

    t = frame_idx / max(total_frames - 1, 1)  # 0.0 → 1.0

    # Sample animated bar
    bar_h = 0.05 + 0.55 * t
    ax.bar(0.5, bar_h, width=0.4, bottom=0.1, color="#4c9eff", alpha=0.85)

    # Label
    label = f"Frame {frame_idx + 1}/{total_frames}"
    ax.text(
        0.5, 0.82, label, ha="center", va="center",
        fontsize=max(6, int(height / 120)),
        color="white", fontweight="bold",
        path_effects=[pe.withStroke(linewidth=2, foreground="black")],
    )
    ax.text(
        0.5, 0.72, "当前项目的介绍",
        ha="center", va="center",
        fontsize=max(5, int(height / 160)),
        color="#a0b0c0",
    )

    plt.tight_layout(pad=0)
    return fig


# ── Render pipeline ───────────────────────────────────────────────────────────
def render_video(
    quality: str = "preview",
    platform: str = "douyin",
    output_file: str | None = None,
) -> Path:
    """Render frames to PNG then stitch with ffmpeg.  Supports checkpoint-resume."""
    qp = _QUALITY_PRESETS.get(quality, _QUALITY_PRESETS["preview"])
    pp = _PLATFORM_PRESETS.get(platform, _PLATFORM_PRESETS["douyin"])
    width, height, fps = pp["width"], pp["height"], pp["fps"]
    dpi = qp["dpi"]
    total_frames = qp["total_frames"]

    out_dir = settings.video.output_dir / "my_tutor"
    frames_dir = settings.temp_dir / "my_tutor_frames" / f"{quality}_{platform}"
    frames_dir.mkdir(parents=True, exist_ok=True)
    out_dir.mkdir(parents=True, exist_ok=True)

    output_path = Path(output_file) if output_file else (
        out_dir / f"{quality}_{platform}.mp4"
    )

    # ── Render frames (checkpoint-resume: skip already-rendered) ────────────
    for i in tqdm(range(total_frames), desc=f"Rendering {quality}/{platform}", unit="frame"):
        frame_path = frames_dir / f"frame_{i:05d}.png"
        if frame_path.exists():
            continue
        fig = _draw_frame(i, total_frames, width, height, dpi)
        fig.savefig(frame_path, dpi=dpi, bbox_inches="tight", pad_inches=0)
        plt.close(fig)

    # ── FFmpeg stitch ────────────────────────────────────────────────────────
    ffmpeg_bin = shutil.which("ffmpeg") or "ffmpeg"
    cmd = [
        ffmpeg_bin, "-y",
        "-framerate", str(fps),
        "-i", str(frames_dir / "frame_%05d.png"),
        "-vf", f"scale={width}:{height}:flags=lanczos",
        "-c:v", "libx264",
        "-crf", str(qp["crf"]),
        "-pix_fmt", "yuv420p",
        "-movflags", "+faststart",
        str(output_path),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"ffmpeg failed:\n{result.stderr}")

    return output_path
