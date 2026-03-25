"""Smoke test for my_tutor."""

from my_tutor.entrypoints import run_smoke_check


def test_smoke_check_returns_ok():
    result = run_smoke_check()
    assert result["status"] == "ok"
    assert result["project"] == "my_tutor"
