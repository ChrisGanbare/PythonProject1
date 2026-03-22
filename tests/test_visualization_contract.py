"""shared.visualization contract and registry."""

from __future__ import annotations

from shared.visualization import (
    default_backend_name,
    frame_request_from_env,
    get_backend,
    list_backends,
)
from shared.visualization.registry import register_backend
from shared.visualization.backends.plotly_static import PlotlyStaticVizBackend


def test_default_backend_is_matplotlib() -> None:
    assert default_backend_name() == "matplotlib"
    b = get_backend()
    assert b.name == "matplotlib"
    assert get_backend("matplotlib").name == "matplotlib"


def test_list_backends() -> None:
    names = {x["name"] for x in list_backends()}
    assert "matplotlib" in names


def test_frame_request_from_env(monkeypatch) -> None:
    monkeypatch.setenv("VIDEO_WIDTH", "1080")
    monkeypatch.setenv("VIDEO_HEIGHT", "1920")
    monkeypatch.setenv("VIDEO_FPS", "30")
    monkeypatch.setenv("VIDEO_DURATION", "30")
    monkeypatch.setenv("VIDEO_DPI", "100")
    fr = frame_request_from_env()
    assert fr.format.width_px == 1080
    assert fr.format.height_px == 1920
    assert fr.format.total_frames >= 1


def test_optional_plotly_register() -> None:
    register_backend("plotly_static", PlotlyStaticVizBackend())
    p = get_backend("plotly_static")
    assert p.name == "plotly_static"
