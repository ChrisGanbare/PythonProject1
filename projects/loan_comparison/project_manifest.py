"""Project manifest discovered by root scheduler."""

PROJECT_MANIFEST = {
    "name": "loan_comparison",
    "description": "Loan visualization and video generation service",
    "default_task": "smoke_check",
    "tasks": {
        "smoke_check": {
            "callable": "loan_comparison.entrypoints:run_smoke_check",
            "description": "Lightweight health check without external dependencies",
        },
        "loan_animation": {
            "callable": "loan_comparison.entrypoints:run_loan_animation",
            "description": "Render loan comparison animation video",
        },
        "api": {
            "callable": "loan_comparison.entrypoints:run_api",
            "description": "Start FastAPI service",
        },
    },
}
