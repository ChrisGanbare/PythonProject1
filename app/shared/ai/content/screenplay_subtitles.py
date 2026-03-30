"""Subtitle cues derived from a Screenplay + render timeline."""

from __future__ import annotations

from shared.ai.content.render_timeline import build_render_timeline
from shared.ai.content.screenplay import Screenplay


def screenplay_to_subtitle_items(
    screenplay: Screenplay,
    *,
    total_secs: float,
    fps: int,
) -> list[dict[str, float | str]]:
    """Build SRT-style items (start/end/text) aligned to timeline scenes."""
    timeline = build_render_timeline(screenplay, total_secs=total_secs, fps=fps)
    items: list[dict[str, float | str]] = []
    for seg in timeline.scenes:
        text = (seg.narration or "").strip()
        if not text:
            continue
        items.append(
            {
                "start": float(seg.start_seconds),
                "end": float(seg.end_seconds),
                "text": text,
            }
        )
    return items
