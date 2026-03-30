"""
Shared Visualization Module — 数据可视化核心

主要导出：
  - 后端注册与解析（registry）
  - 帧请求构造（runtime）
  - Plotly 快速图表（plotly_viz）
"""

from .plotly_viz import ChartConfig, PlotlyVisualizer, quick_line, quick_scatter
from .registry import default_backend_name, get_backend, list_backends, register_backend
from .runtime import frame_request_from_env

__version__ = "1.0.0"
__all__ = [
    # plotly 快速图表
    "PlotlyVisualizer",
    "ChartConfig",
    "quick_scatter",
    "quick_line",
    # 后端管理
    "default_backend_name",
    "get_backend",
    "list_backends",
    "register_backend",
    # 帧请求
    "frame_request_from_env",
]
