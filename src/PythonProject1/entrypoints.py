"""Callable entrypoints exposed for the root scheduler."""

from __future__ import annotations

from PythonProject1.models.loan import LoanData
from PythonProject1.loan_animation_pro import generate_loan_animation


def run_smoke_check() -> dict[str, float]:
    """Quick validation task that does not require ffmpeg/OpenAI."""
    summary = LoanData(loan_amount=1_000_000, annual_rate=0.045, loan_years=30).get_summary()
    result = {
        "equal_interest_total_interest": round(summary["equal_interest"]["total_interest"], 2),
        "equal_principal_total_interest": round(summary["equal_principal"]["total_interest"], 2),
    }
    print("Smoke check passed:", result)
    return result


def run_loan_animation(
    use_original: bool = False,
    output_file: str | None = None,
    width: int | None = None,
    height: int | None = None,
    duration: int | None = None,
    fps: int | None = None,
    loan_amount: float | None = None,
    annual_rate: float | None = None,
    loan_years: int | None = None,
) -> None:
    """Generate the loan comparison animation video."""
    if use_original:
        print("`use_original=true` is no longer needed; using subproject-local original-equivalent renderer.")

    generate_loan_animation(
        output_file=output_file,
        width=width,
        height=height,
        duration=duration,
        fps=fps,
        loan_amount=loan_amount,
        annual_rate=annual_rate,
        loan_years=loan_years,
    )


def run_api(host: str = "0.0.0.0", port: int = 8000) -> None:
    """Start FastAPI service for this subproject."""
    from PythonProject1.main import start_api_server

    start_api_server(host=host, port=port)

