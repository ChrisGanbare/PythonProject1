"""Callable entrypoints for v2_templates project."""

from __future__ import annotations

from typing import Any


def run_render(
    template: str = "bar_chart_race",
    data: dict | None = None,
    brand: str = "default",
    platform: str = "douyin",
    output_file: str = "",
) -> dict[str, Any]:
    """Render a v2 template video via core.v2_renderer."""
    from core.v2_renderer import render_v2_template

    result_path = render_v2_template(
        template_name=template,
        data=data or {},
        brand=brand,
        platform=platform,
        output_path=output_file or None,
    )
    return {"final_video_path": str(result_path), "status": "success"}
