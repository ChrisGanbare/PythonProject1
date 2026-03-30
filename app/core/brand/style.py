"""
品牌系统 - 企业品牌定制能力

支持颜色、字体、Logo 等品牌元素
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from pathlib import Path


@dataclass
class ColorPalette:
    """颜色调色板"""
    
    # 主色
    primary: str = "#1f77b4"  # 蓝色
    secondary: str = "#ff7f0e"  # 橙色
    accent: str = "#2ca02c"  # 绿色
    
    # 基础色
    background: str = "#FFFFFF"
    text: str = "#000000"
    text_secondary: str = "#666666"
    
    # 图表颜色序列
    charts: List[str] = field(default_factory=lambda: [
        "#1f77b4",  # 蓝
        "#ff7f0e",  # 橙
        "#2ca02c",  # 绿
        "#d62728",  # 红
        "#9467bd",  # 紫
        "#8c564b",  # 棕
        "#e377c2",  # 粉
        "#7f7f7f",  # 灰
        "#bcbd22",  # 橄榄
        "#17becf"   # 青
    ])
    
    # 语义色
    success: str = "#28a745"
    warning: str = "#ffc107"
    error: str = "#dc3545"
    info: str = "#17a2b8"
    
    def to_dict(self) -> Dict[str, str]:
        """转换为字典"""
        return {
            "primary": self.primary,
            "secondary": self.secondary,
            "accent": self.accent,
            "background": self.background,
            "text": self.text,
            "text_secondary": self.text_secondary,
            "charts": self.charts,
            "success": self.success,
            "warning": self.warning,
            "error": self.error,
            "info": self.info
        }


@dataclass
class FontPair:
    """字体配对"""
    
    # 标题字体
    heading: str = "Arial Black"
    heading_weight: str = "bold"
    
    # 正文字体
    body: str = "Arial"
    body_weight: str = "normal"
    
    # 等宽字体（代码/数据）
    mono: str = "Courier New"
    
    # 字号
    heading_size: int = 48
    subheading_size: int = 32
    body_size: int = 18
    caption_size: int = 14
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "heading": {
                "family": self.heading,
                "weight": self.heading_weight,
                "size": self.heading_size
            },
            "body": {
                "family": self.body,
                "weight": self.body_weight,
                "size": self.body_size
            },
            "mono": {
                "family": self.mono,
                "size": 16
            },
            "subheading": {
                "size": self.subheading_size
            },
            "caption": {
                "size": self.caption_size
            }
        }


@dataclass
class BrandStyle:
    """品牌风格"""
    
    # 基础信息
    name: str = "Default"
    description: str = "Default brand style"
    
    # 颜色
    colors: ColorPalette = field(default_factory=ColorPalette)
    
    # 字体
    fonts: FontPair = field(default_factory=FontPair)
    
    # 品牌资产
    logo_path: Optional[str] = None
    watermark_path: Optional[str] = None
    favicon_path: Optional[str] = None
    
    # 布局
    margin: int = 40
    padding: int = 20
    border_radius: int = 8
    
    # 动画
    animation_duration: float = 1.0
    transition_duration: float = 0.5
    
    # 额外配置
    extra: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "name": self.name,
            "description": self.description,
            "colors": self.colors.to_dict(),
            "fonts": self.fonts.to_dict(),
            "logo_path": self.logo_path,
            "watermark_path": self.watermark_path,
            "margin": self.margin,
            "padding": self.padding,
            "border_radius": self.border_radius,
            "animation_duration": self.animation_duration,
            "transition_duration": self.transition_duration,
            "extra": self.extra
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BrandStyle':
        """从字典创建"""
        colors_data = data.pop("colors", {})
        fonts_data = data.pop("fonts", {})
        
        colors = ColorPalette(**colors_data) if colors_data else ColorPalette()
        fonts = FontPair(**fonts_data) if fonts_data else FontPair()
        
        return cls(
            colors=colors,
            fonts=fonts,
            **data
        )


# 预定义品牌主题
BRAND_THEMES: Dict[str, BrandStyle] = {}


def register_theme(name: str, style: BrandStyle):
    """注册品牌主题"""
    BRAND_THEMES[name] = style


def get_theme(name: str) -> Optional[BrandStyle]:
    """获取品牌主题"""
    return BRAND_THEMES.get(name)


def list_themes() -> Dict[str, BrandStyle]:
    """列出所有主题"""
    return BRAND_THEMES.copy()


# 注册预定义主题

# 1. 默认主题
register_theme("default", BrandStyle(
    name="Default",
    description="Default brand style"
))

# 2. 企业风格
register_theme("corporate", BrandStyle(
    name="Corporate",
    description="Professional corporate style",
    colors=ColorPalette(
        primary="#003366",  # 深蓝
        secondary="#0066cc",  # 蓝色
        accent="#0099ff",  # 亮蓝
        charts=[
            "#003366", "#0066cc", "#0099ff",
            "#66b3ff", "#99ccff", "#cce5ff"
        ]
    ),
    fonts=FontPair(
        heading="Helvetica Neue",
        body="Helvetica",
        heading_size=52,
        body_size=20
    )
))

# 3. 极简风格
register_theme("minimalist", BrandStyle(
    name="Minimalist",
    description="Clean and minimal style",
    colors=ColorPalette(
        primary="#000000",
        secondary="#333333",
        accent="#666666",
        background="#FFFFFF",
        text="#000000",
        charts=["#000000", "#333333", "#666666", "#999999"]
    ),
    fonts=FontPair(
        heading="Helvetica Neue Light",
        body="Helvetica Neue",
        heading_size=48,
        body_size=16
    ),
    margin=60,
    border_radius=0
))

# 4. 鲜艳风格
register_theme("vibrant", BrandStyle(
    name="Vibrant",
    description="Colorful and energetic style",
    colors=ColorPalette(
        primary="#FF6B6B",  # 珊瑚红
        secondary="#4ECDC4",  # 青绿
        accent="#45B7D1",  # 天蓝
        charts=[
            "#FF6B6B", "#4ECDC4", "#45B7D1",
            "#FFA07A", "#98D8C8", "#F7DC6F"
        ]
    ),
    fonts=FontPair(
        heading="Montserrat",
        body="Open Sans",
        heading_size=56,
        body_size=20
    ),
    border_radius=12
))

# 5. NYT 风格（参考纽约时报）
register_theme("new_york_times", BrandStyle(
    name="New York Times",
    description="Inspired by The New York Times data visualization",
    colors=ColorPalette(
        primary="#326891",  # NYT 蓝
        secondary="#EAECEF",  # 浅灰
        accent="#5F6D7B",  # 深灰
        text="#121212",
        charts=[
            "#326891", "#EAECEF", "#5F6D7B",
            "#A5A9AB", "#D3D7DB"
        ]
    ),
    fonts=FontPair(
        heading="Georgia",
        body="Georgia",
        heading_size=50,
        body_size=18
    )
))

# 6. FT 风格（参考金融时报）
register_theme("financial_times", BrandStyle(
    name="Financial Times",
    description="Inspired by Financial Times visual style",
    colors=ColorPalette(
        primary="#F27935",  # FT 橙
        secondary="#00A651",  # 绿色
        accent="#662D91",  # 紫色
        charts=[
            "#F27935", "#00A651", "#662D91",
            "#ED1B2F", "#0072CE"
        ]
    ),
    fonts=FontPair(
        heading="FT Clegg Headline",
        body="FT Clegg Text",
        heading_size=52,
        body_size=19
    )
))


# 导出
__all__ = [
    'ColorPalette',
    'FontPair',
    'BrandStyle',
    'BRAND_THEMES',
    'register_theme',
    'get_theme',
    'list_themes'
]
