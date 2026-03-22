"""贷款项目内容规划适配器。"""

from __future__ import annotations

from shared.content.planner import build_content_plan
from shared.content.schemas import ContentBrief, ContentPlan


def build_loan_content_plan(request, summary: dict) -> ContentPlan:
    """将贷款业务摘要转换为统一内容方案。"""
    equal_interest = summary["equal_interest"]["total_interest"] / 10_000
    equal_principal = summary["equal_principal"]["total_interest"] / 10_000
    saved = summary["comparison"]["interest_difference"] / 10_000
    cheaper = summary["comparison"]["which_is_cheaper"]

    brief = ContentBrief(
        topic="贷款还款方式对比",
        platform=request.platform.value,
        style=request.style,
        variant=request.content_variant,
        total_duration=request.video_duration,
        hook_fact=(
            f"{request.loan_amount / 10000:.0f}万贷款，{request.loan_years}年下来，"
            f"两种还款方式到底差多少利息？"
        ),
        setup_fact=(
            f"等额本息总利息约{equal_interest:.1f}万，"
            f"等额本金总利息约{equal_principal:.1f}万。"
        ),
        climax_fact=f"差额被拉大到约{saved:.1f}万，这就是长期现金流选择的代价。",
        conclusion_fact=f"如果现金流允许，{cheaper}通常更省总利息。",
        call_to_action="先看自己的现金流，再决定还款方式。",
        tags=["贷款", "房贷", request.platform.value, request.style.value],
    )
    return build_content_plan(brief)

