"""Project manifest discovered by root scheduler."""

PROJECT_MANIFEST = {
    "name": "loan_comparison",
    "description": "Loan visualization and video generation service",
    "default_task": "smoke_check",
    "capabilities": {
        "screenplay_workflow": True,
        "viz_backends": ["matplotlib"],
    },
    "tasks": {
        "smoke_check": {
            "callable": "loan_comparison.entrypoints:run_smoke_check",
            "description": "Validation without heavy dependencies",
        },
        "loan_animation": {
            "callable": "loan_comparison.entrypoints:run_loan_animation",
            "description": "Generate comparison video (matplotlib)",
            "parameters": [
                {"name": "loan_amount", "type": "float", "default": 2000000},
                {"name": "annual_rate", "type": "float", "default": 0.042},
                {"name": "loan_years", "type": "int", "default": 30},
                {"name": "output_file", "type": "str", "default": ""},
                {"name": "quality", "type": "str", "default": "preview"},
                {"name": "style", "type": "str", "default": "cinematic", "description": "Visual style (cinematic, minimal, dramatic)"},
                {"name": "topic", "type": "str", "default": "", "description": "Custom topic prompt for AI Planner"}
            ]
        },
        "scene_schedule_preview": {
            "callable": "loan_comparison.entrypoints:run_scene_schedule_preview",
            "description": "Preview scene-level schedule metadata without rendering video",
            "parameters": [
                {"name": "platform", "type": "str", "default": "douyin"},
                {"name": "duration", "type": "int", "default": 30},
                {"name": "fps", "type": "int", "default": 30},
                {"name": "style", "type": "str", "default": "cinematic"},
                {"name": "topic", "type": "str", "default": ""}
            ]
        },
        "api": {
            "callable": "loan_comparison.entrypoints:run_api",
            "description": "Start FastAPI service",
        },
    },
}
