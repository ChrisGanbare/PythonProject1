"""PNG frame cache helpers."""

from pathlib import Path

import pytest

from shared.render.visualization.png_frame_cache import (
    all_frames_cached,
    encode_video_from_png_sequence_ffmpeg,
    frame_png_path,
)


def test_frame_png_path():
    p = frame_png_path(Path("/tmp/c"), 42)
    assert p == Path("/tmp/c/frame_000042.png")


def test_all_frames_cached(tmp_path):
    d = tmp_path / "c"
    d.mkdir()
    assert not all_frames_cached(d, 3)
    for i in range(3):
        (d / f"frame_{i:06d}.png").write_bytes(b"x")
    assert all_frames_cached(d, 3)
    assert not all_frames_cached(d, 4)


@pytest.mark.skipif(
    __import__("shutil").which("ffmpeg") is None,
    reason="ffmpeg not installed",
)
def test_encode_video_from_png_sequence_ffmpeg(tmp_path):
    from PIL import Image

    d = tmp_path / "frames"
    d.mkdir()
    for i in range(2):
        img = Image.new("RGBA", (32, 24), (10, 20, 30, 255))
        img.save(frame_png_path(d, i))
    out = tmp_path / "out.mp4"
    ok = encode_video_from_png_sequence_ffmpeg(
        out,
        d,
        2,
        fps=10,
        bitrate=500,
        preset="ultrafast",
        crf=30,
    )
    assert ok is True
    assert out.is_file() and out.stat().st_size > 100
