"""Content planner adapter for my_tutor."""

from __future__ import annotations

from shared.content.planner import build_content_plan
from shared.content.schemas import ContentBrief, ContentPlan


def build_my_tutor_content_plan(request, summary: dict | None = None) -> ContentPlan:
    del summary
    brief = ContentBrief(
        topic="当前项目的介绍",
        platform=request.platform.value,
        style=request.style,
        variant=request.content_variant,
        total_duration=request.video_duration,
        hook_fact="用一句话抛出本期核心问题。",
        setup_fact="在这里放入关键数据背景。",
        climax_fact="在这里放入最值得放大的高潮数字。",
        conclusion_fact="在这里放入一句话结论。",
        call_to_action="补一句适合平台的行动建议。",
        tags=["my_tutor", request.platform.value, request.style.value],
    )
    return build_content_plan(brief)
