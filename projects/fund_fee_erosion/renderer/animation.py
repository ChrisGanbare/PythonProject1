"""基金手续费侵蚀动画渲染器（subprocess 包装层）。

generate_fund_animation() — 调用 impl.py 子进程完成渲染
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path
from typing import Callable

from shared.config.settings import VideoConfig, settings
from shared.core.exceptions import RenderError
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
    width: int | None = None,
    height: int | None = None,
    duration: int | None = None,
    fps: int | None = None,
    principal: float | None = None,
    gross_return: float | None = None,
    years: int | None = None,
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

    if width is not None:
        env["VIDEO_WIDTH"] = str(int(width))
    if height is not None:
        env["VIDEO_HEIGHT"] = str(int(height))
    if duration is not None:
        env["VIDEO_DURATION"] = str(int(duration))
    if fps is not None:
        env["VIDEO_FPS"] = str(int(fps))
    if principal is not None:
        env["VIDEO_PRINCIPAL"] = str(float(principal))
    if gross_return is not None:
        env["VIDEO_GROSS_RETURN"] = str(float(gross_return))
    if years is not None:
        env["VIDEO_YEARS"] = str(int(years))

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
        progress_callback: Callable[[int, int], None] | None = None,
    ) -> Path:
        try:
            return generate_fund_animation(
                output_file=output_path,
                width=int(self.config.width),
                height=int(self.config.height),
                fps=int(self.config.fps),
                duration=int(self.config.total_duration),
                principal=float(self.fund_params.principal),
                gross_return=float(self.fund_params.gross_return),
                years=int(self.fund_params.years),
                progress_callback=progress_callback,
            )
        except Exception as exc:
            raise RenderError(
                f"生成动画失败: {exc}", step="generate_animation"
            ) from exc


if __name__ == "__main__":
    main()
