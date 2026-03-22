"""基金项目内容规划适配器。"""

from __future__ import annotations

from shared.content.planner import build_content_plan
from shared.content.schemas import ContentBrief, ContentPlan


def build_fund_content_plan(request, summary: dict[str, dict]) -> ContentPlan:
    """将基金费用侵蚀摘要转换为统一内容方案。"""
    zero_value = summary["zero"]["final_value_wan"]
    active_value = summary["active"]["final_value_wan"]
    drag_wan = summary["active"]["fee_drag_wan"]
    drag_pct = summary["active"]["fee_drag_pct"]

    brief = ContentBrief(
        topic="基金手续费复利侵蚀",
        platform=request.platform.value,
        style=request.style,
        variant=request.content_variant,
        total_duration=request.video_duration,
        hook_fact=(
            f"同样收益率下，{request.years}年里多1.5%年费，"
            f"最终资产会少多少？"
        ),
        setup_fact=(
            f"无费用基准终值约{zero_value:.1f}万，"
            f"主动基金场景终值约{active_value:.1f}万。"
        ),
        climax_fact=f"长期下来会少掉约{drag_wan:.1f}万，财富侵蚀比例接近{drag_pct:.1f}%。",
        conclusion_fact="低费率长期更有优势，费用差距会被复利不断放大。",
        call_to_action="看收益时别只看涨幅，也要看费用结构。",
        tags=["基金", "复利", "费率", request.platform.value, request.style.value],
    )
    return build_content_plan(brief)

