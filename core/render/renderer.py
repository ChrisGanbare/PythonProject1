"""
渲染器集成 - 将模板清单渲染为实际视频

连接模板引擎与可视化后端，负责将 VideoManifest 转换为视频文件。

支持多种渲染后端:
    - PlotlyBackend: 使用 Plotly 进行静态图表渲染
    - ManimBackend: 使用 Manim 进行动画渲染 (开发中)

使用示例:
    ```python
    from core.render import create_renderer
    
    # 创建渲染器
    renderer = create_renderer(backend="plotly", width=1920, height=1080)
    
    # 渲染视频
    video_path = renderer.render(manifest.to_dict(), "output.mp4")
    ```
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
import asyncio

import pandas as pd
import plotly.graph_objects as go
import plotly.io as pio


class RenderBackend(ABC):
    """
    渲染后端协议 (抽象基类)
    
    定义渲染器的标准接口，所有渲染后端都必须实现这些方法。
    
    设计模式: 策略模式
        - 允许在运行时切换不同的渲染后端
        - 便于扩展新的渲染引擎 (如 Manim、Matplotlib 等)
    """
    
    @abstractmethod
    def render_frame(self, scene: Dict[str, Any], output_path: str) -> str:
        """
        渲染单帧图像
        
        Args:
            scene: 场景配置 (包含图表类型、数据、配置等)
            output_path: 输出文件路径
            
        Returns:
            str: 实际输出的文件路径
        """
        pass
    
    @abstractmethod
    def render_clip(
        self, 
        scenes: List[Dict[str, Any]], 
        output_path: str,
        fps: int = 30
    ) -> str:
        """
        渲染多个场景为视频片段
        
        Args:
            scenes: 场景列表
            output_path: 输出视频路径
            fps: 帧率，默认 30
            
        Returns:
            str: 实际输出的视频路径
        """
        pass


class PlotlyBackend(RenderBackend):
    """
    Plotly 渲染后端
    
    使用 Plotly 库渲染静态图表，然后通过 FFmpeg 合成为视频。
    
    支持的图表类型:
        - bar_chart / horizontal_bar: 柱状图
        - line_chart: 折线图
        - scatter: 散点图
        - bubble: 气泡图
    
    渲染流程:
        1. 解析场景配置
        2. 根据类型创建 Plotly 图表
        3. 保存为 PNG 图像
        4. 使用 FFmpeg 将图像序列合成为视频
    """
    
    def __init__(self, width: int = 1920, height: int = 1080):
        """
        初始化 Plotly 渲染器
        
        Args:
            width: 输出宽度 (像素)，默认 1920
            height: 输出高度 (像素)，默认 1080
        """
        self.width = width
        self.height = height
        self.fig: Optional[go.Figure] = None
    
    def render_frame(self, scene: Dict[str, Any], output_path: str) -> str:
        """
        渲染单帧为图像
        
        Args:
            scene: 场景配置
                - type: 图表类型 (bar_chart, line_chart 等)
                - data: 图表数据
                - config: 图表配置
            output_path: 输出文件路径
            
        Returns:
            str: 输出文件路径
            
        处理流程:
            1. 获取场景类型
            2. 调用对应的图表创建方法
            3. 使用 Plotly 保存为图像
        """
        scene_type = scene.get("type", "bar_chart")
        data = scene.get("data", {})
        config = scene.get("config", {})
        
        # 根据类型创建图表
        if scene_type in ["bar_chart", "horizontal_bar"]:
            fig = self._create_bar_chart(data, config)
        elif scene_type == "line_chart":
            fig = self._create_line_chart(data, config)
        elif scene_type == "scatter":
            fig = self._create_scatter_chart(data, config)
        elif scene_type == "bubble":
            fig = self._create_bubble_chart(data, config)
        else:
            # 默认使用柱状图
            fig = self._create_bar_chart(data, config)
        
        # 保存图像
        pio.write_image(fig, output_path, width=self.width, height=self.height)
        
        return output_path
    
    def render_clip(
        self,
        scenes: List[Dict[str, Any]],
        output_path: str,
        fps: int = 30
    ) -> str:
        """
        渲染多个场景为视频片段
        
        Args:
            scenes: 场景列表
            output_path: 输出视频路径
            fps: 帧率，默认 30
            
        Returns:
            str: 输出视频路径
            
        处理流程:
            1. 创建临时目录存储帧图像
            2. 遍历场景，渲染每一帧
            3. 使用 FFmpeg 将图像序列合成为视频
            4. 清理临时文件
        """
        import tempfile
        from pathlib import Path
        
        # 创建临时目录存储帧
        with tempfile.TemporaryDirectory() as tmpdir:
            frame_paths = []
            
            # 渲染每一帧
            for i, scene in enumerate(scenes):
                frame_path = Path(tmpdir) / f"frame_{i:04d}.png"
                self.render_frame(scene, str(frame_path))
                frame_paths.append(str(frame_path))
            
            # 使用 FFmpeg 合成视频
            video_path = self._frames_to_video(frame_paths, output_path, fps)
        
        return video_path
    
    def _frames_to_video(
        self, 
        frame_paths: List[str], 
        output_path: str,
        fps: int = 30
    ) -> str:
        """
        将帧序列合成为视频
        
        Args:
            frame_paths: 帧图像路径列表
            output_path: 输出视频路径
            fps: 帧率
            
        Returns:
            str: 输出视频路径
            
        技术实现:
            使用 FFmpeg 的 image2 demuxer 将 PNG 序列编码为 H.264 视频
            命令示例:
                ffmpeg -framerate 30 -i frame_%04d.png -c:v libx264 output.mp4
        """
        import subprocess
        
        # FFmpeg 命令
        cmd = [
            "ffmpeg", "-y",  # -y: 覆盖输出文件
            "-framerate", str(fps),
            "-i", f"frame_%04d.png",
            "-c:v", "libx264",  # H.264 编码
            "-pix_fmt", "yuv420p",  # 像素格式 (兼容大多数播放器)
            output_path
        ]
        
        # 在帧目录执行
        import os
        frame_dir = os.path.dirname(frame_paths[0])
        result = subprocess.run(
            cmd,
            cwd=frame_dir,
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            raise RuntimeError(f"FFmpeg 错误：{result.stderr}")
        
        return output_path
    
    def _create_bar_chart(self, data: Dict, config: Dict) -> go.Figure:
        """
        创建柱状图
        
        Args:
            data: 图表数据
                - categories: 分类列表
                - values: 数值列表
            config: 图表配置
                - orientation: 'v' (垂直) 或 'h' (水平)
                
        Returns:
            go.Figure: Plotly 图表对象
        """
        categories = data.get("categories", [])
        values = data.get("values", [])
        
        orientation = config.get("orientation", "v")
        
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=categories if orientation == "v" else values,
            y=values if orientation == "v" else categories,
            orientation=orientation,
            marker_color="steelblue"
        ))
        
        fig.update_layout(
            width=self.width,
            height=self.height,
            showlegend=False
        )
        
        return fig
    
    def _create_line_chart(self, data: Dict, config: Dict) -> go.Figure:
        """
        创建折线图
        
        Args:
            data: 图表数据
                - dates: 日期列表
                - values: 数值列表
                - series: 系列名称
                
        Returns:
            go.Figure: Plotly 图表对象
        """
        dates = data.get("dates", [])
        values = data.get("values", [])
        series = data.get("series", [])
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=dates,
            y=values,
            mode="lines+markers",  # 线条 + 数据点
            name=series[0] if series else "Series"
        ))
        
        fig.update_layout(
            width=self.width,
            height=self.height,
            showlegend=True
        )
        
        return fig
    
    def _create_scatter_chart(self, data: Dict, config: Dict) -> go.Figure:
        """
        创建散点图
        
        Args:
            data: 图表数据
                - x: X 轴数据
                - y: Y 轴数据
                - categories: 分类标签
                
        Returns:
            go.Figure: Plotly 图表对象
        """
        x = data.get("x", [])
        y = data.get("y", [])
        categories = data.get("categories", [])
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=x,
            y=y,
            mode="markers",  # 仅数据点
            marker=dict(size=12),
            text=categories  # 悬停文本
        ))
        
        fig.update_layout(
            width=self.width,
            height=self.height
        )
        
        return fig
    
    def _create_bubble_chart(self, data: Dict, config: Dict) -> go.Figure:
        """
        创建气泡图 (带大小的散点图)
        
        Args:
            data: 图表数据
                - x: X 轴数据
                - y: Y 轴数据
                - sizes: 气泡大小列表
                - categories: 分类标签
                
        Returns:
            go.Figure: Plotly 图表对象
            
        技术要点:
            使用 sizemode="area" 确保气泡面积与数值成正比
            sizeref 用于调整气泡大小的比例因子
        """
        x = data.get("x", [])
        y = data.get("y", [])
        sizes = data.get("sizes", [10] * len(x))
        categories = data.get("categories", [])
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=x,
            y=y,
            mode="markers",
            marker=dict(
                size=sizes,
                sizemode="area",  # 面积模式
                sizeref=2.*max(sizes)/(40.**2),  # 大小参考因子
                sizemin=4  # 最小大小
            ),
            text=categories
        ))
        
        fig.update_layout(
            width=self.width,
            height=self.height
        )
        
        return fig


class ManimBackend(RenderBackend):
    """
    Manim 渲染后端
    
    使用 Manim 引擎进行高质量数学动画渲染。
    
    状态: 开发中
    当前降级策略: 如果 Manim 不可用，自动降级到 Plotly 后端
    
    优势:
        - 高质量数学动画
        - 精确的摄像机控制
        - 平滑的转场效果
    
    限制:
        - 需要安装 Manim 及其依赖 (FFmpeg, LaTeX)
        - 渲染速度较慢
    """
    
    def __init__(self, resolution: Tuple[int, int] = (1920, 1080)):
        """
        初始化 Manim 渲染器
        
        Args:
            resolution: 分辨率 (宽，高)，默认 (1920, 1080)
        """
        self.resolution = resolution
        self.manim_available = self._check_manim()
    
    def _check_manim(self) -> bool:
        """检查 Manim 是否可用"""
        try:
            import manim
            return True
        except ImportError:
            return False
    
    def render_frame(self, scene: Dict[str, Any], output_path: str) -> str:
        """
        渲染单帧 (使用 Manim)
        
        Args:
            scene: 场景配置
            output_path: 输出路径
            
        Returns:
            str: 输出路径
            
        降级策略:
            如果 Manim 不可用，自动使用 Plotly 后端
        """
        if not self.manim_available:
            # 降级到 Plotly
            backend = PlotlyBackend(
                width=self.resolution[0],
                height=self.resolution[1]
            )
            return backend.render_frame(scene, output_path)
        
        # TODO: 实现 Manim 渲染
        raise NotImplementedError("Manim 后端尚未完全实现")
    
    def render_clip(
        self,
        scenes: List[Dict[str, Any]],
        output_path: str,
        fps: int = 30
    ) -> str:
        """
        渲染 Manim 动画
        
        Args:
            scenes: 场景列表
            output_path: 输出路径
            fps: 帧率
            
        Returns:
            str: 输出路径
            
        降级策略:
            如果 Manim 不可用，自动使用 Plotly 后端
        """
        if not self.manim_available:
            backend = PlotlyBackend(
                width=self.resolution[0],
                height=self.resolution[1]
            )
            return backend.render_clip(scenes, output_path, fps)
        
        # TODO: 实现 Manim 动画渲染
        raise NotImplementedError("Manim 后端尚未完全实现")


class VideoRenderer:
    """
    视频渲染器 - 统一管理渲染流程
    
    提供高级 API，封装渲染后端的选择和调用细节。
    
    使用示例:
        ```python
        # 创建渲染器
        renderer = VideoRenderer(backend="plotly", width=1920, height=1080)
        
        # 渲染视频
        video_path = renderer.render(manifest.to_dict(), "output.mp4")
        
        # 异步渲染
        video_path = await renderer.render_async(manifest.to_dict(), "output.mp4")
        ```
    """
    
    def __init__(
        self,
        backend: str = "plotly",
        width: int = 1920,
        height: int = 1080
    ):
        """
        初始化视频渲染器
        
        Args:
            backend: 后端名称 ("plotly" 或 "manim")
            width: 输出宽度
            height: 输出高度
            
        Raises:
            ValueError: 未知的后端名称
        """
        if backend == "plotly":
            self.backend = PlotlyBackend(width, height)
        elif backend == "manim":
            self.backend = ManimBackend((width, height))
        else:
            raise ValueError(f"未知的后端：{backend}")
        
        self.width = width
        self.height = height
    
    def render(self, manifest: Dict[str, Any], output_path: str) -> str:
        """
        渲染视频清单为视频
        
        Args:
            manifest: 视频清单 (VideoManifest.to_dict() 的返回值)
            output_path: 输出文件路径
            
        Returns:
            str: 输出文件路径
            
        处理流程:
            1. 从清单中提取场景和转场
            2. 调用后端渲染场景序列
            3. 应用转场效果 (TODO)
            4. 添加音频 (TODO)
            5. 返回输出路径
        """
        scenes = manifest.get("scenes", [])
        transitions = manifest.get("transitions", [])
        
        if not scenes:
            raise ValueError("没有可渲染的场景")
        
        # 渲染场景
        video_path = self.backend.render_clip(scenes, output_path)
        
        # TODO: 应用转场
        # TODO: 添加音频
        # TODO: 添加水印/Logo
        
        return video_path
    
    async def render_async(
        self,
        manifest: Dict[str, Any],
        output_path: str
    ) -> str:
        """
        异步渲染视频
        
        Args:
            manifest: 视频清单
            output_path: 输出路径
            
        Returns:
            str: 输出路径
            
        使用场景:
            - API 服务中的异步请求处理
            - 批量渲染时不阻塞主线程
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            lambda: self.render(manifest, output_path)
        )


def create_renderer(
    backend: str = "plotly",
    **kwargs
) -> VideoRenderer:
    """
    创建渲染器的工厂函数
    
    Args:
        backend: 后端名称 ("plotly" 或 "manim")
        **kwargs: 传递给 VideoRenderer 的参数
        
    Returns:
        VideoRenderer: 渲染器实例
        
    使用示例:
        ```python
        renderer = create_renderer(backend="plotly", width=1920, height=1080)
        ```
    """
    return VideoRenderer(backend, **kwargs)
