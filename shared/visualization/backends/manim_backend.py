"""
Manim — auxiliary backend for data-viz video.

Strengths: mathematical formula animation, geometric transforms, algorithm
step-through, statistical fitting animations, and explanatory overlays.

Not suitable as the primary data-chart backend (use matplotlib for bar races,
line charts, etc.).  Best used for **explanatory segments** within a larger
composition — e.g. a loan amortization formula derivation before the chart
animation, or a regression fitting walkthrough.

Integration model: subprocess invocation via ``manim`` CLI (same pattern as
the existing ``video_platform_introduction`` project), with environment
variables for parameters and ``SCREENPLAY_PATH`` for scene content.

Requires: ``pip install manim>=0.18.0``
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

from shared.visualization.types import FrameRequest, VideoFormatSpec


# ---------------------------------------------------------------------------
# Quality mapping — Manim flag ↔ project quality presets
# ---------------------------------------------------------------------------

QUALITY_FLAGS: dict[str, str] = {
    "preview": "-ql",   # 480p15  — fast iteration
    "draft": "-qm",     # 720p30  — review
    "final": "-qh",     # 1080p60 — production
    "4k": "-qk",        # 2160p60 — ultra
}

QUALITY_FOLDERS: dict[str, str] = {
    "preview": "480p15",
    "draft": "720p30",
    "final": "1080p60",
    "4k": "2160p60",
}


class ManimVizBackend:
    """VizRenderBackend implementation for Manim scenes."""

    @property
    def name(self) -> str:
        return "manim"

    def capabilities(self) -> dict[str, Any]:
        return {
            "animation": True,
            "formula_rendering": True,
            "geometric_transforms": True,
            "vector_text": True,
            "ffmpeg_export": True,
            "dpi_control": False,  # Manim manages its own pixel pipeline
            "frame_caching": False,  # PngCachingFFMpegWriter not applicable
            "recommended_for": [
                "formula_derivation",
                "algorithm_stepthrough",
                "geometric_proof",
                "regression_fitting",
                "distribution_animation",
                "statistical_explanation",
            ],
            "optional_dependencies": ["manim"],
        }

    # ------------------------------------------------------------------
    # Helper: check availability
    # ------------------------------------------------------------------

    @staticmethod
    def is_available() -> bool:
        """Return True if manim can be imported."""
        try:
            import importlib

            importlib.import_module("manim")
            return True
        except ImportError:
            return False

    # ------------------------------------------------------------------
    # Core render API
    # ------------------------------------------------------------------

    def render_scene(
        self,
        scene_file: str | Path,
        scene_class: str,
        *,
        quality: str = "preview",
        output_dir: str | Path | None = None,
        screenplay: dict[str, Any] | None = None,
        extra_env: dict[str, str] | None = None,
        frame_request: FrameRequest | None = None,
        timeout_secs: int = 600,
    ) -> dict[str, Any]:
        """
        Invoke Manim as a subprocess to render *scene_class* from *scene_file*.

        Returns a dict with ``status``, ``video_path``, ``stdout``, ``returncode``.
        """
        scene_file = Path(scene_file).resolve()
        if not scene_file.exists():
            raise FileNotFoundError(f"scene file not found: {scene_file}")

        flag = QUALITY_FLAGS.get(quality, "-ql")
        q_folder = QUALITY_FOLDERS.get(quality, "480p15")

        if output_dir is None:
            from shared.config.settings import settings
            output_dir = settings.output_dir / "manim_renders"
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        env = os.environ.copy()
        if extra_env:
            env.update(extra_env)

        # Inject frame_request as env vars if provided
        if frame_request:
            env["VIDEO_WIDTH"] = str(frame_request.format.width_px)
            env["VIDEO_HEIGHT"] = str(frame_request.format.height_px)
            env["VIDEO_FPS"] = str(frame_request.format.fps)
            env["VIDEO_DURATION"] = str(frame_request.format.total_duration_secs)
            if frame_request.theme_token:
                env["VIDEO_THEME_NAME"] = frame_request.theme_token
            if frame_request.viz_scene_id:
                env["VIDEO_VIZ_SCENE_ID"] = frame_request.viz_scene_id

        # Write screenplay to temp file if provided
        temp_json_path: str | None = None
        if screenplay:
            fd, temp_json_path = tempfile.mkstemp(
                suffix=".json", prefix="manim_sp_", dir=str(output_dir)
            )
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(screenplay, f, ensure_ascii=False, indent=2)
            env["SCREENPLAY_PATH"] = temp_json_path

        cmd = [
            sys.executable, "-m", "manim",
            flag,
            str(scene_file),
            scene_class,
            "--media_dir", str(output_dir),
        ]

        try:
            proc = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                check=False,
                cwd=str(scene_file.parent),
                env=env,
                timeout=timeout_secs,
            )

            video_path = (
                output_dir / "videos" / scene_file.stem / q_folder / f"{scene_class}.mp4"
            )

            return {
                "status": "success" if proc.returncode == 0 else "error",
                "returncode": proc.returncode,
                "stdout": proc.stdout,
                "video_path": str(video_path) if video_path.exists() else None,
                "command": " ".join(cmd),
            }
        except subprocess.TimeoutExpired:
            return {
                "status": "timeout",
                "returncode": -1,
                "stdout": f"Manim render timed out after {timeout_secs}s",
                "video_path": None,
                "command": " ".join(cmd),
            }
        finally:
            if temp_json_path and os.path.exists(temp_json_path):
                try:
                    os.remove(temp_json_path)
                except OSError:
                    pass

    # ------------------------------------------------------------------
    # Utility: format spec → Manim config overrides
    # ------------------------------------------------------------------

    @staticmethod
    def format_to_manim_config(fmt: VideoFormatSpec) -> dict[str, Any]:
        """Translate VideoFormatSpec to Manim config keys (for scene-level override)."""
        return {
            "pixel_width": fmt.width_px,
            "pixel_height": fmt.height_px,
            "frame_rate": fmt.fps,
        }
