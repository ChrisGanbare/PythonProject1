"""
柱状图竞赛模板 - Bar Chart Race

 Flourish 风格的时间序列数据动态展示
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


@register_template("bar_chart_race")
class BarChartRaceTemplate(VideoTemplate):
    """
    柱状图竞赛模板
    
    适用于：
    - 排名变化展示
    - 时间序列对比
    - 竞争态势可视化
    
    数据要求:
    - date: 日期列
    - category: 分类列
    - value: 数值列
    """
    
    def _define_schema(self) -> DataSchema:
        return DataSchema(
            required_columns=["date", "category", "value"]
            # 不强制类型检查，允许更灵活的数据输入
        )
    
    def build(self, data: DataSource, style: BrandStyle = None) -> VideoManifest:
        """构建柱状图竞赛视频清单"""
        self.set_data(data)
        if style:
            self.set_style(style)
        
        # 生成场景
        scenes = self._build_scenes()
        
        # 生成转场
        transitions = self._build_transitions(len(scenes))
        
        # 计算数据哈希
        data_hash = hashlib.md5(
            str(self.data.to_dict()).encode()
        ).hexdigest()[:8]
        
        return VideoManifest(
            template_name="bar_chart_race",
            data_hash=data_hash,
            brand_style_name=style.name if style else "default",
            scenes=scenes,
            transitions=transitions,
            metadata={
                "total_dates": len(self.data["date"].unique()),
                "total_categories": len(self.data["category"].unique()),
                "value_range": (
                    self.data["value"].min(),
                    self.data["value"].max()
                )
            }
        )
    
    def _build_scenes(self) -> List[dict]:
        """构建场景列表"""
        scenes = []
        
        # 按日期分组
        dates = sorted(self.data["date"].unique())
        
        for i, date in enumerate(dates):
            date_data = self.data[self.data["date"] == date]
            
            # 获取前 N 名
            top_n = date_data.nlargest(10, "value")
            
            scene = {
                "id": f"scene_{i}",
                "title": str(date),
                "type": "bar_chart",
                "data": {
                    "categories": top_n["category"].tolist(),
                    "values": top_n["value"].tolist(),
                    "labels": top_n.apply(
                        lambda row: f"{row['category']}: {row['value']}", 
                        axis=1
                    ).tolist()
                },
                "config": {
                    "orientation": "h",
                    "show_labels": True,
                    "show_values": True,
                    "sort_by": "value",
                    "sort_order": "desc"
                },
                "duration": self.config.animation_duration,
                "camera": {
                    "position": [0, 0, 0],
                    "zoom": 1.0,
                    "rotation": 0
                }
            }
            
            scenes.append(scene)
        
        return scenes
    
    def _build_transitions(self, scene_count: int) -> List[dict]:
        """构建转场列表"""
        transitions = []
        
        for i in range(scene_count - 1):
            transition = {
                "from_scene": f"scene_{i}",
                "to_scene": f"scene_{i+1}",
                "type": self.config.transition_type,
                "duration": self.config.transition_duration,
                "easing": self.config.easing
            }
            transitions.append(transition)
        
        return transitions


# 注册其他柱状图模板
@register_template("bar_chart_horizontal")
class HorizontalBarTemplate(VideoTemplate):
    """水平柱状图模板"""
    
    def _define_schema(self) -> DataSchema:
        return DataSchema(
            required_columns=["category", "value"]
        )
    
    def build(self, data: DataSource, style: BrandStyle = None) -> VideoManifest:
        self.set_data(data)
        
        return VideoManifest(
            template_name="bar_chart_horizontal",
            data_hash="static",
            brand_style_name=style.name if style else "default",
            scenes=[{
                "id": "scene_0",
                "type": "horizontal_bar",
                "data": {
                    "categories": self.data["category"].tolist(),
                    "values": self.data["value"].tolist()
                }
            }],
            transitions=[]
        )
