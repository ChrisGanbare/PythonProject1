"""Register and resolve visualization backends. Default: matplotlib (efficient for frame animation)."""

from __future__ import annotations

from typing import Any

from shared.visualization.backends.matplotlib_backend import MatplotlibVizBackend

_DEFAULT_NAME = "matplotlib"

_registry: dict[str, Any] = {
    _DEFAULT_NAME: MatplotlibVizBackend(),
}


def register_backend(name: str, backend: Any) -> None:
    if not name:
        raise ValueError("backend name required")
    _registry[name] = backend


def get_backend(name: str | None = None) -> Any:
    """Return backend instance; defaults to matplotlib."""
    key = (name or _DEFAULT_NAME).strip().lower()
    if key not in _registry:
        raise KeyError(f"unknown viz backend '{key}'. Registered: {sorted(_registry)}")
    return _registry[key]


def list_backends() -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for name, backend in sorted(_registry.items()):
        caps = getattr(backend, "capabilities", lambda: {})()
        out.append({"name": name, "capabilities": caps})
    return out


def default_backend_name() -> str:
    return _DEFAULT_NAME
