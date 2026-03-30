"""短视频内容节奏分配。"""

from __future__ import annotations

from shared.ai.content.schemas import ContentVariant

def build_story_windows(total_duration: int, variant: ContentVariant = ContentVariant.STANDARD) -> list[tuple[float, float]]:
    """根据总时长输出四段内容节拍时间窗。"""
    total = float(total_duration)

    if variant == ContentVariant.SHORT:
        hook_end = min(2.5, round(total * 0.2, 2))
        setup_end = max(hook_end + 1.5, round(total * 0.45, 2))
        climax_end = max(setup_end + 1.5, round(total * 0.72, 2))
    else:
        hook_end = min(3.0, round(total * 0.18, 2))
        setup_end = max(hook_end + 2.0, round(total * 0.52, 2))
        climax_end = max(setup_end + 2.0, round(total * 0.78, 2))

    if climax_end >= total:
        climax_end = max(setup_end + 1.0, total - 1.0)
    if setup_end >= climax_end:
        setup_end = max(hook_end + 1.0, climax_end - 1.0)
    if hook_end >= setup_end:
        hook_end = max(1.0, setup_end - 1.0)

    return [
        (0.0, round(hook_end, 2)),
        (round(hook_end, 2), round(setup_end, 2)),
        (round(setup_end, 2), round(climax_end, 2)),
        (round(climax_end, 2), round(total, 2)),
    ]

