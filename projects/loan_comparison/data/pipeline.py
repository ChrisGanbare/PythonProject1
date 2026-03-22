"""P1: single entry for loan numbers feeding charts + fingerprint alignment."""

from __future__ import annotations

from typing import Any

from loan_comparison.models.loan import LoanData


def loan_params_for_viz(loan: LoanData) -> dict[str, float | int]:
    """Stable loan triple for cache keys and matplotlib env (matches manifest `loan`)."""
    return {
        "loan_amount": float(loan.loan_amount),
        "annual_rate": float(loan.annual_rate),
        "loan_years": int(loan.loan_years),
    }


def loan_summary_for_charts(loan: LoanData) -> dict[str, Any]:
    """Full summary for labels / B-roll copy; charts should use the same LoanData instance."""
    return {
        **loan_params_for_viz(loan),
        "computed": loan.get_summary(),
    }
