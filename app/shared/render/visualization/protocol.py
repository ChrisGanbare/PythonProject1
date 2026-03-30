"""Protocol for pluggable visualization backends."""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class VizRenderBackend(Protocol):
    """Renders data visualization frames or clips (matplotlib, plotly static export, etc.)."""

    @property
    def name(self) -> str: ...

    def capabilities(self) -> dict[str, Any]:
        """Machine-readable feature flags for manifests and UI."""
        ...
