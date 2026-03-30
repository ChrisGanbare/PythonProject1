"""
散点图模板 - Scatter Plot

关系与分布展示
"""

from typing import List
import pandas as pd
import hashlib

from .base import (
    VideoTemplate, 
    TemplateConfig, 
    DataSchema, 
    VideoManifest,
    register_template
)
from core.data.sources import DataSource
from core.brand.style import BrandStyle


@register_template("scatter_plot_dynamic")
class ScatterPlotTemplate(VideoTemplate):
    """
    动态散点图模板
    
    适用于：
    - 相关性分析
    - 分布展示
    - 异常值检测
    """
    
    def _define_schema(self) -> DataSchema:
        return DataSchema(
            required_columns=["x", "y", "category"],
            optional_columns=["size", "color"]
        )
    
    def build(self, data: DataSource, style: BrandStyle = None) -> VideoManifest:
        self.set_data(data)
        if style:
            self.set_style(style)
        
        return VideoManifest(
            template_name="scatter_plot_dynamic",
            data_hash=hashlib.md5(str(self.data.to_dict()).encode()).hexdigest()[:8],
            brand_style_name=style.name if style else "default",
            scenes=[{
                "id": "scene_0",
                "type": "scatter",
                "data": {
                    "x": self.data["x"].tolist(),
                    "y": self.data["y"].tolist(),
                    "categories": self.data["category"].tolist(),
                    "sizes": self.data.get("size", [10] * len(self.data)).tolist(),
                    "colors": self.data.get("color", ["blue"] * len(self.data)).tolist()
                },
                "config": {
                    "show_grid": True,
                    "show_legend": True,
                    "bubble_mode": "size" in self.data.columns
                }
            }],
            transitions=[]
        )


@register_template("bubble_chart")
class BubbleChartTemplate(VideoTemplate):
    """气泡图模板（带大小的散点图）"""
    
    def _define_schema(self) -> DataSchema:
        return DataSchema(
            required_columns=["x", "y", "size", "category"]
        )
    
    def build(self, data: DataSource, style: BrandStyle = None) -> VideoManifest:
        self.set_data(data)
        
        return VideoManifest(
            template_name="bubble_chart",
            data_hash="bubble",
            brand_style_name=style.name if style else "default",
            scenes=[{
                "id": "scene_0",
                "type": "bubble",
                "data": {
                    "x": self.data["x"].tolist(),
                    "y": self.data["y"].tolist(),
                    "sizes": self.data["size"].tolist(),
                    "categories": self.data["category"].tolist()
                }
            }]
        )
