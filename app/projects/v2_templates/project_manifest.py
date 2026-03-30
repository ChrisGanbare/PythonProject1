"""Project manifest for v2_templates discovered by root scheduler."""

PROJECT_MANIFEST = {
    "name": "v2_templates",
    "description": "通用图表视频模板，支持柱状图竞赛、折线图动画、散点图等多种数据可视化",
    "default_task": "render",
    "capabilities": {
        "viz_backends": ["matplotlib"],
    },
    "tasks": {
        "render": {
            "callable": "v2_templates.entrypoints:run_render",
            "description": "使用指定模板将数据渲染为可视化视频",
            "parameters": [
                {
                    "name": "template",
                    "type": "string",
                    "description": "模板名称。bar_chart_race=柱状图竞赛, bar_chart_horizontal=横向柱状图, line_chart_animated=动态折线图, area_chart_stacked=堆叠面积图, scatter_plot_dynamic=动态散点图, bubble_chart=气泡图",
                    "enum": [
                        "bar_chart_race",
                        "bar_chart_horizontal",
                        "line_chart_animated",
                        "area_chart_stacked",
                        "scatter_plot_dynamic",
                        "bubble_chart",
                    ],
                    "default": "bar_chart_race",
                },
                {
                    "name": "data",
                    "type": "object",
                    "description": "图表数据，格式示例：{\"categories\": [\"A\", \"B\", \"C\"], \"values\": [10, 20, 30]}",
                    "default": {},
                },
                {
                    "name": "brand",
                    "type": "string",
                    "description": "品牌视觉主题：default=默认, corporate=商务风, vibrant=鲜艳活泼",
                    "enum": ["default", "corporate", "vibrant"],
                    "default": "default",
                },
                {
                    "name": "platform",
                    "type": "string",
                    "description": "目标发布平台：douyin=抖音竖屏, bilibili_landscape=B站横屏, bilibili_portrait=B站竖屏, xiaohongshu=小红书",
                    "enum": ["douyin", "bilibili_landscape", "bilibili_portrait", "xiaohongshu"],
                    "default": "douyin",
                },
            ],
        },
    },
}
