"""Loan-specific validation helpers."""

from __future__ import annotations

from typing import Union

from shared.core.exceptions import ParameterValidationError

Number = Union[int, float]


def validate_loan_amount(amount: Number) -> float:
    try:
        value = float(amount)
    except (TypeError, ValueError) as exc:
        raise ParameterValidationError("loan amount must be numeric", "loan_amount", str(amount), ">=10000") from exc

    if value < 10_000:
        raise ParameterValidationError("loan amount too low", "loan_amount", str(value), ">=10000")
    if value > 10_000_000:
        raise ParameterValidationError("loan amount too high", "loan_amount", str(value), "<=10000000")

    return value


def validate_annual_rate(rate: Number) -> float:
    try:
        value = float(rate)
    except (TypeError, ValueError) as exc:
        raise ParameterValidationError("annual rate must be numeric", "annual_rate", str(rate), "0.001-0.2") from exc

    if value < 0.001:
        raise ParameterValidationError("annual rate too low", "annual_rate", str(value), ">=0.001")
    if value > 0.2:
        raise ParameterValidationError("annual rate too high", "annual_rate", str(value), "<=0.2")

    return value


def validate_loan_years(years: Number) -> int:
    try:
        value = int(years)
    except (TypeError, ValueError) as exc:
        raise ParameterValidationError("loan years must be integer", "loan_years", str(years), "1-40") from exc

    if value < 1:
        raise ParameterValidationError("loan years too low", "loan_years", str(value), ">=1")
    if value > 40:
        raise ParameterValidationError("loan years too high", "loan_years", str(value), "<=40")

    return value
