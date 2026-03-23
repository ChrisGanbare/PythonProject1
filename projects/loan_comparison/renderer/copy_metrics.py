"""Data-driven copy helpers for the loan comparison renderer."""

from __future__ import annotations


def format_amount_short(amount: float) -> str:
    value = float(amount)
    if abs(value) >= 100000000:
        return f"{value / 100000000:.2f}亿"
    if abs(value) >= 10000:
        scaled = value / 10000
        if abs(scaled - round(scaled)) < 0.05:
            return f"{scaled:.0f}万"
        return f"{scaled:.1f}万"
    return f"{value:.0f}元"


def format_amount_full(amount: float) -> str:
    value = float(amount)
    if abs(value) >= 10000:
        return f"{value / 10000:.1f} 万元"
    return f"{value:.0f} 元"


def format_rate_percent(rate: float) -> str:
    return f"{float(rate) * 100:.2f}".rstrip("0").rstrip(".") + "%"


def format_term_label(years: int) -> str:
    total_months = int(years) * 12
    return f"{int(years)}年 / {total_months}期"


def build_loan_copy_metrics(
    *,
    loan_amount: float,
    annual_rate: float,
    loan_years: int,
    total_months: int,
    final_equal_interest: float,
    final_equal_principal: float,
    equal_interest_monthly: float,
    equal_principal_first_month: float,
    equal_principal_last_month: float,
) -> dict[str, str | float]:
    interest_gap = max(0.0, float(final_equal_interest) - float(final_equal_principal))
    gap_pct = (interest_gap / final_equal_interest * 100.0) if final_equal_interest > 0 else 0.0
    first_month_gap = float(equal_principal_first_month) - float(equal_interest_monthly)

    loan_amount_short = format_amount_short(loan_amount)
    annual_rate_label = format_rate_percent(annual_rate)
    term_label = format_term_label(loan_years)
    gap_wan_label = f"{interest_gap / 10000:.1f}万"
    gap_pct_label = f"{gap_pct:.1f}%"
    first_month_gap_label = format_amount_short(first_month_gap)

    return {
        "loan_amount_short": loan_amount_short,
        "loan_amount_full": format_amount_full(loan_amount),
        "annual_rate_label": annual_rate_label,
        "term_label": term_label,
        "start_point_label": loan_amount_short,
        "interest_gap": interest_gap,
        "interest_gap_wan_label": gap_wan_label,
        "interest_gap_pct_label": gap_pct_label,
        "first_month_gap": first_month_gap,
        "first_month_gap_label": first_month_gap_label,
        "hook_text": f"同样{loan_amount_short}房贷，{loan_years}年可能多付{gap_wan_label}利息",
        "summary_text": f"月供稳定和总利息更低，往往不能同时拿到",
        "conclusion_title": f"总利息差 {gap_wan_label}",
        "conclusion_body": f"等额本金少付约{gap_wan_label}，约省{gap_pct_label}；代价是首月多还{first_month_gap_label}",
        "accent_label": "现金流扛得住前期压力，优先看等额本金；更在意月供稳定，再看等额本息",
        "footer_question": f"{loan_years}年后，谁为利息多付出一辆车的钱？",
        "full_interest_label": f"{loan_years}年总利息",
        "monthly_reference_label": f"月供参考（第1期 / 第{total_months}期）",
        "equal_interest_monthly_label": f"{equal_interest_monthly:.0f}元/月（固定）",
        "equal_principal_monthly_label": f"{equal_principal_first_month:.0f}元（首月）\n{equal_principal_last_month:.0f}元（末月）",
    }