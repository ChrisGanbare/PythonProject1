from __future__ import annotations

from loan_comparison.renderer.copy_metrics import (
    build_loan_copy_metrics,
    format_amount_short,
    format_rate_percent,
    format_term_label,
)


def test_basic_formatters() -> None:
    assert format_amount_short(1_000_000) == "100万"
    assert format_rate_percent(0.045) == "4.5%"
    assert format_term_label(30) == "30年 / 360期"


def test_build_loan_copy_metrics_contains_data_driven_copy() -> None:
    metrics = build_loan_copy_metrics(
        loan_amount=1_000_000,
        annual_rate=0.045,
        loan_years=30,
        total_months=360,
        final_equal_interest=824_000,
        final_equal_principal=677_000,
        equal_interest_monthly=5067,
        equal_principal_first_month=6528,
        equal_principal_last_month=2786,
    )

    assert metrics["loan_amount_short"] == "100万"
    assert metrics["interest_gap_wan_label"] == "14.7万"
    assert "多付14.7万利息" in str(metrics["hook_text"])
    assert metrics["interest_gap_pct_label"] == "17.8%"
    assert "首月多还" in str(metrics["conclusion_body"])