from __future__ import annotations

from fund_fee_erosion.data.pipeline import fund_params_for_viz
from fund_fee_erosion.models.calculator import FundParams
from shared.library.render_manifest import compute_fund_reproducibility_fingerprint


def test_fund_params_and_fingerprint() -> None:
    p = FundParams(principal=500_000, gross_return=0.07, years=20)
    d = fund_params_for_viz(p)
    assert d["principal"] == 500_000
    fp = compute_fund_reproducibility_fingerprint(
        fund=d,
        video_config={"width": 1080, "height": 1920, "fps": 30, "total_duration": 30, "dpi": 100, "bitrate": 8000, "preset": "medium", "crf": 20},
    )
    assert len(fp) == 64
