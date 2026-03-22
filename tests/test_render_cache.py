"""render_cache helpers."""

from __future__ import annotations

from shared.visualization.render_cache import render_cache_dir, sanitize_cache_segment


def test_sanitize_cache_segment() -> None:
    assert "hello" in sanitize_cache_segment("Hello World!")


def test_render_cache_dir(tmp_path, monkeypatch):
    class _S:
        cache_dir = tmp_path

    monkeypatch.setattr("shared.visualization.render_cache.settings", _S())
    p = render_cache_dir("loan_comparison", "a" * 64)
    assert p.parent.name == "loan_comparison"
    assert len(p.name) == 32
