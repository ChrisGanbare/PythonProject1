"""Tests for SQLite screenplay versioning."""

from __future__ import annotations

from pathlib import Path

import pytest

from shared.content.screenplay import Mood, Scene, Screenplay, VisualStyle
from shared.library.screenplay_store import ScreenplayStore, ScriptVersionStatus


def _minimal_screenplay(title: str = "T") -> Screenplay:
    return Screenplay(
        title=title,
        logline="L",
        topic="topic",
        target_audience="aud",
        mood=Mood.NEUTRAL,
        visual_style=VisualStyle.DATA_DRIVEN,
        scenes=[
            Scene(
                id="scene_1",
                duration_est=8.0,
                narration="hello",
                visual_prompt="chart",
            )
        ],
        total_duration_est=30.0,
    )


def test_create_and_versioning(tmp_path: Path) -> None:
    store = ScreenplayStore(db_path=tmp_path / "x.db")
    sid = store.create_script(goal="科普", platform="douyin", topic="房贷")
    v1 = store.add_version(sid, _minimal_screenplay("v1"), status=ScriptVersionStatus.DRAFT)
    assert v1 == 1
    v2 = store.add_version(sid, _minimal_screenplay("v2"), status=ScriptVersionStatus.DRAFT, parent_version=1)
    assert v2 == 2
    latest = store.get_version(sid, None)
    assert latest is not None
    assert latest.version == 2
    assert latest.screenplay.title == "v2"
    store.set_version_status(sid, 2, ScriptVersionStatus.APPROVED)
    assert store.get_version(sid, 2) is not None
    assert store.get_version(sid, 2).status == ScriptVersionStatus.APPROVED


def test_unknown_script_raises(tmp_path: Path) -> None:
    store = ScreenplayStore(db_path=tmp_path / "y.db")
    with pytest.raises(ValueError, match="unknown script_id"):
        store.add_version("nope", _minimal_screenplay())
