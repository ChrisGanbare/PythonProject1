"""
可视化图表组件基类

定义所有图表组件的统一接口，支持主题、动画、摄像机变换。
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


class ChartType(str, Enum):
    """图表类型"""

    BAR = "bar"
    BAR_STACKED = "bar_stacked"
    LINE = "line"
    AREA = "area"
    PIE = "pie"
    DONUT = "donut"
    SCATTER = "scatter"
    HEATMAP = "heatmap"
    RADAR = "radar"
    SANKEY = "sankey"


@dataclass
class ChartStyle:
    """图表样式配置"""

    # 颜色
    primary_color: str = "#4F9EFF"
    secondary_color: str = "#22D47E"
    accent_color: str = "#FBBF24"
    background_color: str = "#0D0D1A"
    text_color: str = "#FFFFFF"
    grid_color: str = "#1F2937"

    # 字体
    font_family: str = "Source Han Sans SC"
    title_font_size: int = 24
    label_font_size: int = 14
    tick_font_size: int = 12

    # 布局
    show_grid: bool = True
    show_legend: bool = True
    legend_position: str = "upper right"

    # 动画
    animation_easing: str = "ease_in_out_cubic"
    animation_duration: int = 30  # 帧数


@dataclass
class ChartBounds:
    """图表边界配置"""

    left: float = 0.1
    right: float = 0.9
    bottom: float = 0.1
    top: float = 0.9

    def to_axes_coords(self) -> tuple[float, float, float, float]:
        """转换为 matplotlib axes 坐标"""
        return (
            self.left,
            self.bottom,
            self.right - self.left,
            self.top - self.bottom,
        )


@dataclass
class AnimationFrame:
    """动画帧数据"""

    frame_index: int
    progress: float  # 0-1，动画进度
    data_snapshot: dict[str, Any]
    camera_transform: dict[str, float] = field(default_factory=dict)


class ChartBase(ABC):
    """图表基类 — 所有图表组件必须继承此类"""

    def __init__(
        self,
        data: pd.DataFrame,
        style: ChartStyle = None,
        bounds: ChartBounds = None,
        title: str = "",
        **kwargs,
    ):
        self.data = data
        self.style = style or ChartStyle()
        self.bounds = bounds or ChartBounds()
        self.title = title
        self.kwargs = kwargs

        self._fig: plt.Figure | None = None
        self._ax = None
        self._current_frame = 0
        self._total_frames = 0

    @property
    @abstractmethod
    def chart_type(self) -> ChartType:
        """返回图表类型"""
        pass

    @abstractmethod
    def _do_render(self, frame_index: int = 0, total_frames: int = 1):
        """
        执行渲染逻辑

        Args:
            frame_index: 当前帧索引（用于动画）
            total_frames: 总帧数（用于动画进度计算）
        """
        pass

    def render_frame(
        self, frame_index: int = 0, total_frames: int = 1
    ) -> np.ndarray:
        """
        渲染单帧

        Args:
            frame_index: 当前帧索引
            total_frames: 总帧数

        Returns:
            RGBA numpy array (H, W, 4)
        """
        self._current_frame = frame_index
        self._total_frames = total_frames

        # 创建图形
        self._setup_figure()

        # 执行渲染
        self._do_render(frame_index, total_frames)

        # 转换为 numpy array
        return self._fig_to_array()

    def _setup_figure(self):
        """设置图形"""
        plt.close("all")
        self._fig, self._ax = plt.subplots(
            figsize=(16, 9),
            dpi=100,
            facecolor=self.style.background_color,
        )
        self._ax.set_facecolor(self.style.background_color)

        # 设置边界
        self._ax.set_position(self.bounds.to_axes_coords())

        # 设置标题
        if self.title:
            self._ax.set_title(
                self.title,
                fontsize=self.style.title_font_size,
                color=self.style.text_color,
                fontfamily=self.style.font_family,
                pad=20,
            )

    def _fig_to_array(self) -> np.ndarray:
        """将 matplotlib 图形转换为 RGBA numpy array"""
        self._fig.canvas.draw()
        data = np.frombuffer(self._fig.canvas.tostring_argb(), dtype=np.uint8)
        data = data.reshape(self._fig.canvas.get_width_height()[::-1] + (4,))

        # ARGB -> RGBA
        data = data[..., [1, 2, 3, 0]]

        plt.close(self._fig)
        return data

    def _apply_camera_transform(self, transform: dict[str, float]):
        """应用摄像机变换"""
        if not self._ax:
            return

        # 平移
        if "x" in transform or "y" in transform:
            x_shift = transform.get("x", 0)
            y_shift = transform.get("y", 0)
            xlim = self._ax.get_xlim()
            ylim = self._ax.get_ylim()
            x_range = xlim[1] - xlim[0]
            y_range = ylim[1] - ylim[0]
            self._ax.set_xlim(
                xlim[0] + x_shift * x_range, xlim[1] + x_shift * x_range
            )
            self._ax.set_ylim(
                ylim[0] + y_shift * y_range, ylim[1] + y_shift * y_range
            )

        # 缩放
        if "zoom" in transform:
            zoom = transform["zoom"]
            xlim = self._ax.get_xlim()
            ylim = self._ax.get_ylim()
            x_center = (xlim[0] + xlim[1]) / 2
            y_center = (ylim[0] + ylim[1]) / 2
            x_range = (xlim[1] - xlim[0]) / zoom
            y_range = (ylim[1] - ylim[0]) / zoom
            self._ax.set_xlim(x_center - x_range / 2, x_center + x_range / 2)
            self._ax.set_ylim(y_center - y_range / 2, y_center + y_range / 2)

    def _get_animation_progress(
        self, frame_index: int, total_frames: int
    ) -> float:
        """获取动画进度（带缓动）"""
        if total_frames <= 1:
            return 1.0

        t = frame_index / total_frames

        # ease-in-out-cubic
        if t < 0.5:
            return 4 * t * t * t
        return 1 - pow(-2 * t + 2, 3) / 2

    def _setup_grid(self):
        """设置网格"""
        if self.style.show_grid:
            self._ax.grid(
                True,
                linestyle="--",
                linewidth=0.5,
                color=self.style.grid_color,
                alpha=0.5,
            )

    def _setup_legend(self):
        """设置图例"""
        if self.style.show_legend and self._ax:
            self._ax.legend(
                loc=self.style.legend_position,
                facecolor=self.style.background_color,
                edgecolor=self.style.grid_color,
                labelcolor=self.style.text_color,
                fontsize=self.style.label_font_size,
            )

    def animate(
        self,
        output_path: str,
        fps: int = 30,
        duration: int = 10,
        camera_motion: str = None,
    ):
        """
        生成完整动画

        Args:
            output_path: 输出文件路径
            fps: 帧率
            duration: 时长（秒）
            camera_motion: 摄像机运动类型
        """
        from matplotlib.animation import FuncAnimation, FFMpegWriter

        total_frames = fps * duration

        def init():
            self._setup_figure()
            self._do_render(0, total_frames)
            return [self._ax]

        def update(frame):
            self._fig.clf()
            self._setup_figure()
            self._do_render(frame, total_frames)
            return [self._ax]

        anim = FuncAnimation(
            self._fig,
            update,
            init_func=init,
            frames=total_frames,
            blit=False,
            interval=1000 / fps,
        )

        writer = FFMpegWriter(
            fps=fps,
            metadata={"title": self.title},
            bitrate=8000,
        )

        anim.save(output_path, writer=writer)
        plt.close()

    def get_data_summary(self) -> dict[str, Any]:
        """获取数据摘要"""
        return {
            "row_count": len(self.data),
            "column_count": len(self.data.columns),
            "columns": list(self.data.columns),
            "numeric_columns": list(
                self.data.select_dtypes(include=[np.number]).columns
            ),
        }
