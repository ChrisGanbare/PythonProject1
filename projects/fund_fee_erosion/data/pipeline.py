"""P1: stable fund triple for fingerprints and matplotlib env."""

from __future__ import annotations

from fund_fee_erosion.models.calculator import FundParams


def fund_params_for_viz(params: FundParams) -> dict[str, float | int]:
    return {
        "principal": float(params.principal),
        "gross_return": float(params.gross_return),
        "years": int(params.years),
    }
