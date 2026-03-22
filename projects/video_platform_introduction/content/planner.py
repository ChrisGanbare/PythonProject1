"""Content planner adapter for video_platform_introduction."""

from __future__ import annotations

from shared.content.planner import build_content_plan
from shared.content.schemas import ContentBrief, ContentPlan


def build_video_platform_introduction_content_plan(request, summary: dict | None = None) -> ContentPlan:
    del summary
    topic = (getattr(request, "topic", None) or "").strip() or "Video Platform Introduction"
    brief = ContentBrief(
        topic=topic,
        platform=request.platform.value,
        style=request.style,
        variant=request.content_variant,
        total_duration=request.video_duration,
        hook_fact="30 秒看懂这个平台，为什么适合中文创作者快速做出平台介绍视频。",
        setup_fact="从模板化生产、scene 级调度到字幕与封面输出，交代平台的核心工作流。",
        climax_fact="把自动字幕、平台适配和批量渲染串成一个真正能提效的创作闭环。",
        conclusion_fact="用一支平台介绍片，快速讲清产品价值、适用人群与下一步动作。",
        call_to_action="如果你要为产品或团队快速做介绍视频，现在就先试一轮预览流程。",
        tags=["video_platform_introduction", topic, request.platform.value, request.style.value],
    )
    return build_content_plan(brief)
