"""
可视化模块 - 基于 Plotly 的图表渲染

参考设计:
- Plotly 组件化架构
- D3 数据绑定理念
- 声明式配置
"""

import plotly.graph_objects as go
import plotly.io as pio
from typing import Dict, List, Any, Optional
import numpy as np


class ChartConfig:
    """图表配置 - 声明式配置模式"""
    
    def __init__(self, chart_type: str = "scatter"):
        self.chart_type = chart_type
        self.data: Dict[str, Any] = {}
        self.layout: Dict[str, Any] = {}
        self.animation: Dict[str, Any] = {"enabled": False}
        self.style: Dict[str, Any] = {}
    
    def set_data(self, **kwargs) -> 'ChartConfig':
        """设置数据 - 链式调用"""
        self.data.update(kwargs)
        return self
    
    def set_layout(self, **kwargs) -> 'ChartConfig':
        """设置布局 - 链式调用"""
        self.layout.update(kwargs)
        return self
    
    def enable_animation(self, duration: int = 1000) -> 'ChartConfig':
        """启用动画"""
        self.animation = {"enabled": True, "duration": duration}
        return self
    
    def set_style(self, **kwargs) -> 'ChartConfig':
        """设置样式 - 链式调用"""
        self.style.update(kwargs)
        return self


class PlotlyVisualizer:
    """
    Plotly 可视化器
    
    功能:
    - 支持多种图表类型
    - 声明式配置
    - 导出为图像/HTML
    - 动画支持
    """
    
    def __init__(self, width: int = 800, height: int = 600):
        self.width = width
        self.height = height
        self.fig: Optional[go.Figure] = None
    
    def create_chart(self, config: ChartConfig) -> go.Figure:
        """
        根据配置创建图表
        
        Args:
            config: 图表配置对象
            
        Returns:
            Plotly Figure 对象
        """
        # 创建基础 Figure
        self.fig = go.Figure()
        
        # 添加数据轨迹
        self._add_traces(config)
        
        # 更新布局
        self.fig.update_layout(
            width=self.width,
            height=self.height,
            **config.layout
        )
        
        # 应用样式
        if config.style:
            self.fig.update_traces(**config.style)
        
        return self.fig
    
    def _add_traces(self, config: ChartConfig):
        """添加数据轨迹"""
        chart_type = config.chart_type
        data = config.data
        
        # 根据类型创建不同的轨迹
        if chart_type == "scatter":
            trace = go.Scatter(
                x=data.get('x', []),
                y=data.get('y', []),
                mode=data.get('mode', 'lines+markers'),
                name=data.get('name', 'Series')
            )
        elif chart_type == "bar":
            trace = go.Bar(
                x=data.get('x', []),
                y=data.get('y', []),
                name=data.get('name', 'Series')
            )
        elif chart_type == "line":
            trace = go.Scatter(
                x=data.get('x', []),
                y=data.get('y', []),
                mode='lines',
                name=data.get('name', 'Series')
            )
        elif chart_type == "area":
            trace = go.Scatter(
                x=data.get('x', []),
                y=data.get('y', []),
                fill='tozeroy',
                mode='lines',
                name=data.get('name', 'Series')
            )
        else:
            raise ValueError(f"Unsupported chart type: {chart_type}")
        
        self.fig.add_trace(trace)
    
    def create_animated_chart(self, frames_data: List[Dict]) -> go.Figure:
        """
        创建动画图表
        
        Args:
            frames_data: 每帧的数据列表
            
        Returns:
            带动画的 Figure 对象
        """
        if not frames_data:
            raise ValueError("frames_data cannot be empty")
        
        # 创建基础 Figure
        self.fig = go.Figure()
        
        # 添加初始帧
        initial_data = frames_data[0]
        self.fig.add_trace(go.Scatter(
            x=initial_data.get('x', []),
            y=initial_data.get('y', []),
            mode='lines+markers',
            name='Series'
        ))
        
        # 创建帧
        frames = []
        for i, frame_data in enumerate(frames_data):
            frame = go.Frame(
                data=[go.Scatter(
                    x=frame_data.get('x', []),
                    y=frame_data.get('y', [])
                )],
                name=str(i)
            )
            frames.append(frame)
        
        self.fig.frames = frames
        
        # 更新布局以支持动画
        self.fig.update_layout(
            width=self.width,
            height=self.height,
            updatemenus=[{
                'type': 'buttons',
                'buttons': [{
                    'label': 'Play',
                    'method': 'animate',
                    'args': [None]
                }]
            }],
            sliders=[{
                'steps': [{
                    'method': 'animate',
                    'args': [[str(i)]],
                    'label': str(i)
                } for i in range(len(frames_data))]
            }]
        )
        
        return self.fig
    
    def save_as_image(self, filepath: str, format: str = "png"):
        """
        保存为图像
        
        Args:
            filepath: 输出文件路径
            format: 图像格式 (png, jpeg, svg, pdf)
        """
        if self.fig is None:
            raise ValueError("No figure created yet")
        
        try:
            pio.write_image(self.fig, filepath, format=format)
            print(f"Saved chart to {filepath}")
        except ValueError as e:
            # kaleido 未安装时的降级方案
            print(f"Note: Static image export requires kaleido: pip install kaleido")
            print(f"  Falling back to HTML export...")
            html_path = filepath.rsplit('.', 1)[0] + '.html'
            self.save_as_html(html_path)
    
    def save_as_html(self, filepath: str):
        """
        保存为交互式 HTML
        
        Args:
            filepath: 输出文件路径
        """
        if self.fig is None:
            raise ValueError("No figure created yet")
        
        pio.write_html(self.fig, filepath)
        print(f"Saved interactive chart to {filepath}")


# 便捷函数
def quick_scatter(x: List, y: List, title: str = "Scatter Plot", 
                  save_path: Optional[str] = None) -> go.Figure:
    """快速创建散点图"""
    config = ChartConfig("scatter")
    config.set_data(x=x, y=y, name="Data")
    config.set_layout(title=title, xaxis_title="X", yaxis_title="Y")
    
    viz = PlotlyVisualizer()
    fig = viz.create_chart(config)
    
    if save_path:
        viz.save_as_image(save_path)
    
    return fig


def quick_line(x: List, y: List, title: str = "Line Chart",
               save_path: Optional[str] = None) -> go.Figure:
    """快速创建折线图"""
    config = ChartConfig("line")
    config.set_data(x=x, y=y, name="Trend")
    config.set_layout(title=title, xaxis_title="X", yaxis_title="Y")
    
    viz = PlotlyVisualizer()
    fig = viz.create_chart(config)
    
    if save_path:
        viz.save_as_image(save_path)
    
    return fig


if __name__ == "__main__":
    # 测试代码
    print("Testing PlotlyVisualizer...")
    
    # 测试基础图表
    x = list(range(10))
    y = [i ** 2 for i in x]
    
    fig = quick_scatter(x, y, title="Quadratic Function", 
                        save_path="test_scatter.png")
    print("✓ Scatter chart created")
    
    # 测试动画图表
    frames = []
    for i in range(5):
        frames.append({
            'x': list(range(i + 1)),
            'y': [j ** 2 for j in range(i + 1)]
        })
    
    viz = PlotlyVisualizer()
    fig = viz.create_animated_chart(frames)
    viz.save_as_html("test_animated.html")
    print("✓ Animated chart created")
    
    print("\nAll tests passed!")
