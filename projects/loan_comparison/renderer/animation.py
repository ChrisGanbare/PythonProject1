"""Loan animation renderer.

generate_loan_animation() — subprocess wrapper that invokes impl.py
ContentEngine             — thin orchestration layer used by the API
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path
from typing import Callable

from shared.config.settings import VideoConfig, settings
from shared.core.exceptions import RenderError
from loan_comparison.models.loan import LoanData


# ── path helpers ────────────────────────────────────────────────────────────

def _repo_root() -> Path:
    # projects/loan_comparison/renderer/animation.py → parents[3] = workspace root
    return Path(__file__).resolve().parents[3]


def _impl_script() -> Path:
    return Path(__file__).resolve().parent / "impl.py"


def _default_output() -> Path:
    return _repo_root() / "runtime" / "outputs" / "loan_comparison_flourish.mp4"


def _to_abs_output(path: str | Path | None) -> Path:
    if not path:
        return _default_output()
    candidate = Path(path).expanduser()
    if candidate.is_absolute():
        return candidate
    return _repo_root() / candidate


# ── public API ──────────────────────────────────────────────────────────────

def generate_loan_animation(
    output_file: str | Path | None = None,
    width: int | None = None,
    height: int | None = None,
    duration: int | None = None,
    fps: int | None = None,
    loan_amount: float | None = None,
    annual_rate: float | None = None,
    loan_years: int | None = None,
    progress_callback: Callable[[int, int], None] | None = None,
) -> Path:
    """Render animation by running impl.py as a subprocess."""
    script_path = _impl_script()
    if not script_path.exists():
        raise RuntimeError(f"animation implementation not found: {script_path}")

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
    if loan_amount is not None:
        env["VIDEO_LOAN_AMOUNT"] = str(float(loan_amount))
    if annual_rate is not None:
        env["VIDEO_ANNUAL_RATE"] = str(float(annual_rate))
    if loan_years is not None:
        env["VIDEO_LOAN_YEARS"] = str(int(loan_years))

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
            "loan animation render failed:\n"
            f"stdout:\n{completed.stdout}\n\n"
            f"stderr:\n{completed.stderr}"
        )

    if progress_callback:
        progress_callback(1, 1)

    if not output_path.exists() or output_path.stat().st_size <= 0:
        raise RuntimeError(f"video generation failed, output empty: {output_path}")

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
        progress_callback: Callable[[int, int], None] | None = None,
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
                progress_callback=progress_callback,
            )
        except Exception as exc:
            raise RenderError(f"failed to generate animation: {exc}", step="generate_animation") from exc


if __name__ == "__main__":
    main()
