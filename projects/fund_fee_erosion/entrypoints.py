"""Callable entrypoints exposed for the root scheduler."""

from __future__ import annotations

from fund_fee_erosion.models.calculator import FundParams
from fund_fee_erosion.renderer.animation import generate_fund_animation


def run_smoke_check() -> dict:
    """Quick validation: compute summary without ffmpeg/OpenAI."""
    params = FundParams(principal=1_000_000, gross_return=0.08, years=30)
    summary = params.get_summary()

    result = {
        k: {
            "final_value_wan": v["final_value_wan"],
            "fee_drag_wan": v["fee_drag_wan"],
            "fee_drag_pct": v["fee_drag_pct"],
        }
        for k, v in summary.items()
    }
    print("Smoke check passed:")
    for k, v in result.items():
        print(f"  {k}: 终值 {v['final_value_wan']:.1f}万，"
              f"侵蚀 {v['fee_drag_wan']:.1f}万（{v['fee_drag_pct']:.1f}%）")
    return result


def run_fund_animation(
    output_file: str | None = None,
    width: int | None = None,
    height: int | None = None,
    duration: int | None = None,
    fps: int | None = None,
    principal: float | None = None,
    gross_return: float | None = None,
    years: int | None = None,
) -> None:
    """Generate the fund fee erosion animation video."""
    generate_fund_animation(
        output_file=output_file,
        width=width,
        height=height,
        duration=duration,
        fps=fps,
        principal=principal,
        gross_return=gross_return,
        years=years,
    )
