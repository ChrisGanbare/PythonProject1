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


def run_api(host: str = "0.0.0.0", port: int = 8001) -> None:
    """Start FastAPI service for this project."""
    from fund_fee_erosion.api.main import start_api_server
    start_api_server(host=host, port=port)


def run_fund_animation(
    output_file: str | None = None,
    platform: str | None = None,
    quality: str | None = None,
    width: int | None = None,
    height: int | None = None,
    duration: int | None = None,
    fps: int | None = None,
    principal: float | None = None,
    gross_return: float | None = None,
    years: int | None = None,
    screenplay: dict | None = None,
) -> dict[str, str | None]:
    """Generate the fund fee erosion animation video.

    ``screenplay`` 可选：与贷款项目一致的 ``Screenplay`` JSON，用于后续绑定节拍/叙事；当前版本会先校验结构再成片。
    """
    screenplay_title = None
    if screenplay is not None:
        from shared.content.screenplay import Screenplay

        sp = Screenplay.model_validate(screenplay)
        screenplay_title = sp.title
        print(f"[fund_fee_erosion] 已接收剧本 JSON: {sp.title!r}（{len(sp.scenes)} scenes），成片管线将随版本深化消费。")

    out = generate_fund_animation(
        output_file=output_file,
        platform=platform,
        quality=quality,
        width=width,
        height=height,
        duration=duration,
        fps=fps,
        principal=principal,
        gross_return=gross_return,
        years=years,
    )
    return {
        "final_video_path": str(out),
        "screenplay_title": screenplay_title,
    }
