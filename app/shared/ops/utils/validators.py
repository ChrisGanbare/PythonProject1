"""Generic validation helpers."""

from __future__ import annotations

from typing import Union

from shared.render.core.exceptions import ParameterValidationError

Number = Union[int, float]


def validate_range(
    value: Number,
    min_val: Number,
    max_val: Number,
    parameter_name: str,
) -> Number:
    """Raise ParameterValidationError if value is outside [min_val, max_val]."""
    try:
        numeric = type(value)(value)
    except (TypeError, ValueError) as exc:
        raise ParameterValidationError(
            f"{parameter_name} must be numeric",
            parameter_name,
            str(value),
            f"{min_val}-{max_val}",
        ) from exc

    if numeric < min_val:
        raise ParameterValidationError(
            f"{parameter_name} too low",
            parameter_name,
            str(numeric),
            f">={min_val}",
        )
    if numeric > max_val:
        raise ParameterValidationError(
            f"{parameter_name} too high",
            parameter_name,
            str(numeric),
            f"<={max_val}",
        )
    return numeric
