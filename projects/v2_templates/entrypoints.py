"""v2 模板渲染入口"""

from __future__ import annotations

import logging
from typing import Any

from core.v2_renderer import run_v2_render

logger = logging.getLogger(__name__)


def run_render(
    template: str = "bar_chart_race",
    data: dict[str, Any] | None = None,
    brand: str = "default",
    platform: str = "bilibili",
    **kwargs,
) -> dict[str, Any]:
    """
    v2.2 模板渲染入口
    
    Args:
        template: 模板名称
        data: 图表数据
        brand: 品牌主题
        platform: 目标平台
        **kwargs: 其他参数
        
    Returns:
        渲染结果
    """
    if data is None:
        return {
            "success": False,
            "error": "缺少数据参数",
            "message": "请提供 data 参数（图表数据）"
        }
    
    return run_v2_render(
        template=template,
        data=data,
        brand=brand,
        platform=platform,
        **kwargs
    )
