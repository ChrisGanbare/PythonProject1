"""Loan animation renderer.

generate_loan_animation() — subprocess wrapper that invokes impl.py
ContentEngine             — thin orchestration layer used by the API
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Callable, cast

from shared.content.render_mapping import RenderExpression
from shared.content.render_timeline import RenderTimeline
from shared.config.settings import VideoConfig, get_quality_preset, settings
from shared.core.exceptions import RenderError
from shared.platform.presets import get_platform_preset
from shared.content.screenplay import Screenplay
from shared.library.render_manifest import (
    collect_viz_scene_refs_from_screenplay,
    compute_reproducibility_fingerprint,
)
from shared.visualization.render_cache import render_cache_dir

from ..data.pipeline import loan_params_for_viz
from ..models.loan import LoanData
from .director import Director


# ── path helpers ────────────────────────────────────────────────────────────

def _repo_root() -> Path:
    # projects/loan_comparison/renderer/animation.py → parents[3] = workspace root
    return Path(__file__).resolve().parents[3]


def _impl_script() -> Path:
    return Path(__file__).resolve().parent / "impl.py"


def _default_output() -> Path:
    return _repo_root() / "runtime" / "outputs" / "loan_comparison_flourish.mp4"


def resolve_scene_schedule_sidecar_path(output_path: str | Path) -> Path:
    candidate = Path(output_path)
    return candidate.with_name(f"{candidate.stem}.scene_schedule.json")


def _to_abs_output(path: str | Path | None) -> Path:
    if not path:
        return _default_output()
    candidate = Path(path).expanduser()
    if candidate.is_absolute():
        return candidate
    return _repo_root() / candidate


def _deep_merge_dict(base: dict[str, object], overrides: dict[str, object]) -> dict[str, object]:
    merged = dict(base)
    for key, value in overrides.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _deep_merge_dict(merged[key], value)
        else:
            merged[key] = value
    return merged


def _drop_none_values(payload: object) -> object:
    if isinstance(payload, dict):
        return {
            key: _drop_none_values(value)
            for key, value in payload.items()
            if value is not None
        }
    if isinstance(payload, list):
        return [_drop_none_values(item) for item in payload]
    return payload


def _sanitize_render_expression_payload(payload: dict[str, object]) -> dict[str, object]:
    return cast(dict[str, object], _drop_none_values(payload))


def _merge_render_expression_payloads(
    screenplay_payload: dict[str, object] | None,
    explicit_payload: dict[str, object],
) -> dict[str, object]:
    if not screenplay_payload:
        return dict(explicit_payload)
    return _deep_merge_dict(_sanitize_render_expression_payload(screenplay_payload), explicit_payload)


def _build_scene_schedule_payload(render_expression_payload: dict[str, object]) -> dict[str, object] | None:
    timeline_payload = render_expression_payload.get("timeline")
    if not isinstance(timeline_payload, dict) or not timeline_payload.get("scenes"):
        return None
    try:
        timeline = RenderTimeline.model_validate(timeline_payload)
    except Exception:
        return None
    return timeline.export_schedule_payload()


def _write_scene_schedule_sidecar(output_path: Path, schedule_payload: dict[str, object] | None) -> Path | None:
    if not schedule_payload:
        return None
    sidecar_path = resolve_scene_schedule_sidecar_path(output_path)
    sidecar_path.write_text(json.dumps(schedule_payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return sidecar_path


# ── public API ──────────────────────────────────────────────────────────────

def generate_loan_animation(
    output_file: str | Path | None = None,
    platform: str | None = None,
    quality: str | None = None,
    width: int | None = None,
    height: int | None = None,
    duration: int | None = None,
    fps: int | None = None,
    loan_amount: float | None = None,
    annual_rate: float | None = None,
    loan_years: int | None = None,
    screenplay: Screenplay | None = None,
    theme_overrides: dict | None = None,
    render_expression: RenderExpression | dict | None = None,
    progress_callback: Callable[[int, int], None] | None = None,
) -> Path:
    """
    Renders the loan animation using Matplotlib.
    
    If `screenplay` is provided, it uses the Director to configure the renderer.
    """
    # ── 1. Resolve Params ───────────────────────────────────────────────────
    script_path = _impl_script()
    if not script_path.exists():
        raise RuntimeError(f"animation implementation not found: {script_path}")

    output_path = _to_abs_output(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    repo_root = _repo_root()
    mpl_config_dir = repo_root / "runtime" / "matplotlib"
    mpl_config_dir.mkdir(parents=True, exist_ok=True)

    effective_width = width
    effective_height = height
    effective_fps = fps
    effective_duration = duration

    if platform is not None:
        platform_preset = get_platform_preset(platform)
        if width is not None and int(width) != platform_preset.width:
            raise ValueError(f"platform '{platform}' requires width={platform_preset.width}")
        if height is not None and int(height) != platform_preset.height:
            raise ValueError(f"platform '{platform}' requires height={platform_preset.height}")
        if fps is not None and int(fps) != platform_preset.fps:
            raise ValueError(f"platform '{platform}' requires fps={platform_preset.fps}")
        if duration is not None and not (platform_preset.min_duration <= int(duration) <= platform_preset.max_duration):
            raise ValueError(
                f"platform '{platform}' requires duration between {platform_preset.min_duration} and {platform_preset.max_duration} seconds"
            )
        effective_width = platform_preset.width
        effective_height = platform_preset.height
        effective_fps = platform_preset.fps

    effective_width = int(effective_width or settings.video.width)
    effective_height = int(effective_height or settings.video.height)
    effective_fps = int(effective_fps or settings.video.fps)
    effective_duration = int(effective_duration or settings.video.total_duration)
    effective_loan_amount = float(loan_amount or 1_000_000)
    effective_annual_rate = float(annual_rate or 0.045)
    effective_loan_years = int(loan_years or 30)

    render_expression_payload: dict[str, object]
    if isinstance(render_expression, dict):
        render_expression_payload = _sanitize_render_expression_payload(dict(render_expression))
    elif render_expression is None:
        render_expression_payload = {}
    else:
        render_expression_payload = render_expression.model_dump(exclude_none=True)

    # ── 2. Prepare Environment ──────────────────────────────────────────────
    env = os.environ.copy()
    env["MPLCONFIGDIR"] = str(mpl_config_dir)
    env["PYTHONUTF8"] = "1"
    env["PYTHONIOENCODING"] = "utf-8"
    env["VIDEO_OUTPUT_FILE"] = str(output_path)
    env["VIDEO_LOAN_AMOUNT"] = str(effective_loan_amount)
    env["VIDEO_ANNUAL_RATE"] = str(effective_annual_rate)
    env["VIDEO_LOAN_YEARS"] = str(effective_loan_years)
    env["VIDEO_WIDTH"] = str(effective_width)
    env["VIDEO_HEIGHT"] = str(effective_height)
    env["VIDEO_DURATION"] = str(effective_duration)
    env["VIDEO_FPS"] = str(effective_fps)
    env["VIDEO_RENDER_EXPRESSION"] = json.dumps(render_expression_payload, ensure_ascii=False)

    # [NEW] Director Integration
    if screenplay:
        director = Director(screenplay)
        director.direct()
        legacy_config = director.export_legacy_config(total_seconds=effective_duration, fps=effective_fps)
        if legacy_config:
            env["VIDEO_THEME_CONFIG"] = json.dumps(legacy_config)
            screenplay_render_expression = legacy_config.get("render_expression")
            if isinstance(screenplay_render_expression, dict):
                render_expression_payload = _merge_render_expression_payloads(
                    screenplay_render_expression,
                    render_expression_payload,
                )

    env["VIDEO_RENDER_EXPRESSION"] = json.dumps(render_expression_payload, ensure_ascii=False)

    if theme_overrides:
        current_theme = json.loads(env.get("VIDEO_THEME_CONFIG", "{}") or "{}")
        current_theme.update(theme_overrides)
        env["VIDEO_THEME_CONFIG"] = json.dumps(current_theme, ensure_ascii=False)

    if quality is not None:
        quality_preset = get_quality_preset(quality)
        env["VIDEO_DPI"] = str(int(quality_preset["dpi"]))
        env["VIDEO_BITRATE"] = str(int(quality_preset["bitrate"]))
        env["VIDEO_PRESET"] = str(quality_preset["preset"])
        env["VIDEO_CRF"] = str(int(quality_preset["crf"]))

    if quality is not None:
        _qp = get_quality_preset(quality)
        _vid_fp = {
            "width": effective_width,
            "height": effective_height,
            "fps": effective_fps,
            "total_duration": effective_duration,
            "dpi": int(_qp["dpi"]),
            "bitrate": int(_qp["bitrate"]),
            "preset": str(_qp["preset"]),
            "crf": int(_qp["crf"]),
            "renderer_revision": 3,
        }
    else:
        _vid_fp = {
            "width": effective_width,
            "height": effective_height,
            "fps": effective_fps,
            "total_duration": effective_duration,
            "dpi": int(settings.video.dpi),
            "bitrate": int(settings.video.bitrate),
            "preset": str(settings.video.preset),
            "crf": int(settings.video.crf),
            "renderer_revision": 3,
        }
    _loan_data = LoanData(
        loan_amount=effective_loan_amount,
        annual_rate=effective_annual_rate,
        loan_years=effective_loan_years,
    )
    _loan_fp = loan_params_for_viz(_loan_data)
    _viz_refs = collect_viz_scene_refs_from_screenplay(screenplay) if screenplay else []
    env["VIDEO_RENDER_FINGERPRINT"] = compute_reproducibility_fingerprint(
        loan=_loan_fp,
        video_config=_vid_fp,
        viz_refs=_viz_refs,
    )
    _cache = render_cache_dir("loan_comparison", env["VIDEO_RENDER_FINGERPRINT"])
    _cache.mkdir(parents=True, exist_ok=True)
    env["VIDEO_FRAME_CACHE_DIR"] = str(_cache)

    scene_schedule_payload = _build_scene_schedule_payload(render_expression_payload)

    # ── 3. Execute Subprocess ───────────────────────────────────────────────
    cmd = [sys.executable, str(script_path)]

    try:
        completed = subprocess.run(
            cmd,
            cwd=str(repo_root),
            env=env,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
    except Exception as e:
        raise RuntimeError(f"failed to run animation script: {e}") from e

    if completed.returncode != 0:
        raise RuntimeError(
            "loan animation render failed:\n"
            f"stdout:\n{completed.stdout}\n\n"
            f"stderr:\n{completed.stderr}"
        )

    if completed.stdout:
        print(completed.stdout, end="" if completed.stdout.endswith("\n") else "\n")
    if completed.stderr:
        print(completed.stderr, end="" if completed.stderr.endswith("\n") else "\n", file=sys.stderr)

    if not output_path.exists() or output_path.stat().st_size <= 0:
        raise RuntimeError(f"video generation failed, output empty: {output_path}")

    scene_schedule_path = _write_scene_schedule_sidecar(output_path, scene_schedule_payload)
    if scene_schedule_path is not None:
        print(f"scene schedule metadata: {scene_schedule_path}")

    if progress_callback is not None:
        progress_callback(1, 1)

    return output_path


def main() -> None:
    output = generate_loan_animation(
        output_file=os.getenv("VIDEO_OUTPUT_FILE"),
        width=int(os.getenv("VIDEO_WIDTH")) if os.getenv("VIDEO_WIDTH") else None,
        height=int(os.getenv("VIDEO_HEIGHT")) if os.getenv("VIDEO_HEIGHT") else None,
        duration=int(os.getenv("VIDEO_DURATION")) if os.getenv("VIDEO_DURATION") else None,
        fps=int(os.getenv("VIDEO_FPS")) if os.getenv("VIDEO_FPS") else None,
        loan_amount=float(os.getenv("VIDEO_LOAN_AMOUNT")) if os.getenv("VIDEO_LOAN_AMOUNT") else None,
        annual_rate=float(os.getenv("VIDEO_ANNUAL_RATE")) if os.getenv("VIDEO_ANNUAL_RATE") else None,
        loan_years=int(os.getenv("VIDEO_LOAN_YEARS")) if os.getenv("VIDEO_LOAN_YEARS") else None,
    )
    print(f"video generated: {output}")


# ── ContentEngine ────────────────────────────────────────────────────────────

class ColorScheme:
    def __init__(self, name: str = "dark_flourish"):
        self.name = name


class ContentEngine:
    def __init__(
        self,
        loan_data: LoanData,
        video_config: VideoConfig | None = None,
        color_scheme: ColorScheme | None = None,
    ):
        self.loan_data = loan_data
        self.config = video_config or settings.video
        self.color_scheme = color_scheme or ColorScheme()

    def generate_animation(
        self,
        output_path: Path,
        render_expression: RenderExpression | None = None,
        progress_callback: Callable[[int, int], None] | None = None,
        screenplay: Screenplay | None = None,
    ) -> Path:
        """Generate video using the subprocess renderer."""
        try:
            return generate_loan_animation(
                output_file=output_path,
                width=int(self.config.width),
                height=int(self.config.height),
                fps=int(self.config.fps),
                duration=int(self.config.total_duration),
                loan_amount=float(self.loan_data.loan_amount),
                annual_rate=float(self.loan_data.annual_rate),
                loan_years=int(self.loan_data.loan_years),
                render_expression=render_expression,
                progress_callback=progress_callback,
                screenplay=screenplay,
            )
        except Exception as exc:
            raise RenderError(f"failed to generate animation: {exc}", step="generate_animation") from exc


if __name__ == "__main__":
    main()
