"""
模板引擎 - Flourish 风格的视频模板系统

提供预定义的视频模板，用户只需提供数据即可生成专业视频。

使用示例:
    ```python
    from core.templates import get_template
    from core.data.sources import CSVSource
    from core.brand import get_theme
    
    # 获取模板
    template = get_template("bar_chart_race")
    
    # 加载数据
    data = CSVSource("sales_data.csv")
    
    # 选择品牌主题
    brand = get_theme("corporate")
    
    # 构建视频清单
    manifest = template.build(data, brand)
    ```
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
    """
    模板配置类
    
    用于配置模板的各项参数，包括视频规格、图表样式、动画效果等。
    
    属性:
        name: 模板名称
        category: 模板分类 (如 bar_chart, line_chart 等)
        description: 模板描述
        width: 视频宽度 (像素)，默认 1920
        height: 视频高度 (像素)，默认 1080
        fps: 帧率，默认 30
        duration: 视频总时长 (秒)
        chart_type: 图表类型
        show_legend: 是否显示图例
        show_grid: 是否显示网格
        show_annotations: 是否显示标注
        animation_enabled: 是否启用动画
        animation_duration: 动画时长 (秒)
        easing: 缓动函数名称
        transition_type: 转场类型
        transition_duration: 转场时长 (秒)
        extra: 额外配置 (字典)
    """
    
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
    """
    数据模式定义
    
    用于验证输入数据是否符合模板要求。
    
    属性:
        required_columns: 必需的列名列表
        optional_columns: 可选的列名列表
        column_types: 列类型定义 (列名 -> 类型)
    
    使用示例:
        ```python
        schema = DataSchema(
            required_columns=["date", "category", "value"],
            column_types={"date": "datetime", "value": "number"}
        )
        
        is_valid, errors = schema.validate(dataframe)
        ```
    """
    
    required_columns: List[str] = field(default_factory=list)
    optional_columns: List[str] = field(default_factory=list)
    column_types: Dict[str, str] = field(default_factory=dict)
    
    def validate(self, df: pd.DataFrame) -> tuple[bool, List[str]]:
        """
        验证数据是否符合模式要求
        
        Args:
            df: 待验证的 DataFrame
            
        Returns:
            tuple[bool, List[str]]: (是否通过验证，错误信息列表)
            
        验证逻辑:
            1. 检查必需列是否存在
            2. 检查列类型是否匹配 (宽松模式)
               - number: 接受任何数值类型
               - datetime: 接受 datetime 或 object (字符串日期)
        """
        errors = []
        
        # 检查必需列
        missing_cols = set(self.required_columns) - set(df.columns)
        if missing_cols:
            errors.append(f"缺少必需列：{missing_cols}")
        
        # 检查类型 (宽松模式)
        for col, expected_type in self.column_types.items():
            if col in df.columns:
                actual_type = str(df[col].dtype)
                
                # 宽松的数字类型检查
                if expected_type == "number":
                    if not pd.api.types.is_numeric_dtype(df[col]):
                        errors.append(f"列 '{col}' 应为数值类型，实际为 {actual_type}")
                # 宽松的日期类型检查
                elif expected_type == "datetime":
                    if not (pd.api.types.is_datetime64_any_dtype(df[col]) or 
                           actual_type == "object"):
                        errors.append(f"列 '{col}' 应为日期类型，实际为 {actual_type}")
        
        return len(errors) == 0, errors


class VideoTemplate(ABC):
    """
    视频模板基类 (抽象类)
    
    所有模板都必须继承此类并实现抽象方法。
    
    模板生命周期:
        1. 初始化：创建模板实例
        2. 设置数据：调用 set_data() 加载并验证数据
        3. 设置品牌：调用 set_style() 设置品牌风格
        4. 构建清单：调用 build() 生成视频清单
    
    使用示例:
        ```python
        class MyTemplate(VideoTemplate):
            def _define_schema(self) -> DataSchema:
                return DataSchema(required_columns=["date", "value"])
            
            def build(self, data, style) -> VideoManifest:
                # 实现构建逻辑
                pass
        ```
    """
    
    def __init__(self, config: Optional[TemplateConfig] = None):
        """
        初始化模板
        
        Args:
            config: 模板配置，None 则使用默认配置
        """
        self.config = config or TemplateConfig()
        self.data_schema = self._define_schema()
        self._data: Optional[pd.DataFrame] = None
        self._brand_style: Optional[BrandStyle] = None
    
    @abstractmethod
    def _define_schema(self) -> DataSchema:
        """
        定义数据模式 (抽象方法，子类必须实现)
        
        Returns:
            DataSchema: 数据模式定义
            
        实现示例:
            ```python
            def _define_schema(self) -> DataSchema:
                return DataSchema(
                    required_columns=["date", "category", "value"]
                )
            ```
        """
        pass
    
    @abstractmethod
    def build(self, data: DataSource, style: Optional[BrandStyle] = None) -> 'VideoManifest':
        """
        构建视频清单 (抽象方法，子类必须实现)
        
        Args:
            data: 数据源
            style: 品牌风格 (可选)
            
        Returns:
            VideoManifest: 视频清单 (包含场景、转场等信息)
        """
        pass
    
    def set_data(self, data: DataSource) -> 'VideoTemplate':
        """
        设置数据源
        
        Args:
            data: 数据源对象
            
        Returns:
            self: 支持链式调用
            
        Raises:
            ValueError: 数据验证失败时抛出
            
        处理流程:
            1. 从数据源加载 DataFrame
            2. 使用数据模式验证数据
            3. 验证失败则抛出异常
            4. 验证成功则保存数据
        """
        df = data.load()
        
        # 验证数据
        is_valid, errors = self.data_schema.validate(df)
        if not is_valid:
            raise ValueError(f"数据验证失败：{'; '.join(errors)}")
        
        self._data = df
        return self
    
    def set_style(self, style: BrandStyle) -> 'VideoTemplate':
        """
        设置品牌风格
        
        Args:
            style: 品牌风格对象
            
        Returns:
            self: 支持链式调用
        """
        self._brand_style = style
        return self
    
    @property
    def data(self) -> Optional[pd.DataFrame]:
        """获取当前数据"""
        return self._data
    
    @property
    def brand_style(self) -> Optional[BrandStyle]:
        """获取当前品牌风格"""
        return self._brand_style


@dataclass
class VideoManifest:
    """
    视频清单
    
    包含渲染视频所需的所有信息，包括场景、转场、音频等。
    
    属性:
        template_name: 使用的模板名称
        data_hash: 数据哈希值 (用于缓存和版本控制)
        brand_style_name: 使用的品牌主题名称
        scenes: 场景列表 (每个场景包含图表类型、数据、配置等)
        transitions: 转场列表 (定义场景间的过渡效果)
        audio: 音频配置 (可选)
        metadata: 元数据 (包含统计信息等)
    
    使用示例:
        ```python
        manifest = VideoManifest(
            template_name="bar_chart_race",
            data_hash="abc123",
            scenes=[...],
            transitions=[...]
        )
        
        # 转换为字典 (用于 JSON 序列化)
        config_dict = manifest.to_dict()
        ```
    """
    
    template_name: str
    data_hash: str
    brand_style_name: str
    scenes: List[Dict[str, Any]]
    transitions: List[Dict[str, Any]]
    audio: Optional[Dict[str, Any]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """
        转换为字典
        
        Returns:
            Dict[str, Any]: 字典格式的清单配置
            
        用途:
            - JSON 序列化
            - API 响应
            - 配置文件导出
        """
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
    """
    模板注册表
    
    用于管理和查找所有已注册的模板。
    采用单例模式，全局只有一个注册表实例。
    
    使用示例:
        ```python
        # 获取全局注册表
        registry = template_registry
        
        # 注册模板
        registry.register("my_template", MyTemplate)
        
        # 获取模板类
        TemplateClass = registry.get("my_template")
        
        # 创建模板实例
        template = registry.create("my_template", config)
        ```
    """
    
    def __init__(self):
        """初始化注册表"""
        self._templates: Dict[str, Type[VideoTemplate]] = {}
    
    def register(self, name: str, template_class: Type[VideoTemplate]):
        """
        注册模板类
        
        Args:
            name: 模板名称 (唯一标识符)
            template_class: 模板类 (VideoTemplate 的子类)
        """
        self._templates[name] = template_class
    
    def get(self, name: str) -> Optional[Type[VideoTemplate]]:
        """
        获取模板类
        
        Args:
            name: 模板名称
            
        Returns:
            模板类，如果不存在则返回 None
        """
        return self._templates.get(name)
    
    def list_templates(self) -> Dict[str, Type[VideoTemplate]]:
        """
        列出所有已注册的模板
        
        Returns:
            Dict[str, Type[VideoTemplate]]: 模板名称到模板类的映射
        """
        return self._templates.copy()
    
    def create(self, name: str, config: Optional[TemplateConfig] = None) -> Optional[VideoTemplate]:
        """
        创建模板实例
        
        Args:
            name: 模板名称
            config: 模板配置
            
        Returns:
            模板实例，如果模板不存在则返回 None
        """
        template_class = self.get(name)
        if not template_class:
            return None
        return template_class(config)


# 全局注册表实例 (单例模式)
template_registry = TemplateRegistry()


def register_template(name: str):
    """
    装饰器：注册模板类
    
    使用装饰器可以自动将模板类注册到全局注册表中。
    
    使用示例:
        ```python
        @register_template("bar_chart_race")
        class BarChartRaceTemplate(VideoTemplate):
            def _define_schema(self) -> DataSchema:
                return DataSchema(required_columns=["date", "category", "value"])
            
            def build(self, data, style) -> VideoManifest:
                # 实现构建逻辑
                pass
        ```
    
    Args:
        name: 模板名称
        
    Returns:
        装饰器函数
    """
    def decorator(cls: Type[VideoTemplate]) -> Type[VideoTemplate]:
        template_registry.register(name, cls)
        return cls
    return decorator
