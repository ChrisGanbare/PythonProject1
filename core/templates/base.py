"""
模板引擎 - Flourish 风格的视频模板系统

提供预定义的视频模板，用户只需提供数据即可生成专业视频
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Type
from pathlib import Path
import pandas as pd

from core.brand.style import BrandStyle
from core.data.sources import DataSource


@dataclass
class TemplateConfig:
    """模板配置"""
    
    # 基础配置
    name: str = "Default Template"
    category: str = "general"
    description: str = ""
    
    # 视频规格
    width: int = 1920
    height: int = 1080
    fps: int = 30
    duration: float = 10.0
    
    # 图表配置
    chart_type: str = "bar"
    show_legend: bool = True
    show_grid: bool = True
    show_annotations: bool = True
    
    # 动画配置
    animation_enabled: bool = True
    animation_duration: float = 2.0
    easing: str = "ease_in_out_quad"
    
    # 转场配置
    transition_type: str = "fade"
    transition_duration: float = 1.0
    
    # 额外配置
    extra: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DataSchema:
    """数据模式定义"""
    
    required_columns: List[str] = field(default_factory=list)
    optional_columns: List[str] = field(default_factory=list)
    column_types: Dict[str, str] = field(default_factory=dict)
    
    def validate(self, df: pd.DataFrame) -> tuple[bool, List[str]]:
        """验证数据是否符合模式"""
        errors = []
        
        # 检查必需列
        missing_cols = set(self.required_columns) - set(df.columns)
        if missing_cols:
            errors.append(f"Missing required columns: {missing_cols}")
        
        # 检查类型
        for col, expected_type in self.column_types.items():
            if col in df.columns:
                actual_type = str(df[col].dtype)
                if expected_type not in actual_type:
                    errors.append(f"Column '{col}' should be {expected_type}, got {actual_type}")
        
        return len(errors) == 0, errors


class VideoTemplate(ABC):
    """视频模板基类"""
    
    def __init__(self, config: Optional[TemplateConfig] = None):
        self.config = config or TemplateConfig()
        self.data_schema = self._define_schema()
        self._data: Optional[pd.DataFrame] = None
        self._brand_style: Optional[BrandStyle] = None
    
    @abstractmethod
    def _define_schema(self) -> DataSchema:
        """定义数据模式"""
        pass
    
    @abstractmethod
    def build(self, data: DataSource, style: Optional[BrandStyle] = None) -> 'VideoManifest':
        """构建视频清单"""
        pass
    
    def set_data(self, data: DataSource) -> 'VideoTemplate':
        """设置数据源"""
        df = data.load()
        
        # 验证数据
        is_valid, errors = self.data_schema.validate(df)
        if not is_valid:
            raise ValueError(f"Data validation failed: {'; '.join(errors)}")
        
        self._data = df
        return self
    
    def set_style(self, style: BrandStyle) -> 'VideoTemplate':
        """设置品牌风格"""
        self._brand_style = style
        return self
    
    @property
    def data(self) -> Optional[pd.DataFrame]:
        """获取数据"""
        return self._data
    
    @property
    def brand_style(self) -> Optional[BrandStyle]:
        """获取品牌风格"""
        return self._brand_style


@dataclass
class VideoManifest:
    """视频清单"""
    
    template_name: str
    data_hash: str
    brand_style_name: str
    scenes: List[Dict[str, Any]]
    transitions: List[Dict[str, Any]]
    audio: Optional[Dict[str, Any]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "template_name": self.template_name,
            "data_hash": self.data_hash,
            "brand_style_name": self.brand_style_name,
            "scenes": self.scenes,
            "transitions": self.transitions,
            "audio": self.audio,
            "metadata": self.metadata
        }


class TemplateRegistry:
    """模板注册表"""
    
    def __init__(self):
        self._templates: Dict[str, Type[VideoTemplate]] = {}
    
    def register(self, name: str, template_class: Type[VideoTemplate]):
        """注册模板"""
        self._templates[name] = template_class
    
    def get(self, name: str) -> Optional[Type[VideoTemplate]]:
        """获取模板类"""
        return self._templates.get(name)
    
    def list_templates(self) -> Dict[str, Type[VideoTemplate]]:
        """列出所有模板"""
        return self._templates.copy()
    
    def create(self, name: str, config: Optional[TemplateConfig] = None) -> Optional[VideoTemplate]:
        """创建模板实例"""
        template_class = self.get(name)
        if not template_class:
            return None
        return template_class(config)


# 全局注册表
template_registry = TemplateRegistry()


def register_template(name: str):
    """装饰器：注册模板"""
    def decorator(cls: Type[VideoTemplate]) -> Type[VideoTemplate]:
        template_registry.register(name, cls)
        return cls
    return decorator
