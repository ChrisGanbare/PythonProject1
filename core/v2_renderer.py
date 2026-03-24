"""
v2.2 通用模板渲染器

使用新的模板引擎、品牌系统、平台规格直接生成视频
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


def render_v2_template(
    template_name: str,
    data: dict[str, Any],
    brand: str = "default",
    platform: str = "bilibili",
    output_path: str | None = None,
) -> str:
    """
    使用 v2.2 模板引擎渲染视频
    
    Args:
        template_name: 模板名称 (bar_chart_race, line_chart_animated 等)
        data: 图表数据
        brand: 品牌主题名称
        platform: 目标平台
        output_path: 输出路径
        
    Returns:
        输出文件路径
    """
    """
    使用 v2.2 模板引擎渲染视频
    
    Args:
        template_name: 模板名称 (bar_chart_race, line_chart_animated 等)
        data: 图表数据
        brand: 品牌主题名称
        platform: 目标平台
        output_path: 输出路径
        
    Returns:
        输出文件路径
    """
    from core.templates import get_template
    from core.data.sources import InlineDataSource
    from core.brand import get_theme
    from core.render import create_renderer
    
    # 1. 获取模板
    template = get_template(template_name)
    if not template:
        raise ValueError(f"模板不存在：{template_name}")
    
    # 2. 加载数据
    data_source = InlineDataSource(data)
    
    # 3. 获取品牌主题
    brand_style = get_theme(brand)
    if not brand_style:
        brand_style = get_theme("default")
    
    # 4. 构建视频清单
    manifest = template.build(data_source, brand_style)
    
    # 5. 渲染视频
    renderer = create_renderer(backend="plotly")
    
    if output_path is None:
        output_path = "output.mp4"
    
    video_path = renderer.render(manifest.to_dict(), output_path)
    
    logger.info(f"视频已生成：{video_path}")
    return video_path


def run_v2_render(
    template: str,
    data: dict[str, Any],
    brand: str = "default",
    platform: str = "bilibili",
    **kwargs,
) -> dict[str, Any]:
    """
    v2.2 渲染入口函数 (供 AI 编译器调用)
    
    Args:
        template: 模板名称
        data: 图表数据
        brand: 品牌主题
        platform: 目标平台
        **kwargs: 其他参数
        
    Returns:
        渲染结果
    """
    try:
        output_path = render_v2_template(
            template_name=template,
            data=data,
            brand=brand,
            platform=platform,
        )
        
        return {
            "success": True,
            "output_path": output_path,
            "message": f"视频已生成：{output_path}"
        }
        
    except Exception as e:
        logger.exception("v2 渲染失败")
        return {
            "success": False,
            "error": str(e),
            "message": f"渲染失败：{e}"
        }
