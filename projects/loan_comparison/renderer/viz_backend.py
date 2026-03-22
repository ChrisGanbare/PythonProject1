"""Loan project: expose default matplotlib backend (aligned with scaffold pattern)."""

from __future__ import annotations

from shared.visualization.registry import default_backend_name, get_backend


def describe_viz_backend() -> dict[str, str]:
    b = get_backend()
    return {"default_name": default_backend_name(), "active": b.name}
