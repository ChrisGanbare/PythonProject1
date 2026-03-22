from __future__ import annotations

from loan_comparison.renderer.viz_backend import describe_viz_backend


def test_describe_viz_backend() -> None:
    d = describe_viz_backend()
    assert d["default_name"] == "matplotlib"
    assert d["active"] == "matplotlib"
