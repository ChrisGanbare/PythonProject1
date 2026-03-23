"""Project manifest discovered by root scheduler."""

PROJECT_MANIFEST = {
    "name": "panel_tutor",
    "description": "创作控制台用户指南",
    "default_task": "smoke_check",
    "capabilities": {
        "viz_backends": ["matplotlib"],
    },
    "tasks": {
        "smoke_check": {
            "callable": "panel_tutor.entrypoints:run_smoke_check",
            "description": "Basic validation for panel_tutor",
        },
        "render": {
            "callable": "panel_tutor.entrypoints:run_render",
            "description": "Generate visualization video",
        },
    },
}
