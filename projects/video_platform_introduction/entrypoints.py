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
    Generate the introduction video using Manim.

    Args:
        quality: Render quality (preview, draft, final, or legacy low/medium/high/4k).
        preview: Whether to open the video after rendering.
        platform: Target publish platform. Reserved for future platform-specific rendering.
        style: Content style. Reserved for future renderer theme selection.
        video_duration: Requested duration in seconds. Reserved for future pacing control.
        topic: Optional topic label for output metadata.
        screenplay: Optional confirmed screenplay from the dashboard workflow.
    """
    del platform, style, video_duration

    # Map quality to Manim flags
    quality_map = {
        "preview": "-ql",
        "draft": "-qm",
        "final": "-qh",
        "low": "-ql",
        "medium": "-qm",
        "high": "-qh",
        "4k": "-qk"
    }
    flag = quality_map.get(quality, "-ql")
    preview_flag = "-p" if preview else ""

    # Path to the scene file
    current_dir = Path(__file__).parent
    scene_path = current_dir / "renderer" / "intro_scene.py"
    output_dir = current_dir.parent.parent / "runtime" / "outputs" / "video_platform_introduction"

    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)

    # Environment variables for the subprocess
    env = os.environ.copy()
    temp_json_path = None

    if screenplay:
        # Create a temporary file for the screenplay JSON
        fd, temp_json_path = tempfile.mkstemp(suffix=".json", prefix="screenplay_", dir=str(output_dir))
        with os.fdopen(fd, 'w', encoding='utf-8') as f:
            json.dump(screenplay, f, ensure_ascii=False, indent=2)
        env["SCREENPLAY_PATH"] = temp_json_path
        print(f"Screenplay saved to temporary file: {temp_json_path}")

    # Construct command using sys.executable to ensure we use the same python environment
    # command format: python -m manim [flags] [scene_file] [scene_name] --media_dir [dir]
    # command = f'"{sys.executable}" -m manim {flag} {preview_flag} "{scene_path}" IntroductionScene --media_dir "{output_dir}"'

    import subprocess
    cmd = [
        sys.executable, "-m", "manim",
        flag,
        str(scene_path),
        "IntroductionScene",
        "--media_dir", str(output_dir)
    ]
    
    if preview:
        cmd.insert(3, "-p")

    print(f"Executing: {' '.join(cmd)}")
    
    # Use subprocess.run to capture output and return code
    try:
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT, # Merge stderr into stdout
            text=True,
            check=False,
            cwd=str(current_dir), # Run from project dir to ensure relative paths like "assets/logo.png" work
            env=env
        )
        
        print(f"Manim Output:\n{result.stdout}")
        
        if result.returncode != 0:
            raise RuntimeError(f"Manim rendering failed with exit code {result.returncode}.\nOutput: {result.stdout[-500:]}") # Show last 500 chars

    except Exception as e:
        raise RuntimeError(f"Execution error: {str(e)}")
    finally:
        # Clean up temporary file
        if temp_json_path and os.path.exists(temp_json_path):
            try:
                os.remove(temp_json_path)
            except OSError as e:
                print(f"Warning: Failed to remove temp file {temp_json_path}: {e}")

    # Calculate expected output path
    quality_folder_map = {
        "low": "480p15",
        "medium": "720p30",
        "high": "1080p60",
        "4k": "2160p60"
    }
    q_folder = quality_folder_map.get(quality, "480p15")
    video_file = output_dir / "videos" / "intro_scene" / q_folder / "IntroductionScene.mp4"

    return {
        "status": "success",
        "message": f"Video rendered successfully",
        "topic": topic or "Video Platform Introduction",
        "screenplay_attached": "yes" if screenplay else "no",
        "final_video_path": str(video_file)
    }
