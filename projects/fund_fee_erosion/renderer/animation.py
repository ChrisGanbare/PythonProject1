"""基金手续费侵蚀动画渲染器（subprocess 包装层）。

generate_fund_animation() — 调用 impl.py 子进程完成渲染
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Callable

from shared.content.render_mapping import RenderExpression
from shared.config.settings import VideoConfig, get_quality_preset, settings
from shared.core.exceptions import RenderError
from shared.library.render_manifest import compute_fund_reproducibility_fingerprint
from shared.platform.presets import get_platform_preset
from shared.visualization.render_cache import render_cache_dir

from fund_fee_erosion.data.pipeline import fund_params_for_viz
from fund_fee_erosion.models.calculator import FundParams


# ── 路径辅助 ─────────────────────────────────────────────────

def _repo_root() -> Path:
    # projects/fund_fee_erosion/renderer/animation.py → parents[3] = 工作区根目录
    return Path(__file__).resolve().parents[3]


def _impl_script() -> Path:
    return Path(__file__).resolve().parent / "impl.py"


def _default_output() -> Path:
    return _repo_root() / "runtime" / "outputs" / "fund_fee_erosion.mp4"


def _to_abs_output(path: str | Path | None) -> Path:
    if not path:
        return _default_output()
    candidate = Path(path).expanduser()
    if candidate.is_absolute():
        return candidate
    return _repo_root() / candidate


# ── 公共 API ─────────────────────────────────────────────────

def generate_fund_animation(
    output_file: str | Path | None = None,
    platform: str | None = None,
    quality: str | None = None,
    width: int | None = None,
    height: int | None = None,
    duration: int | None = None,
    fps: int | None = None,
    dpi: int | None = None,
    bitrate: int | None = None,
    preset: str | None = None,
    crf: int | None = None,
    principal: float | None = None,
    gross_return: float | None = None,
    years: int | None = None,
    render_expression: RenderExpression | None = None,
    progress_callback: Callable[[int, int], None] | None = None,
) -> Path:
    """通过子进程调用 impl.py 渲染动画视频。"""
    script_path = _impl_script()
    if not script_path.exists():
        raise RuntimeError(f"动画实现脚本不存在: {script_path}")

    output_path = _to_abs_output(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    repo_root = _repo_root()
    mpl_config_dir = repo_root / "runtime" / "matplotlib"
    mpl_config_dir.mkdir(parents=True, exist_ok=True)

    env = os.environ.copy()
    env["VIDEO_OUTPUT_FILE"] = str(output_path)
    env["MPLBACKEND"] = "Agg"
    env["MPLCONFIGDIR"] = str(mpl_config_dir)
    env.setdefault("PYTHONIOENCODING", "utf-8")

    if quality is not None:
        quality_preset = get_quality_preset(quality)
        dpi = int(quality_preset["dpi"])
        bitrate = int(quality_preset["bitrate"])
        preset = str(quality_preset["preset"])
        crf = int(quality_preset["crf"])

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
        width = platform_preset.width
        height = platform_preset.height
        fps = platform_preset.fps

    if width is not None:
        env["VIDEO_WIDTH"] = str(int(width))
    if height is not None:
        env["VIDEO_HEIGHT"] = str(int(height))
    if duration is not None:
        env["VIDEO_DURATION"] = str(int(duration))
    if fps is not None:
        env["VIDEO_FPS"] = str(int(fps))
    if dpi is not None:
        env["VIDEO_DPI"] = str(int(dpi))
    if bitrate is not None:
        env["VIDEO_BITRATE"] = str(int(bitrate))
    if preset is not None:
        env["VIDEO_PRESET"] = str(preset)
    if crf is not None:
        env["VIDEO_CRF"] = str(int(crf))
    if principal is not None:
        env["VIDEO_PRINCIPAL"] = str(float(principal))
    if gross_return is not None:
        env["VIDEO_GROSS_RETURN"] = str(float(gross_return))
    if years is not None:
        env["VIDEO_YEARS"] = str(int(years))
    if render_expression is not None:
        env["VIDEO_RENDER_EXPRESSION"] = json.dumps(render_expression.model_dump(), ensure_ascii=False)

    eff_w = int(width if width is not None else settings.video.width)
    eff_h = int(height if height is not None else settings.video.height)
    eff_fps = int(fps if fps is not None else settings.video.fps)
    eff_dur = int(duration if duration is not None else settings.video.total_duration)
    eff_p = float(principal if principal is not None else 1_000_000)
    eff_g = float(gross_return if gross_return is not None else 0.08)
    eff_y = int(years if years is not None else 30)
    if quality is not None:
        _qp = get_quality_preset(quality)
        eff_dpi = int(_qp["dpi"])
        eff_br = int(_qp["bitrate"])
        eff_preset = str(_qp["preset"])
        eff_crf = int(_qp["crf"])
    else:
        eff_dpi = int(dpi if dpi is not None else settings.video.dpi)
        eff_br = int(bitrate if bitrate is not None else settings.video.bitrate)
        eff_preset = str(preset if preset is not None else settings.video.preset)
        eff_crf = int(crf if crf is not None else settings.video.crf)
    _vid_fp = {
        "width": eff_w,
        "height": eff_h,
        "fps": eff_fps,
        "total_duration": eff_dur,
        "dpi": eff_dpi,
        "bitrate": eff_br,
        "preset": eff_preset,
        "crf": eff_crf,
    }
    _fp_params = FundParams(principal=eff_p, gross_return=eff_g, years=eff_y)
    env["VIDEO_RENDER_FINGERPRINT"] = compute_fund_reproducibility_fingerprint(
        fund=fund_params_for_viz(_fp_params),
        video_config=_vid_fp,
    )
    _fcache = render_cache_dir("fund_fee_erosion", env["VIDEO_RENDER_FINGERPRINT"])
    _fcache.mkdir(parents=True, exist_ok=True)
    env["VIDEO_FRAME_CACHE_DIR"] = str(_fcache)

    if progress_callback:
        progress_callback(0, 1)

    completed = subprocess.run(
        [sys.executable, str(script_path)],
        cwd=str(repo_root),
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )

    if completed.returncode != 0:
        raise RuntimeError(
            "基金动画渲染失败:\n"
            f"stdout:\n{completed.stdout}\n\n"
            f"stderr:\n{completed.stderr}"
        )

    if progress_callback:
        progress_callback(1, 1)

    if not output_path.exists() or output_path.stat().st_size <= 0:
        raise RuntimeError(f"视频生成失败，输出文件为空: {output_path}")

    return output_path


def main() -> None:
    output = generate_fund_animation(
        output_file=os.getenv("VIDEO_OUTPUT_FILE"),
        width=int(os.getenv("VIDEO_WIDTH")) if os.getenv("VIDEO_WIDTH") else None,
        height=int(os.getenv("VIDEO_HEIGHT")) if os.getenv("VIDEO_HEIGHT") else None,
        duration=int(os.getenv("VIDEO_DURATION")) if os.getenv("VIDEO_DURATION") else None,
        fps=int(os.getenv("VIDEO_FPS")) if os.getenv("VIDEO_FPS") else None,
        principal=float(os.getenv("VIDEO_PRINCIPAL")) if os.getenv("VIDEO_PRINCIPAL") else None,
        gross_return=float(os.getenv("VIDEO_GROSS_RETURN")) if os.getenv("VIDEO_GROSS_RETURN") else None,
        years=int(os.getenv("VIDEO_YEARS")) if os.getenv("VIDEO_YEARS") else None,
    )
    print(f"视频已生成: {output}")


# ── ContentEngine ────────────────────────────────────────────

class ContentEngine:
    """供 API 层调用的编排器。"""

    def __init__(
        self,
        fund_params: FundParams,
        video_config: VideoConfig | None = None,
    ):
        self.fund_params = fund_params
        self.config = video_config or settings.video

    def generate_animation(
        self,
        output_path: Path,
        render_expression: RenderExpression | None = None,
        progress_callback: Callable[[int, int], None] | None = None,
    ) -> Path:
        try:
            return generate_fund_animation(
                output_file=output_path,
                width=int(self.config.width),
                height=int(self.config.height),
                fps=int(self.config.fps),
                duration=int(self.config.total_duration),
                dpi=int(self.config.dpi),
                bitrate=int(self.config.bitrate),
                preset=str(self.config.preset),
                crf=int(self.config.crf),
                principal=float(self.fund_params.principal),
                gross_return=float(self.fund_params.gross_return),
                years=int(self.fund_params.years),
                render_expression=render_expression,
                progress_callback=progress_callback,
            )
        except Exception as exc:
            raise RenderError(
                f"生成动画失败: {exc}", step="generate_animation"
            ) from exc


if __name__ == "__main__":
    main()
