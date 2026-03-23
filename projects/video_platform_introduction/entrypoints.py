"""Callable entrypoints exposed for the root scheduler."""

from __future__ import annotations

import sys
import json
import tempfile
import os
from pathlib import Path


def run_smoke_check() -> dict[str, str]:
    return {"project": "video_platform_introduction", "status": "ok"}


def run_api(host: str = "0.0.0.0", port: int = 8010) -> None:
    from .api.main import start_api_server

    start_api_server(host=host, port=port)


def _manim_available() -> bool:
    """Return True only when both the manim package and the CLI are accessible."""
    import importlib
    try:
        importlib.import_module("manim")
        return True
    except ImportError:
        return False


def run_intro_video(
    quality: str = "preview",
    preview: bool = False,
    platform: str = "douyin",
    style: str = "tech",
    video_duration: int = 30,
    topic: str = "",
    screenplay: dict | None = None,
) -> dict[str, str]:
    """
    Generate the introduction video.

    Uses Manim when available; automatically falls back to a matplotlib-based
    renderer when Manim is not installed so the task never hard-fails due to a
    missing optional dependency.

    Args:
        quality: Render quality (preview, draft, final, or legacy low/medium/high/4k).
        preview: Whether to open the video after rendering (Manim path only).
        platform: Target publish platform. Reserved for future platform-specific rendering.
        style: Content style. Reserved for future renderer theme selection.
        video_duration: Requested duration in seconds. Reserved for future pacing control.
        topic: Optional topic label for output metadata.
        screenplay: Optional confirmed screenplay from the dashboard workflow.
    """
    del platform, style, video_duration

    current_dir = Path(__file__).parent
    output_dir = current_dir.parent.parent / "runtime" / "outputs" / "video_platform_introduction"
    output_dir.mkdir(parents=True, exist_ok=True)

    if not _manim_available():
        # ---- matplotlib fallback ----
        print("[video_platform_introduction] Manim 未安装，使用 matplotlib 渲染器作为替代。")
        from .renderer.intro_matplotlib import render_intro_matplotlib
        video_file = render_intro_matplotlib(output_dir, quality=quality, screenplay=screenplay)
        return {
            "status": "success",
            "message": "Video rendered successfully (matplotlib fallback — Manim not installed)",
            "renderer": "matplotlib",
            "topic": topic or "Video Platform Introduction",
            "screenplay_attached": "yes" if screenplay else "no",
            "final_video_path": str(video_file),
        }

    # ---- Manim path ----
    import subprocess

    quality_map = {
        "preview": "-ql",
        "draft": "-qm",
        "final": "-qh",
        "low": "-ql",
        "medium": "-qm",
        "high": "-qh",
        "4k": "-qk",
    }
    flag = quality_map.get(quality, "-ql")

    scene_path = current_dir / "renderer" / "intro_scene.py"
    env = os.environ.copy()
    temp_json_path = None

    if screenplay:
        fd, temp_json_path = tempfile.mkstemp(suffix=".json", prefix="screenplay_", dir=str(output_dir))
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(screenplay, f, ensure_ascii=False, indent=2)
        env["SCREENPLAY_PATH"] = temp_json_path
        print(f"Screenplay saved to temporary file: {temp_json_path}")

    cmd = [
        sys.executable, "-m", "manim",
        flag,
        str(scene_path),
        "IntroductionScene",
        "--media_dir", str(output_dir),
    ]
    if preview:
        cmd.insert(3, "-p")

    print(f"Executing: {' '.join(cmd)}")
    try:
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            check=False,
            cwd=str(current_dir),
            env=env,
        )
        print(f"Manim Output:\n{result.stdout}")
        if result.returncode != 0:
            raise RuntimeError(
                f"Manim rendering failed with exit code {result.returncode}.\n"
                f"Output: {result.stdout[-500:]}"
            )
    except Exception as exc:
        raise RuntimeError(f"Execution error: {exc}") from exc
    finally:
        if temp_json_path and os.path.exists(temp_json_path):
            try:
                os.remove(temp_json_path)
            except OSError as e:
                print(f"Warning: Failed to remove temp file {temp_json_path}: {e}")

    quality_folder_map = {
        "low": "480p15",
        "medium": "720p30",
        "high": "1080p60",
        "4k": "2160p60",
    }
    q_folder = quality_folder_map.get(quality, "480p15")
    video_file = output_dir / "videos" / "intro_scene" / q_folder / "IntroductionScene.mp4"

    return {
        "status": "success",
        "message": "Video rendered successfully",
        "renderer": "manim",
        "topic": topic or "Video Platform Introduction",
        "screenplay_attached": "yes" if screenplay else "no",
        "final_video_path": str(video_file),
    }
