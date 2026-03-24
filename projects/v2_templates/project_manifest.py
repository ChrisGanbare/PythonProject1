"""v2 模板项目 - 使用新模板引擎直接生成视频"""

PROJECT_MANIFEST = {
    "name": "v2_templates",
    "description": "v2.2 通用模板渲染器 - 支持 6+ 种图表模板",
    "default_task": "render",
    "capabilities": {
        "viz_backends": ["plotly"],
        "v2_templates": True,
    },
    "tasks": {
        "render": {
            "callable": "v2_templates.entrypoints:run_render",
            "description": "使用 v2.2 模板引擎渲染视频",
            "parameters": [
                {
                    "name": "template",
                    "type": "string",
                    "description": "模板名称",
                    "choices": [
                        "bar_chart_race",
                        "line_chart_animated",
                        "scatter_plot_dynamic",
                        "area_chart_stacked",
                        "bubble_chart",
                        "bar_chart_horizontal"
                    ],
                    "default": "bar_chart_race"
                },
                {
                    "name": "data",
                    "type": "object",
                    "description": "图表数据 (JSON 格式)"
                },
                {
                    "name": "brand",
                    "type": "string",
                    "description": "品牌主题",
                    "choices": [
                        "default",
                        "corporate",
                        "minimalist",
                        "vibrant",
                        "new_york_times",
                        "financial_times"
                    ],
                    "default": "default"
                },
                {
                    "name": "platform",
                    "type": "string",
                    "description": "目标平台",
                    "choices": [
                        "bilibili",
                        "douyin",
                        "xiaohongshu",
                        "youtube",
                        "instagram",
                        "tiktok"
                    ],
                    "default": "bilibili"
                }
            ]
        }
    }
}
