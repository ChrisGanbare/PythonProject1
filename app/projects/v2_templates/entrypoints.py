"""Callable entrypoints for v2_templates project."""

from __future__ import annotations

from typing import Any


# 每种模板对应的列要求及示例数据
_TEMPLATE_DEFAULTS: dict[str, dict[str, list]] = {
    "bar_chart_race": {
        "date": ["2021", "2021", "2021", "2022", "2022", "2022", "2023", "2023", "2023"],
        "category": ["商品A", "商品B", "商品C"] * 3,
        "value": [100, 150, 80, 130, 160, 95, 170, 140, 120],
    },
    "bar_chart_horizontal": {
        "date": ["Q1", "Q1", "Q1", "Q2", "Q2", "Q2"],
        "category": ["北区", "中区", "南区"] * 2,
        "value": [320, 280, 350, 380, 310, 400],
    },
    "line_chart_animated": {
        "date": ["1月", "2月", "3月", "4月", "1月", "2月", "3月", "4月"],
        "series": ["产品A", "产品A", "产品A", "产品A", "产品B", "产品B", "产品B", "产品B"],
        "value": [10, 20, 15, 30, 8, 18, 25, 22],
    },
    "area_chart_stacked": {
        "date": ["一季度", "二季度", "三季度", "一季度", "二季度", "三季度"],
        "category": ["线上", "线上", "线上", "线下", "线下", "线下"],
        "value": [200, 280, 320, 150, 180, 210],
    },
    "scatter_plot_dynamic": {
        "x": [1.2, 2.5, 3.1, 4.8, 2.0, 3.7],
        "y": [3.4, 5.6, 2.1, 6.3, 4.0, 5.0],
        "category": ["A", "A", "B", "B", "C", "C"],
    },
    "bubble_chart": {
        "x": [1.0, 2.5, 4.0, 3.0],
        "y": [2.0, 3.5, 1.5, 4.5],
        "size": [20, 40, 15, 35],
        "category": ["X", "Y", "X", "Z"],
    },
}

# 各模板必需列名
_REQUIRED_COLUMNS: dict[str, list[str]] = {
    "bar_chart_race": ["date", "category", "value"],
    "bar_chart_horizontal": ["date", "category", "value"],
    "line_chart_animated": ["date", "series", "value"],
    "area_chart_stacked": ["date", "category", "value"],
    "scatter_plot_dynamic": ["x", "y", "category"],
    "bubble_chart": ["x", "y", "size", "category"],
}


def _normalize_data(template: str, data: dict | list | None) -> dict:
    """确保 data 包含模板所需列；缺失时用示例数据填充。"""
    required = _REQUIRED_COLUMNS.get(template, [])
    default = _TEMPLATE_DEFAULTS.get(template, {})

    if not data:
        return default

    # 若是列式 dict，检查是否包含必需列
    if isinstance(data, dict):
        missing = [c for c in required if c not in data]
        if not missing:
            return data
        # 必需列缺失：用示例数据
        return default

    # list 格式：交给 pd.DataFrame 处理，可能缺列时用默认数据
    try:
        import pandas as pd
        df = pd.DataFrame(data)
        missing = [c for c in required if c not in df.columns]
        if not missing:
            return data
    except Exception:
        pass
    return default


def run_render(
    template: str = "bar_chart_race",
    data: dict | list | None = None,
    brand: str = "default",
    platform: str = "douyin",
    output_file: str = "",
) -> dict[str, Any]:
    """Render a v2 template video via core.v2_renderer."""
    from core.v2_renderer import render_v2_template

    normalized = _normalize_data(template, data)

    result_path = render_v2_template(
        template_name=template,
        data=normalized,
        brand=brand,
        platform=platform,
        output_path=output_file or None,
    )
    return {"final_video_path": str(result_path), "status": "success"}
