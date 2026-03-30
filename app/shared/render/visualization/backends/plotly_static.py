"""
Plotly → static image export (optional dependency).

Use for complex multidimensional charts where matplotlib is cumbersome.
Requires: pip install plotly kaleido

Not registered by default to keep core installs light; call
`register_backend("plotly_static", PlotlyStaticVizBackend())` when needed.
"""

from __future__ import annotations

from typing import Any


class PlotlyStaticVizBackend:
    @property
    def name(self) -> str:
        return "plotly_static"

    def capabilities(self) -> dict[str, Any]:
        return {
            "animation": False,
            "static_png_export": True,
            "optional_dependencies": ["plotly", "kaleido"],
            "recommended_for": ["3d_surface", "complex_interactive_layout_export"],
        }
