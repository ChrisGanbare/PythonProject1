"""Tests for ManimVizBackend — protocol compliance, capabilities, availability check."""

from __future__ import annotations

import pytest

from shared.visualization.backends.manim_backend import (
    QUALITY_FLAGS,
    QUALITY_FOLDERS,
    ManimVizBackend,
)
from shared.visualization.protocol import VizRenderBackend
from shared.visualization.types import VideoFormatSpec


class TestManimVizBackendProtocol:
    """Verify ManimVizBackend satisfies VizRenderBackend protocol."""

    def test_is_protocol_instance(self):
        backend = ManimVizBackend()
        assert isinstance(backend, VizRenderBackend)

    def test_name(self):
        assert ManimVizBackend().name == "manim"

    def test_capabilities_keys(self):
        caps = ManimVizBackend().capabilities()
        assert "animation" in caps
        assert "formula_rendering" in caps
        assert "recommended_for" in caps
        assert isinstance(caps["recommended_for"], list)

    def test_capabilities_values(self):
        caps = ManimVizBackend().capabilities()
        assert caps["animation"] is True
        assert caps["formula_rendering"] is True
        assert caps["dpi_control"] is False  # Manim manages its own pixel pipeline
        assert caps["frame_caching"] is False  # PngCachingFFMpegWriter not applicable


class TestManimAvailability:
    def test_is_available_returns_bool(self):
        result = ManimVizBackend.is_available()
        assert isinstance(result, bool)


class TestQualityMapping:
    def test_quality_flags_coverage(self):
        for q in ("preview", "draft", "final", "4k"):
            assert q in QUALITY_FLAGS, f"missing quality flag: {q}"
            assert q in QUALITY_FOLDERS, f"missing quality folder: {q}"

    def test_flags_are_valid_manim_flags(self):
        for flag in QUALITY_FLAGS.values():
            assert flag.startswith("-q"), f"unexpected flag format: {flag}"


class TestFormatToManimConfig:
    def test_basic_conversion(self):
        fmt = VideoFormatSpec(
            width_px=1920,
            height_px=1080,
            dpi=100,
            fps=60,
            total_duration_secs=30.0,
            total_frames=1800,
        )
        config = ManimVizBackend.format_to_manim_config(fmt)
        assert config["pixel_width"] == 1920
        assert config["pixel_height"] == 1080
        assert config["frame_rate"] == 60

    def test_portrait_format(self):
        fmt = VideoFormatSpec(
            width_px=1080,
            height_px=1920,
            dpi=100,
            fps=30,
            total_duration_secs=15.0,
            total_frames=450,
        )
        config = ManimVizBackend.format_to_manim_config(fmt)
        assert config["pixel_width"] == 1080
        assert config["pixel_height"] == 1920


class TestManimRegistration:
    """Verify that manim backend appears in registry when available."""

    def test_registry_lists_manim_if_installed(self):
        from shared.visualization.registry import list_backends

        backends = list_backends()
        names = [b["name"] for b in backends]
        # matplotlib is always present
        assert "matplotlib" in names
        # manim is present only if the package is installed
        if ManimVizBackend.is_available():
            assert "manim" in names

    def test_get_backend_manim(self):
        from shared.visualization.registry import get_backend

        if ManimVizBackend.is_available():
            backend = get_backend("manim")
            assert backend.name == "manim"
        else:
            with pytest.raises(KeyError):
                get_backend("manim")
