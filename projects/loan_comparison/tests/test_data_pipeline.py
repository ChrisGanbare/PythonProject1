"""Loan data pipeline helpers."""

from __future__ import annotations

from loan_comparison.data.pipeline import loan_params_for_viz, loan_summary_for_charts
from loan_comparison.models.loan import LoanData


def test_loan_params_for_viz() -> None:
    loan = LoanData(loan_amount=2_000_000, annual_rate=0.04, loan_years=20)
    p = loan_params_for_viz(loan)
    assert p["loan_amount"] == 2_000_000
    assert p["loan_years"] == 20
    s = loan_summary_for_charts(loan)
    assert "computed" in s
    assert "equal_interest" in s["computed"]
