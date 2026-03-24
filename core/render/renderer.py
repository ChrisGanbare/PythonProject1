"""
渲染器集成 - 将模板清单渲染为实际视频

连接模板引擎与可视化后端
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
import asyncio

import pandas as pd
import plotly.graph_objects as go
import plotly.io as pio


class RenderBackend(ABC):
    """渲染后端协议"""
    
    @abstractmethod
    def render_frame(self, scene: Dict[str, Any], output_path: str) -> str:
        """渲染单帧"""
        pass
    
    @abstractmethod
    def render_clip(
        self, 
        scenes: List[Dict[str, Any]], 
        output_path: str,
        fps: int = 30
    ) -> str:
        """渲染片段"""
        pass


class PlotlyBackend(RenderBackend):
    """Plotly 渲染后端"""
    
    def __init__(self, width: int = 1920, height: int = 1080):
        self.width = width
        self.height = height
        self.fig: Optional[go.Figure] = None
    
    def render_frame(self, scene: Dict[str, Any], output_path: str) -> str:
        """渲染单帧为图像"""
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
        """渲染多个场景为视频片段"""
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
        """将帧序列合成为视频"""
        import subprocess
        
        # 创建帧列表文件
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            for path in frame_paths:
                f.write(f"file '{path}'\n")
            list_file = f.name
        
        # FFmpeg 命令
        cmd = [
            "ffmpeg", "-y",
            "-framerate", str(fps),
            "-i", f"frame_%04d.png",
            "-c:v", "libx264",
            "-pix_fmt", "yuv420p",
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
            raise RuntimeError(f"FFmpeg error: {result.stderr}")
        
        return output_path
    
    def _create_bar_chart(self, data: Dict, config: Dict) -> go.Figure:
        """创建柱状图"""
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
            showlegend=False,
            title=scene.get("title", "Bar Chart") if (scene := {}) else ""
        )
        
        return fig
    
    def _create_line_chart(self, data: Dict, config: Dict) -> go.Figure:
        """创建折线图"""
        dates = data.get("dates", [])
        values = data.get("values", [])
        series = data.get("series", [])
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=dates,
            y=values,
            mode="lines+markers",
            name=series[0] if series else "Series"
        ))
        
        fig.update_layout(
            width=self.width,
            height=self.height,
            showlegend=True
        )
        
        return fig
    
    def _create_scatter_chart(self, data: Dict, config: Dict) -> go.Figure:
        """创建散点图"""
        x = data.get("x", [])
        y = data.get("y", [])
        categories = data.get("categories", [])
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=x,
            y=y,
            mode="markers",
            marker=dict(size=12),
            text=categories
        ))
        
        fig.update_layout(
            width=self.width,
            height=self.height
        )
        
        return fig
    
    def _create_bubble_chart(self, data: Dict, config: Dict) -> go.Figure:
        """创建气泡图"""
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
                sizemode="area",
                sizeref=2.*max(sizes)/(40.**2),
                sizemin=4
            ),
            text=categories
        ))
        
        fig.update_layout(
            width=self.width,
            height=self.height
        )
        
        return fig


class ManimBackend(RenderBackend):
    """Manim 渲染后端"""
    
    def __init__(self, resolution: Tuple[int, int] = (1920, 1080)):
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
        """渲染单帧（使用 Manim）"""
        if not self.manim_available:
            # 降级到 Plotly
            backend = PlotlyBackend(
                width=self.resolution[0],
                height=self.resolution[1]
            )
            return backend.render_frame(scene, output_path)
        
        # TODO: 实现 Manim 渲染
        raise NotImplementedError("Manim backend not fully implemented")
    
    def render_clip(
        self,
        scenes: List[Dict[str, Any]],
        output_path: str,
        fps: int = 30
    ) -> str:
        """渲染 Manim 动画"""
        if not self.manim_available:
            backend = PlotlyBackend(
                width=self.resolution[0],
                height=self.resolution[1]
            )
            return backend.render_clip(scenes, output_path, fps)
        
        # TODO: 实现 Manim 动画渲染
        raise NotImplementedError("Manim backend not fully implemented")


class VideoRenderer:
    """视频渲染器 - 统一管理渲染流程"""
    
    def __init__(
        self,
        backend: str = "plotly",
        width: int = 1920,
        height: int = 1080
    ):
        if backend == "plotly":
            self.backend = PlotlyBackend(width, height)
        elif backend == "manim":
            self.backend = ManimBackend((width, height))
        else:
            raise ValueError(f"Unknown backend: {backend}")
        
        self.width = width
        self.height = height
    
    def render(self, manifest: Dict[str, Any], output_path: str) -> str:
        """
        渲染视频清单为视频
        
        Args:
            manifest: 视频清单 (VideoManifest.to_dict())
            output_path: 输出路径
            
        Returns:
            输出文件路径
        """
        scenes = manifest.get("scenes", [])
        transitions = manifest.get("transitions", [])
        
        if not scenes:
            raise ValueError("No scenes to render")
        
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
        """异步渲染"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            lambda: self.render(manifest, output_path)
        )


def create_renderer(
    backend: str = "plotly",
    **kwargs
) -> VideoRenderer:
    """创建渲染器"""
    return VideoRenderer(backend, **kwargs)
