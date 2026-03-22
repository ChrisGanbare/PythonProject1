"""Loan domain adapter for screenplay planning."""

from __future__ import annotations

from shared.content.schemas import ContentStyle


def build_loan_screenplay_topic(
    *,
    topic: str | None,
    loan_amount: float,
    loan_years: int,
) -> str:
    if topic:
        return topic
    return f"{loan_amount / 10000:.0f}万贷款 {loan_years}年还款方式对比"


def build_loan_screenplay_context(summary: dict, *, style: ContentStyle | str, platform: str) -> dict[str, str]:
    equal_interest = summary["equal_interest"]["total_interest"] / 10_000
    equal_principal = summary["equal_principal"]["total_interest"] / 10_000
    diff = summary["comparison"]["interest_difference"] / 10_000
    cheaper = summary["comparison"]["which_is_cheaper"]
    style_value = style.value if hasattr(style, "value") else str(style)
    return {
        "platform": platform,
        "style": style_value,
        "equal_interest_text": f"等额本息总利息约 {equal_interest:.1f} 万",
        "equal_principal_text": f"等额本金总利息约 {equal_principal:.1f} 万",
        "interest_difference_text": f"{diff:.1f} 万",
        "which_is_cheaper": cheaper,
        "loan_amount_text": f"{summary['loan_amount'] / 10000:.0f}万",
        "loan_years_text": f"{summary['loan_years']}年",
    }

