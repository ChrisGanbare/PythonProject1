"""Smoke test for panel_tutor."""

from panel_tutor.entrypoints import run_smoke_check


def test_smoke_check_returns_ok():
    result = run_smoke_check()
    assert result["status"] == "ok"
    assert result["project"] == "panel_tutor"
