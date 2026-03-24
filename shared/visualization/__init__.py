"""
Shared Visualization Module

数据可视化核心功能，基于 Plotly
"""

from .plotly_viz import (
    PlotlyVisualizer,
    ChartConfig,
    quick_scatter,
    quick_line
)

__version__ = "1.0.0"
__all__ = [
    'PlotlyVisualizer',
    'ChartConfig',
    'quick_scatter',
    'quick_line'
]
