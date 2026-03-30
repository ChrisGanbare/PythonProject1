from __future__ import annotations

import pytest

from shared.ai.content.screenplay import Mood, Scene, Screenplay, VisualStyle
from shared.ai.content.screenplay_validate import ScreenplayValidationError, validate_screenplay_for_approval


def test_validate_ok() -> None:
    sp = Screenplay(
        title="t",
        logline="l",
        topic="x",
        target_audience="a",
        mood=Mood.NEUTRAL,
        visual_style=VisualStyle.DATA_DRIVEN,
        scenes=[
            Scene(
                id="s1",
                duration_est=5,
                narration="n",
                visual_prompt="vp",
            )
        ],
        total_duration_est=30.0,
    )
    validate_screenplay_for_approval(sp)


def test_validate_empty_scenes() -> None:
    sp = Screenplay(
        title="t",
        logline="l",
        topic="x",
        target_audience="a",
        scenes=[],
        total_duration_est=30.0,
    )
    with pytest.raises(ScreenplayValidationError):
        validate_screenplay_for_approval(sp)
