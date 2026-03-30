"""
Opt-in PNG frame cache for matplotlib + FFMpegWriter pipelines.

When ``VIDEO_FRAME_CACHE_DIR`` is set (typically via ``render_cache_dir`` + fingerprint),
frames are stored as ``frame_000000.png`` … ``frame_NNNNNN.png`` so interrupted renders
can resume: cached frames are streamed to ffmpeg as raw RGBA without redrawing.

Also supports a **full-cache fast path**: if every frame PNG already exists, encode
directly with ffmpeg without running ``FuncAnimation.save`` (still need figure init
for scripts that print summaries after — callers can skip ``anim.save`` only).
"""

from __future__ import annotations

import io
import logging
import subprocess
from pathlib import Path
from typing import Callable

from matplotlib.animation import FFMpegWriter, _validate_grabframe_kwargs

_log = logging.getLogger(__name__)

__all__ = [
    "PngCachingFFMpegWriter",
    "all_frames_cached",
    "encode_video_from_png_sequence_ffmpeg",
    "frame_png_path",
]


def frame_png_path(cache_dir: Path, frame_index: int) -> Path:
    return Path(cache_dir) / f"frame_{int(frame_index):06d}.png"


def all_frames_cached(cache_dir: Path, total_frames: int) -> bool:
    if total_frames <= 0:
        return False
    for i in range(total_frames):
        if not frame_png_path(cache_dir, i).is_file():
            return False
    return True


def encode_video_from_png_sequence_ffmpeg(
    output: Path,
    cache_dir: Path,
    total_frames: int,
    fps: int,
    *,
    bitrate: int,
    preset: str,
    crf: int,
) -> bool:
    """
    If ``frame_000000.png`` … exist under ``cache_dir``, run ffmpeg and return True.
    Otherwise return False (caller should fall back to matplotlib animation save).
    """
    if not all_frames_cached(cache_dir, total_frames):
        return False
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    pattern = str(cache_dir / "frame_%06d.png")
    cmd = [
        "ffmpeg",
        "-y",
        "-hide_banner",
        "-loglevel",
        "error",
        "-framerate",
        str(fps),
        "-i",
        pattern,
        "-c:v",
        "libx264",
        "-pix_fmt",
        "yuv420p",
        "-preset",
        str(preset),
        "-crf",
        str(crf),
    ]
    if bitrate and int(bitrate) > 0:
        cmd.extend(["-b:v", f"{int(bitrate)}k"])
    cmd.append(str(output))
    subprocess.run(cmd, check=True)
    return True


def _fig_pixel_size(fig, dpi: float) -> tuple[int, int]:
    w = int(round(fig.get_figwidth() * dpi))
    h = int(round(fig.get_figheight() * dpi))
    return w, h


class PngCachingFFMpegWriter(FFMpegWriter):
    """
    Like ``FFMpegWriter``, but when ``cache_dir`` is set:

    - If ``frame_<n>.png`` exists for the current frame index (from ``frame_getter``),
      stream that image as raw RGBA to ffmpeg (skip matplotlib rasterization).
    - Otherwise rasterize once, write RGBA to ffmpeg, and save the same buffer to PNG
      for future runs.

    ``frame_getter`` must return the frame index **during** ``FuncAnimation``'s
    ``update(frame)`` / ``grab_frame`` pair (set the index at the start of ``update``).
    """

    def __init__(
        self,
        *args,
        cache_dir: Path | str | None = None,
        frame_getter: Callable[[], int] | None = None,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self._cache_dir = Path(cache_dir) if cache_dir else None
        self._frame_getter = frame_getter

    def grab_frame(self, **savefig_kwargs):
        _validate_grabframe_kwargs(savefig_kwargs)
        self.fig.set_size_inches(self._w, self._h)

        if not self._cache_dir or self._frame_getter is None:
            super().grab_frame(**savefig_kwargs)
            return

        try:
            from PIL import Image
        except ImportError as exc:  # pragma: no cover
            raise RuntimeError("Pillow is required for PNG frame cache") from exc

        try:
            _LANCZOS = Image.Resampling.LANCZOS
        except AttributeError:  # Pillow < 9.1
            _LANCZOS = Image.LANCZOS  # type: ignore[attr-defined]

        frame_idx = int(self._frame_getter())
        cache_path = frame_png_path(self._cache_dir, frame_idx)
        w, h = _fig_pixel_size(self.fig, self.dpi)

        if cache_path.is_file():
            im = Image.open(cache_path).convert("RGBA")
            if im.size != (w, h):
                im = im.resize((w, h), _LANCZOS)
            self._proc.stdin.write(im.tobytes())
            return

        buf = io.BytesIO()
        self.fig.savefig(buf, format="rgba", dpi=self.dpi, **savefig_kwargs)
        data = buf.getvalue()
        self._proc.stdin.write(data)

        cache_path.parent.mkdir(parents=True, exist_ok=True)
        Image.frombytes("RGBA", (w, h), data).save(cache_path, format="PNG")
