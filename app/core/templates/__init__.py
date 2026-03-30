"""
模板注册表
"""

from .base import template_registry, VideoTemplate, TemplateConfig

# 导入所有模板实现以完成注册
from .bar_chart import BarChartRaceTemplate
from .line_chart import LineChartAnimatedTemplate
from .scatter_chart import ScatterPlotTemplate


def get_template(name: str, config: TemplateConfig = None) -> VideoTemplate:
    """获取模板实例"""
    return template_registry.create(name, config)


def list_templates() -> dict:
    """列出所有可用模板"""
    return template_registry.list_templates()


__all__ = [
    'get_template',
    'list_templates',
    'template_registry',
    'VideoTemplate',
    'TemplateConfig'
]
