"""Register and resolve visualization backends. Default: matplotlib (efficient for frame animation)."""

from __future__ import annotations

import logging
from typing import Any

from shared.render.visualization.backends.matplotlib_backend import MatplotlibVizBackend

_log = logging.getLogger(__name__)

_DEFAULT_NAME = "matplotlib"

_registry: dict[str, Any] = {
    _DEFAULT_NAME: MatplotlibVizBackend(),
}

# Lazily register manim if the package is available
try:
    from shared.render.visualization.backends.manim_backend import ManimVizBackend

    _manim = ManimVizBackend()
    if _manim.is_available():
        _registry["manim"] = _manim
    else:
        _log.debug("manim package not installed — backend not registered")
except Exception:  # noqa: BLE001
    _log.debug("manim backend import skipped")


def register_backend(name: str, backend: Any) -> None:
    if not name:
        raise ValueError("backend name required")
    _registry[name] = backend


def get_backend(name: str | None = None) -> Any:
    """Return backend instance; defaults to matplotlib. Falls back to matplotlib if requested backend is unavailable."""
    key = (name or _DEFAULT_NAME).strip().lower()
    if key not in _registry:
        _log.warning(
            "viz backend '%s' not available (not installed?), falling back to '%s'. Registered: %s",
            key,
            _DEFAULT_NAME,
            sorted(_registry),
        )
        return _registry[_DEFAULT_NAME]
    return _registry[key]


def list_backends() -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for name, backend in sorted(_registry.items()):
        caps = getattr(backend, "capabilities", lambda: {})()
        avail = getattr(backend, "is_available", lambda: True)()
        out.append({"name": name, "available": avail, "capabilities": caps})
    return out


def default_backend_name() -> str:
    return _DEFAULT_NAME
