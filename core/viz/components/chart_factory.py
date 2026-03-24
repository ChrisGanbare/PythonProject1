"""
图表组件工厂 — 统一创建和管理图表组件

提供工厂模式创建各种图表类型，支持链式配置。
"""

from __future__ import annotations

from typing import Type

import pandas as pd

from .base import ChartBase, ChartStyle, ChartType
from .bar_chart import BarChart

# 延迟导入其他图表类型（避免循环依赖）
_chart_registry: dict[str, Type[ChartBase]] = {}


class ChartFactory:
    """
    图表工厂 — 统一创建图表组件

    使用示例:
        from core.viz.components import ChartFactory

        # 创建柱状图
        chart = ChartFactory.create(
            "bar",
            data=df,
            x_column="category",
            y_columns=["value"],
            title="销售数据"
        )

        # 创建堆叠柱状图
        stacked_chart = ChartFactory.create(
            "bar_stacked",
            data=df,
            x_column="category",
            y_columns=["value_a", "value_b"],
            title="堆叠对比"
        )

        # 链式配置
        chart = (ChartFactory
            .create("bar", data=df)
            .with_style(primary_color="#FF5733")
            .with_title("自定义标题")
            .with_animation(easing="ease_out_bounce")
        )
    """

    @classmethod
    def register(cls, chart_type: str, chart_class: Type[ChartBase]):
        """注册图表类型"""
        _chart_registry[chart_type] = chart_class

    @classmethod
    def create(cls, chart_type: str, data: pd.DataFrame, **kwargs) -> ChartBase:
        """
        创建图表实例

        Args:
            chart_type: 图表类型
            data: 数据 DataFrame
            **kwargs: 传递给图表构造函数的参数

        Returns:
            图表实例

        Raises:
            ValueError: 未知的图表类型
        """
        # 注册默认图表
        if not _chart_registry:
            cls._register_defaults()

        if chart_type not in _chart_registry:
            available = ", ".join(sorted(_chart_registry.keys()))
            raise ValueError(
                f"Unknown chart type: {chart_type}. Available types: {available}"
            )

        chart_class = _chart_registry[chart_type]
        return chart_class(data, **kwargs)

    @classmethod
    def list_types(cls) -> list[str]:
        """列出所有可用的图表类型"""
        if not _chart_registry:
            cls._register_defaults()
        return sorted(_chart_registry.keys())

    @classmethod
    def get_type_info(cls, chart_type: str) -> dict[str, str]:
        """获取图表类型信息"""
        if not _chart_registry:
            cls._register_defaults()

        if chart_type not in _chart_registry:
            return {"error": f"Unknown chart type: {chart_type}"}

        chart_class = _chart_registry[chart_type]

        return {
            "type": chart_type,
            "class": chart_class.__name__,
            "description": chart_class.__doc__ or "",
            "supports_stacked": hasattr(chart_class, "stacked"),
            "supports_horizontal": hasattr(chart_class, "horizontal"),
        }

    @classmethod
    def _register_defaults(cls):
        """注册默认图表类型"""
        # 柱状图
        cls.register("bar", BarChart)
        cls.register("bar_grouped", BarChart)
        cls.register("bar_stacked", lambda data, **kwargs: BarChart(data, stacked=True, **kwargs))
        cls.register("bar_horizontal", lambda data, **kwargs: BarChart(data, horizontal=True, **kwargs))

        # 其他图表类型将在实现后注册
        # cls.register("line", LineChart)
        # cls.register("area", AreaChart)
        # cls.register("pie", PieChart)
        # cls.register("scatter", ScatterPlot)
        # cls.register("heatmap", Heatmap)
        # cls.register("radar", RadarChart)


class ChartBuilder:
    """
    图表构建器 — 链式配置图表

    使用示例:
        chart = (ChartBuilder(ChartType.BAR, df)
            .set_x_column("category")
            .set_y_columns(["value_1", "value_2"])
            .set_title("销售数据")
            .set_style(primary_color="#4F9EFF")
            .show_values(True)
            .build()
        )
    """

    def __init__(self, chart_type: ChartType | str, data: pd.DataFrame):
        self.chart_type = (
            chart_type.value if isinstance(chart_type, ChartType) else chart_type
        )
        self.data = data
        self.config: dict = {}
        self.style_config: dict = {}

    def set_x_column(self, column: str) -> "ChartBuilder":
        """设置 X 轴列"""
        self.config["x_column"] = column
        return self

    def set_y_columns(self, columns: list[str]) -> "ChartBuilder":
        """设置 Y 轴列"""
        self.config["y_columns"] = columns
        return self

    def set_title(self, title: str) -> "ChartBuilder":
        """设置标题"""
        self.config["title"] = title
        return self

    def set_stacked(self, stacked: bool = True) -> "ChartBuilder":
        """设置是否堆叠"""
        self.config["stacked"] = stacked
        return self

    def set_horizontal(self, horizontal: bool = True) -> "ChartBuilder":
        """设置是否水平"""
        self.config["horizontal"] = horizontal
        return self

    def set_show_values(self, show: bool = True) -> "ChartBuilder":
        """设置是否显示数值标签"""
        self.config["show_values"] = show
        return self

    def set_style(self, **kwargs) -> "ChartBuilder":
        """设置样式"""
        self.style_config.update(kwargs)
        return self

    def set_bounds(self, **kwargs) -> "ChartBuilder":
        """设置边界"""
        self.config["bounds"] = kwargs
        return self

    def add_option(self, key: str, value) -> "ChartBuilder":
        """添加额外选项"""
        self.config[key] = value
        return self

    def build(self) -> ChartBase:
        """构建图表"""
        if self.style_config:
            style = ChartStyle(**self.style_config)
            self.config["style"] = style

        return ChartFactory.create(self.chart_type, self.data, **self.config)


# 快捷创建函数
def create_bar_chart(
    data: pd.DataFrame,
    x_column: str,
    y_columns: list[str],
    title: str = "",
    stacked: bool = False,
    **kwargs,
) -> ChartBase:
    """快捷创建柱状图"""
    return ChartFactory.create(
        "bar_stacked" if stacked else "bar",
        data,
        x_column=x_column,
        y_columns=y_columns,
        title=title,
        **kwargs,
    )


def create_comparison_chart(
    data: pd.DataFrame,
    category_column: str,
    value_column: str,
    group_column: str = None,
    title: str = "",
    **kwargs,
) -> ChartBase:
    """
    快捷创建对比图表

    Args:
        data: 数据
        category_column: 分类列
        value_column: 数值列
        group_column: 分组列（可选）
        title: 标题
    """
    if group_column:
        # 分组柱状图
        pivot_data = data.pivot(
            index=category_column, columns=group_column, values=value_column
        ).reset_index()
        y_columns = [col for col in pivot_data.columns if col != category_column]
        return create_bar_chart(
            pivot_data,
            x_column=category_column,
            y_columns=y_columns,
            title=title,
            **kwargs,
        )
    else:
        # 简单柱状图
        return create_bar_chart(
            data,
            x_column=category_column,
            y_columns=[value_column],
            title=title,
            **kwargs,
        )


# 初始化默认注册
ChartFactory._register_defaults()


# 使用示例
if __name__ == "__main__":
    # 创建示例数据
    df = pd.DataFrame(
        {
            "month": ["Jan", "Feb", "Mar", "Apr", "May"],
            "revenue": [100, 120, 95, 140, 160],
            "cost": [80, 90, 75, 100, 110],
            "profit": [20, 30, 20, 40, 50],
        }
    )

    # 方法 1: 使用工厂
    print("方法 1: ChartFactory.create()")
    chart1 = ChartFactory.create(
        "bar",
        df,
        x_column="month",
        y_columns=["revenue"],
        title="月收入",
    )
    print(f"  创建图表：{chart1.chart_type.value}")
    print(f"  数据摘要：{chart1.get_data_summary()}")

    # 方法 2: 使用构建器
    print("\n方法 2: ChartBuilder")
    chart2 = (
        ChartBuilder(ChartType.BAR, df)
        .set_x_column("month")
        .set_y_columns(["revenue", "cost", "profit"])
        .set_title("财务数据对比")
        .set_style(primary_color="#4F9EFF", secondary_color="#22D47E")
        .show_values(True)
        .build()
    )
    print(f"  创建图表：{chart2.chart_type.value}")

    # 方法 3: 使用快捷函数
    print("\n方法 3: create_bar_chart()")
    chart3 = create_bar_chart(
        df,
        x_column="month",
        y_columns=["revenue", "cost"],
        title="收入 vs 成本",
        stacked=True,
    )
    print(f"  创建图表：{chart3.chart_type.value}")

    # 列出所有可用类型
    print("\n可用图表类型:")
    for chart_type in ChartFactory.list_types():
        info = ChartFactory.get_type_info(chart_type)
        print(f"  - {chart_type}: {info.get('class', 'N/A')}")
