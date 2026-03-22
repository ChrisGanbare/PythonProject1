"""Project manifest discovered by root scheduler."""

PROJECT_MANIFEST = {
    "name": "video_platform_introduction",
    "description": "当前项目的新手教程视频",
    "default_task": "smoke_check",
    "capabilities": {
        "screenplay_workflow": True,
        "viz_backends": ["manim"],
    },
    "tasks": {
        "smoke_check": {
            "callable": "video_platform_introduction.entrypoints:run_smoke_check",
            "description": "Basic validation for video_platform_introduction",
        },
        "api": {
            "callable": "video_platform_introduction.entrypoints:run_api",
            "description": "Start FastAPI service",
        },
        "generate_intro_video": {
            "callable": "video_platform_introduction.entrypoints:run_intro_video",
            "description": "Generate introduction video clips (Manim)",
        },
    },
}
