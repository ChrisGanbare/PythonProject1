"""
动态折线图模板 - Animated Line Chart

时间序列趋势展示
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


@register_template("line_chart_animated")
class LineChartAnimatedTemplate(VideoTemplate):
    """
    动态折线图模板
    
    适用于：
    - 趋势展示
    - 多系列对比
    - 增长率可视化
    """
    
    def _define_schema(self) -> DataSchema:
        return DataSchema(
            required_columns=["date", "series", "value"],
            column_types={
                "date": "datetime",
                "value": "number"
            }
        )
    
    def build(self, data: DataSource, style: BrandStyle = None) -> VideoManifest:
        self.set_data(data)
        if style:
            self.set_style(style)
        
        scenes = self._build_scenes()
        transitions = self._build_transitions(len(scenes))
        
        return VideoManifest(
            template_name="line_chart_animated",
            data_hash=hashlib.md5(str(self.data.to_dict()).encode()).hexdigest()[:8],
            brand_style_name=style.name if style else "default",
            scenes=scenes,
            transitions=transitions
        )
    
    def _build_scenes(self) -> List[dict]:
        scenes = []
        dates = sorted(self.data["date"].unique())
        
        for i, date in enumerate(dates):
            date_data = self.data[self.data["date"] == date]
            
            # 累积数据到当前日期
            cumulative = self.data[self.data["date"] <= date]
            
            scene = {
                "id": f"scene_{i}",
                "title": str(date),
                "type": "line_chart",
                "data": {
                    "series": cumulative["series"].unique().tolist(),
                    "dates": cumulative["date"].tolist(),
                    "values": cumulative["value"].tolist()
                },
                "config": {
                    "show_points": True,
                    "show_grid": True,
                    "smooth": True
                },
                "duration": self.config.animation_duration
            }
            
            scenes.append(scene)
        
        return scenes
    
    def _build_transitions(self, scene_count: int) -> List[dict]:
        return [
            {
                "from_scene": f"scene_{i}",
                "to_scene": f"scene_{i+1}",
                "type": "slide",
                "duration": self.config.transition_duration
            }
            for i in range(scene_count - 1)
        ]


@register_template("area_chart_stacked")
class StackedAreaTemplate(VideoTemplate):
    """堆叠面积图模板"""
    
    def _define_schema(self) -> DataSchema:
        return DataSchema(
            required_columns=["date", "category", "value"]
        )
    
    def build(self, data: DataSource, style: BrandStyle = None) -> VideoManifest:
        self.set_data(data)
        
        return VideoManifest(
            template_name="area_chart_stacked",
            data_hash="stacked",
            brand_style_name=style.name if style else "default",
            scenes=[{
                "id": "scene_0",
                "type": "stacked_area",
                "data": {
                    "dates": self.data["date"].tolist(),
                    "categories": self.data["category"].unique().tolist(),
                    "values": self.data["value"].tolist()
                }
            }],
            transitions=[]
        )
