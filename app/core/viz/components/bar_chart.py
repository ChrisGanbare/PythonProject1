"""
柱状图组件 — 支持普通柱状图、堆叠柱状图、分组柱状图
"""

from __future__ import annotations

from typing import Any

import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from .base import ChartBase, ChartBounds, ChartStyle, ChartType


class BarChart(ChartBase):
    """柱状图组件"""

    def __init__(
        self,
        data: pd.DataFrame,
        x_column: str = None,
        y_columns: list[str] = None,
        stacked: bool = False,
        horizontal: bool = False,
        show_values: bool = True,
        style: ChartStyle = None,
        bounds: ChartBounds = None,
        title: str = "",
        **kwargs,
    ):
        super().__init__(
            data, style=style, bounds=bounds, title=title, **kwargs
        )

        self.x_column = x_column
        self.y_columns = y_columns or []
        self.stacked = stacked
        self.horizontal = horizontal
        self.show_values = show_values

        # 自动推断列
        self._infer_columns()

    @property
    def chart_type(self) -> ChartType:
        return ChartType.BAR_STACKED if self.stacked else ChartType.BAR

    def _infer_columns(self):
        """自动推断列"""
        if not self.x_column and len(self.data.columns) > 0:
            # 第一个非数值列作为 x 轴
            for col in self.data.columns:
                if self.data[col].dtype == "object":
                    self.x_column = col
                    break

            # 如果没有找到非数值列，使用第一列
            if not self.x_column:
                self.x_column = self.data.columns[0]

        if not self.y_columns:
            # 其余数值列作为 y 轴
            self.y_columns = [
                col
                for col in self.data.select_dtypes(include=[np.number]).columns
                if col != self.x_column
            ]

    def _do_render(self, frame_index: int = 0, total_frames: int = 1):
        """执行渲染"""
        progress = self._get_animation_progress(frame_index, total_frames)

        if self.horizontal:
            self._render_horizontal(progress)
        elif self.stacked:
            self._render_stacked(progress)
        else:
            self._render_grouped(progress)

        self._setup_grid()
        self._setup_legend()

    def _render_grouped(self, progress: float):
        """渲染分组柱状图"""
        if not self._ax:
            return

        n_groups = len(self.data)
        n_bars = len(self.y_columns)
        bar_width = 0.8 / n_bars

        x = np.arange(n_groups)
        colors = self._get_colors(n_bars)

        for i, column in enumerate(self.y_columns):
            # 动画效果：柱子从底部生长
            heights = self.data[column].values * progress

            self._ax.bar(
                x + i * bar_width - (n_bars - 1) * bar_width / 2,
                heights,
                bar_width,
                label=column,
                color=colors[i],
                edgecolor="none",
            )

            # 显示数值标签
            if self.show_values and progress > 0.8:
                for j, height in enumerate(heights):
                    if height > 0:
                        self._ax.text(
                            x[j] + i * bar_width - (n_bars - 1) * bar_width / 2,
                            height,
                            f"{height:.1f}",
                            ha="center",
                            va="bottom",
                            fontsize=self.style.label_font_size,
                            color=self.style.text_color,
                        )

        # 设置 x 轴标签
        self._ax.set_xticks(x)
        self._ax.set_xticklabels(
            self.data[self.x_column].values,
            fontsize=self.style.tick_font_size,
            color=self.style.text_color,
            rotation=45,
            ha="right",
        )

        # 设置 y 轴
        self._ax.set_ylabel(
            "Value",
            fontsize=self.style.label_font_size,
            color=self.style.text_color,
        )
        self._ax.tick_params(axis="y", labelsize=self.style.tick_font_size, labelcolor=self.style.text_color)

    def _render_stacked(self, progress: float):
        """渲染堆叠柱状图"""
        if not self._ax:
            return

        n_groups = len(self.data)
        x = np.arange(n_groups)
        colors = self._get_colors(len(self.y_columns))

        bottom = np.zeros(n_groups)

        for i, column in enumerate(self.y_columns):
            # 动画效果：每层依次生长
            layer_progress = min(1.0, progress * len(self.y_columns) - i)
            layer_progress = max(0.0, layer_progress)

            values = self.data[column].values * layer_progress

            self._ax.bar(
                x,
                values,
                0.8,
                bottom=bottom,
                label=column,
                color=colors[i],
                edgecolor="none",
            )

            # 显示数值标签
            if self.show_values and layer_progress > 0.8:
                for j, (b, v) in enumerate(zip(bottom, values)):
                    if v > 0:
                        self._ax.text(
                            x[j],
                            b + v / 2,
                            f"{v:.1f}",
                            ha="center",
                            va="center",
                            fontsize=self.style.label_font_size,
                            color=self.style.text_color,
                        )

            bottom += values

        # 设置 x 轴标签
        self._ax.set_xticks(x)
        self._ax.set_xticklabels(
            self.data[self.x_column].values,
            fontsize=self.style.tick_font_size,
            color=self.style.text_color,
            rotation=45,
            ha="right",
        )

        # 设置 y 轴
        self._ax.set_ylabel(
            "Value",
            fontsize=self.style.label_font_size,
            color=self.style.text_color,
        )
        self._ax.tick_params(axis="y", labelsize=self.style.tick_font_size, labelcolor=self.style.text_color)

    def _render_horizontal(self, progress: float):
        """渲染水平柱状图"""
        if not self._ax:
            return

        n_groups = len(self.data)
        y = np.arange(n_groups)
        colors = self._get_colors(len(self.y_columns))

        # 只渲染第一个 y 列（水平柱状图通常只显示一个指标）
        column = self.y_columns[0] if self.y_columns else self.data.select_dtypes(include=[np.number]).columns[0]
        values = self.data[column].values * progress

        bars = self._ax.barh(y, values, 0.8, color=colors[0], edgecolor="none")

        # 显示数值标签
        if self.show_values and progress > 0.8:
            for i, (bar, value) in enumerate(zip(bars, values)):
                if value > 0:
                    self._ax.text(
                        value,
                        i,
                        f"{value:.1f}",
                        va="center",
                        ha="left",
                        fontsize=self.style.label_font_size,
                        color=self.style.text_color,
                    )

        # 设置 y 轴标签
        self._ax.set_yticks(y)
        self._ax.set_yticklabels(
            self.data[self.x_column].values,
            fontsize=self.style.tick_font_size,
            color=self.style.text_color,
        )

        # 设置 x 轴
        self._ax.set_xlabel(
            column,
            fontsize=self.style.label_font_size,
            color=self.style.text_color,
        )
        self._ax.tick_params(axis="x", labelsize=self.style.tick_font_size, labelcolor=self.style.text_color)

    def _get_colors(self, n: int) -> list[str]:
        """获取颜色列表"""
        base_colors = [
            self.style.primary_color,
            self.style.secondary_color,
            self.style.accent_color,
            "#EC4899",  # 粉色
            "#8B5CF6",  # 紫色
            "#10B981",  # 绿色
            "#F59E0B",  # 琥珀色
            "#EF4444",  # 红色
        ]

        if n <= len(base_colors):
            return base_colors[:n]

        # 生成更多颜色
        return base_colors + [
            f"#{i:06x}" for i in np.random.randint(0, 0xFFFFFF, n - len(base_colors), dtype=int)
        ]

    def add_reference_line(
        self,
        value: float,
        label: str = None,
        color: str = "#EF4444",
        linestyle: str = "--",
    ):
        """添加参考线"""
        if self._ax:
            if self.horizontal:
                self._ax.axvline(
                    value, color=color, linestyle=linestyle, linewidth=2, alpha=0.7
                )
            else:
                self._ax.axhline(
                    value, color=color, linestyle=linestyle, linewidth=2, alpha=0.7
                )

            if label:
                if self.horizontal:
                    self._ax.text(
                        value,
                        0.95,
                        label,
                        transform=self._ax.get_xaxis_transform(),
                        ha="center",
                        va="top",
                        fontsize=self.style.label_font_size,
                        color=color,
                    )
                else:
                    self._ax.text(
                        0.95,
                        value,
                        label,
                        transform=self._ax.get_yaxis_transform(),
                        ha="right",
                        va="center",
                        fontsize=self.style.label_font_size,
                        color=color,
                    )


# 使用示例
if __name__ == "__main__":
    # 创建示例数据
    df = pd.DataFrame(
        {
            "category": ["A", "B", "C", "D", "E"],
            "value_1": [10, 15, 7, 12, 9],
            "value_2": [8, 11, 5, 10, 7],
            "value_3": [5, 8, 3, 6, 4],
        }
    )

    # 创建分组柱状图
    chart = BarChart(
        df,
        x_column="category",
        y_columns=["value_1", "value_2", "value_3"],
        title="分组柱状图示例",
    )

    # 渲染单帧
    frame = chart.render_frame(frame_index=30, total_frames=30)
    print(f"Rendered frame: {frame.shape}")

    # 创建堆叠柱状图
    stacked_chart = BarChart(
        df,
        x_column="category",
        y_columns=["value_1", "value_2", "value_3"],
        stacked=True,
        title="堆叠柱状图示例",
    )

    # 生成动画（需要 FFmpeg）
    # stacked_chart.animate(
    #     output_path="output/bar_chart.mp4",
    #     fps=30,
    #     duration=3,
    # )
