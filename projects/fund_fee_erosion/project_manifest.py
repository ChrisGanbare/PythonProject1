"""Project manifest discovered by root scheduler."""

PROJECT_MANIFEST = {
    "name": "fund_fee_erosion",
    "description": "基金手续费复利侵蚀可视化 — 数据动画子项目",
    "default_task": "smoke_check",
    "capabilities": {
        "viz_backends": ["matplotlib"],
    },
    "tasks": {
        "smoke_check": {
            "callable": "fund_fee_erosion.entrypoints:run_smoke_check",
            "description": "轻量验证，仅做收益计算，无需 ffmpeg",
        },
        "fund_animation": {
            "callable": "fund_fee_erosion.entrypoints:run_fund_animation",
            "description": "渲染基金手续费侵蚀对比动画 MP4，需要 ffmpeg",
        },
        "api": {
            "callable": "fund_fee_erosion.entrypoints:run_api",
            "description": "启动 FastAPI 服务（默认 0.0.0.0:8001）",
        },
    },
}
