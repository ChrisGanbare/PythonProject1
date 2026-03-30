"""
Matplotlib — default backend for data-viz video.

Best balance of: frame-level control, mature stack, FFmpeg-friendly animation,
and alignment with existing project renderers (impl.py subprocess pattern).
"""

from __future__ import annotations

from typing import Any


class MatplotlibVizBackend:
    @property
    def name(self) -> str:
        return "matplotlib"

    def capabilities(self) -> dict[str, Any]:
        return {
            "animation": True,
            "vector_text": True,
            "ffmpeg_export": True,
            "dpi_control": True,
            "recommended_for": ["bar_race", "line_chart", "small_multiples", "loan_schedules"],
        }
