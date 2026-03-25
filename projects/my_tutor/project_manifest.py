"""Project manifest discovered by root scheduler."""

PROJECT_MANIFEST = {
    "name": "my_tutor",
    "description": "当前项目的介绍",
    "default_task": "smoke_check",
    "capabilities": {
        "viz_backends": ["matplotlib"],
    },
    "tasks": {
        "smoke_check": {
            "callable": "my_tutor.entrypoints:run_smoke_check",
            "description": "Basic validation for my_tutor",
        },
        "render": {
            "callable": "my_tutor.entrypoints:run_render",
            "description": "Generate visualization video",
        },
    },
}
