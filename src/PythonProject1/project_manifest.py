"""Project manifest discovered by root scheduler."""

PROJECT_MANIFEST = {
    "name": "PythonProject1",
    "description": "Loan visualization and video generation service",
    "default_task": "smoke_check",
    "tasks": {
        "smoke_check": {
            "callable": "PythonProject1.entrypoints:run_smoke_check",
            "description": "Lightweight health check without external dependencies",
        },
        "loan_animation": {
            "callable": "PythonProject1.entrypoints:run_loan_animation",
            "description": "Render loan animation (subproject-local original-equivalent renderer)",
        },
        "api": {
            "callable": "PythonProject1.entrypoints:run_api",
            "description": "Start FastAPI service",
        },
    },
}


