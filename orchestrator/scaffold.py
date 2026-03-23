"""Project scaffold generator."""

from __future__ import annotations

import re
import shutil
from pathlib import Path

# 仓库随附的参考实现：默认禁止通过控制台 API 删除（避免误删导致测试/文档断裂）
REFERENCE_PROJECT_NAMES: frozenset[str] = frozenset(
    {
        "loan_comparison",
        "fund_fee_erosion",
        "video_platform_introduction",
    }
)


def _sanitize_project_name(project_name: str) -> str:
    candidate = re.sub(r"[^a-zA-Z0-9_]+", "_", project_name).strip("_").lower()
    if not candidate:
        raise ValueError("project name must contain at least one alphanumeric character")
    return candidate


def sanitize_project_name(project_name: str) -> str:
    """Normalize a project id to the same form used for ``projects/<name>/`` (public API)."""
    return _sanitize_project_name(project_name)


def generate_project_scaffold(
    repo_root: Path,
    project_name: str,
    description: str | None = None,
) -> Path:
    """Generate a minimal new project scaffold under projects/."""
    safe_name = _sanitize_project_name(project_name)
    project_root = repo_root / "projects" / safe_name
    if project_root.exists():
        raise FileExistsError(f"project already exists: {project_root}")

    description = (description or f"{safe_name} data visualization project").strip()

    sample_screenplay_json = """{
  "title": "新项目剧本模板",
  "logline": "在此替换为你的叙事梗概。",
  "topic": "replace_me",
  "target_audience": "通用观众",
  "mood": "neutral",
  "visual_style": "data_driven",
  "total_duration_est": 30,
  "metadata": {},
  "scenes": [
    {
      "id": "scene_01",
      "duration_est": 10,
      "narration": "旁白与字幕文本。",
      "visual_prompt": "chart_focus",
      "mood": "neutral",
      "visuals": [],
      "audio_cues": [],
      "action_directives": {}
    }
  ]
}"""

    files: dict[Path, str] = {
        project_root / "__init__.py": "",
        # capabilities 随功能扩展；业务流程与仓库内参考实现一致，见 README「统一业务流程」
        project_root / "project_manifest.py": f'''"""Project manifest discovered by root scheduler."""\n\nPROJECT_MANIFEST = {{\n    "name": "{safe_name}",\n    "description": "{description}",\n    "default_task": "smoke_check",\n    "capabilities": {{\n        "viz_backends": ["matplotlib"],\n    }},\n    "tasks": {{\n        "smoke_check": {{\n            "callable": "{safe_name}.entrypoints:run_smoke_check",\n            "description": "Basic validation for {safe_name}",\n        }},\n        "render": {{\n            "callable": "{safe_name}.entrypoints:run_render",\n            "description": "Generate visualization video",\n        }},\n    }},\n}}\n''',
        project_root / "entrypoints.py": f'''"""Callable entrypoints exposed for the root scheduler."""\n\nfrom __future__ import annotations\n\n\ndef run_smoke_check() -> dict[str, str]:\n    return {{"project": "{safe_name}", "status": "ok"}}\n\n\ndef run_render(\n    quality: str = "draft",\n    platform: str = "douyin",\n    output_file: str = "",\n) -> dict[str, str]:\n    """Generate visualization video via the project renderer."""\n    from {safe_name}.renderer.viz_backend import render_video\n\n    result_path = render_video(\n        quality=quality,\n        platform=platform,\n        output_file=output_file or None,\n    )\n    return {{"final_video_path": str(result_path), "status": "success"}}\n''',
        project_root / "content" / "__init__.py": "",
        project_root / "content" / "planner.py": f'''"""Content planner adapter for {safe_name}."""\n\nfrom __future__ import annotations\n\nfrom shared.content.planner import build_content_plan\nfrom shared.content.schemas import ContentBrief, ContentPlan\n\n\ndef build_{safe_name}_content_plan(request, summary: dict | None = None) -> ContentPlan:\n    del summary\n    brief = ContentBrief(\n        topic="{description}",\n        platform=request.platform.value,\n        style=request.style,\n        variant=request.content_variant,\n        total_duration=request.video_duration,\n        hook_fact="用一句话抛出本期核心问题。",\n        setup_fact="在这里放入关键数据背景。",\n        climax_fact="在这里放入最值得放大的高潮数字。",\n        conclusion_fact="在这里放入一句话结论。",\n        call_to_action="补一句适合平台的行动建议。",\n        tags=["{safe_name}", request.platform.value, request.style.value],\n    )\n    return build_content_plan(brief)\n''',
        project_root / "content" / "sample_screenplay.json": sample_screenplay_json,
        project_root / "renderer" / "__init__.py": "",
        project_root / "renderer" / "viz_backend.py": f'''"""Minimal runnable renderer for {safe_name}.

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
_PLATFORM_PRESETS: dict[str, dict] = {{
    "douyin":             {{"width": 1080, "height": 1920, "fps": 30}},
    "bilibili_landscape": {{"width": 1920, "height": 1080, "fps": 60}},
    "bilibili_portrait":  {{"width": 1080, "height": 1920, "fps": 60}},
    "xiaohongshu":        {{"width": 1080, "height": 1350, "fps": 30}},
}}

# ── Quality presets ──────────────────────────────────────────────────────────
_QUALITY_PRESETS: dict[str, dict] = {{
    "preview": {{"dpi": 72,  "crf": 28, "total_frames": 30}},
    "draft":   {{"dpi": 108, "crf": 23, "total_frames": 90}},
    "final":   {{"dpi": 144, "crf": 18, "total_frames": 180}},
}}


def describe_viz_backend() -> dict[str, str]:
    return {{"project": "{safe_name}", "renderer": "matplotlib+ffmpeg"}}


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
    label = f"Frame {{frame_idx + 1}}/{{total_frames}}"
    ax.text(
        0.5, 0.82, label, ha="center", va="center",
        fontsize=max(6, int(height / 120)),
        color="white", fontweight="bold",
        path_effects=[pe.withStroke(linewidth=2, foreground="black")],
    )
    ax.text(
        0.5, 0.72, "{description}",
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

    out_dir = settings.video.output_dir / "{safe_name}"
    frames_dir = settings.temp_dir / "{safe_name}_frames" / f"{{quality}}_{{platform}}"
    frames_dir.mkdir(parents=True, exist_ok=True)
    out_dir.mkdir(parents=True, exist_ok=True)

    output_path = Path(output_file) if output_file else (
        out_dir / f"{{quality}}_{{platform}}.mp4"
    )

    # ── Render frames (checkpoint-resume: skip already-rendered) ────────────
    for i in tqdm(range(total_frames), desc=f"Rendering {{quality}}/{{platform}}", unit="frame"):
        frame_path = frames_dir / f"frame_{{i:05d}}.png"
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
        "-vf", f"scale={{width}}:{{height}}:flags=lanczos",
        "-c:v", "libx264",
        "-crf", str(qp["crf"]),
        "-pix_fmt", "yuv420p",
        "-movflags", "+faststart",
        str(output_path),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"ffmpeg failed:\\n{{result.stderr}}")

    return output_path
''',
        project_root / "tests" / "__init__.py": "",
        project_root / "tests" / "test_smoke.py": f'''"""Smoke test for {safe_name}."""\n\nfrom {safe_name}.entrypoints import run_smoke_check\n\n\ndef test_smoke_check_returns_ok():\n    result = run_smoke_check()\n    assert result["status"] == "ok"\n    assert result["project"] == "{safe_name}"\n''',
    }

    for file_path, content in files.items():
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content, encoding="utf-8")

    return project_root


def delete_project_scaffold(repo_root: Path, project_name: str) -> Path:
    """Remove ``projects/<name>/``. Refuses reference projects and path traversal."""
    safe_name = _sanitize_project_name(project_name)
    projects_root = (repo_root / "projects").resolve()
    project_root = (projects_root / safe_name).resolve()
    if not project_root.exists():
        raise FileNotFoundError(f"project not found: {safe_name}")
    if not str(project_root).startswith(str(projects_root)) or project_root == projects_root:
        raise ValueError("invalid project path")
    if safe_name in REFERENCE_PROJECT_NAMES:
        raise PermissionError(
            "内置参考项目不可通过控制台删除；若确需移除请手动删除目录或使用 git 还原"
        )
    shutil.rmtree(project_root)
    return project_root
