"""Shared video pipeline tests."""

from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np

from shared.config.settings import settings
from shared.content.planner import build_content_plan
from shared.content.render_mapping import build_render_expression
from shared.content.schemas import ContentBrief, ContentStyle, ContentVariant
from shared.core.task_manager import TaskManager, TaskStatus
from shared.media.video_editor import VideoEditor
from shared.platform.presets import get_platform_preset
from shared.platform.video_request import PlatformName, PlatformRenderRequest, RenderQuality


def _create_sample_video(video_path: Path) -> None:
    frame_size = (320, 240)
    writer = cv2.VideoWriter(
        str(video_path),
        cv2.VideoWriter_fourcc(*"MJPG"),
        10.0,
        frame_size,
    )
    assert writer.isOpened(), "测试视频写入器初始化失败"

    try:
        for color in [(255, 0, 0), (0, 255, 0), (0, 0, 255)]:
            frame = np.zeros((frame_size[1], frame_size[0], 3), dtype=np.uint8)
            frame[:, :] = color
            writer.write(frame)
    finally:
        writer.release()


def test_platform_request_builds_quality_aware_video_config() -> None:
    request = PlatformRenderRequest(
        platform=PlatformName.DOUYIN,
        quality=RenderQuality.PREVIEW,
        video_duration=30,
    )

    config = request.build_video_config(settings.video)

    assert config.width == 1080
    assert config.height == 1920
    assert config.fps == 30
    assert config.total_duration == 30
    assert config.dpi == 72
    assert config.bitrate == 4000
    assert config.crf == 28
    assert config.preset == "veryfast"


def test_platform_preset_exposes_safe_area_ratios() -> None:
    preset = get_platform_preset("douyin")

    assert preset.safe_bottom == 300
    assert round(preset.safe_bottom_ratio, 4) == round(300 / 1920, 4)
    safe_area = preset.to_safe_area_dict()
    assert safe_area["platform"] == "douyin"
    assert safe_area["frame_width"] == 1080
    assert safe_area["content_bottom"] == preset.safe_bottom_ratio
    assert safe_area["subtitle_band_top"] == 1.0 - preset.safe_bottom_ratio
    subtitle_layout = preset.to_subtitle_layout_dict()
    assert subtitle_layout["anchor"] == "bottom"
    assert subtitle_layout["max_lines"] == 3
    assert subtitle_layout["bottom_px"] == 300

    scene_copy_band = preset.to_scene_copy_band_dict()
    assert scene_copy_band["platform"] == "douyin"
    assert scene_copy_band["orientation"] == "vertical"
    assert scene_copy_band["full"]["h"] > scene_copy_band["compact"]["h"]
    assert scene_copy_band["compact"]["y"] >= 60


def test_task_manager_persists_metadata(tmp_path: Path) -> None:
    manager = TaskManager(storage_dir=tmp_path)
    task_id = manager.create_task(metadata={"platform": "douyin", "quality": "preview"})
    manager.update_task(
        task_id,
        status=TaskStatus.COMPLETED,
        metadata={
            "output_file": "demo.mp4",
            "rendered_video_path": "demo.rendered.mp4",
            "final_video_path": "demo.final.mp4",
            "subtitle_burned": True,
            "bgm_applied": True,
        },
    )

    reloaded = TaskManager(storage_dir=tmp_path)
    task = reloaded.get_task(task_id)

    assert task is not None
    assert task.metadata["platform"] == "douyin"
    assert task.metadata["quality"] == "preview"
    assert task.metadata["output_file"] == "demo.mp4"
    assert task.metadata["rendered_video_path"] == "demo.rendered.mp4"
    assert task.metadata["final_video_path"] == "demo.final.mp4"
    assert task.metadata["subtitle_burned"] is True
    assert task.metadata["bgm_applied"] is True
    assert task.created_at.tzinfo is not None
    assert task.updated_at.tzinfo is not None


def test_video_editor_writes_srt_and_extracts_cover(tmp_path: Path) -> None:
    editor = VideoEditor()
    video_path = tmp_path / "sample.avi"
    subtitle_path = tmp_path / "sample.srt"
    cover_path = tmp_path / "sample.png"
    _create_sample_video(video_path)

    editor.write_srt(
        [
            {"start": 0.0, "end": 1.5, "text": "第一句字幕", "style_token": "hook_emphasis", "beat_type": "hook"},
            {"start": 1.5, "end": 3.0, "text": "第二句字幕", "style_token": "body_explainer", "beat_type": "setup"},
        ],
        subtitle_path,
    )
    editor.extract_cover_frame(video_path, cover_path, timestamp_seconds=0.1)
    video_info = editor.get_video_info(video_path)

    subtitle_content = subtitle_path.read_text(encoding="utf-8")
    assert "第一句字幕" in subtitle_content
    assert "00:00:00,000 --> 00:00:01,500" in subtitle_content
    assert cover_path.exists()
    assert cover_path.stat().st_size > 0
    assert video_info["file_size"] > 0
    assert video_info["resolution"] == "320x240"
    assert video_info["duration"] > 0


def test_video_editor_generates_cover_template_from_render_expression(tmp_path: Path) -> None:
    editor = VideoEditor()
    cover_path = tmp_path / "template_cover.png"
    plan = build_content_plan(
        ContentBrief(
            topic="基金费率长期影响",
            platform="douyin",
            style=ContentStyle.TECH,
            variant=ContentVariant.SHORT,
            total_duration=30,
            hook_fact="先看最关键结论",
            setup_fact="再补背景信息",
            climax_fact="关键差额数字出现",
            conclusion_fact="最后给出判断",
            call_to_action="关注长期费率",
        )
    )
    expression = build_render_expression(plan)

    result = editor.generate_cover_image(cover_path, render_expression=expression)

    assert result == cover_path
    assert cover_path.exists()
    assert cover_path.stat().st_size > 0


def test_video_editor_writes_ass_from_render_expression(tmp_path: Path) -> None:
    editor = VideoEditor()
    subtitle_path = tmp_path / "styled.ass"
    plan = build_content_plan(
        ContentBrief(
            topic="字幕样式化测试",
            platform="douyin",
            style=ContentStyle.TECH,
            variant=ContentVariant.SHORT,
            total_duration=30,
            hook_fact="先看开场",
            setup_fact="再看解释",
            climax_fact="最后给高潮数字",
            conclusion_fact="一句话收尾",
            call_to_action="关注后续更新",
        )
    )
    expression = build_render_expression(plan)

    result = editor.write_ass(plan.to_subtitle_items(), subtitle_path, render_expression=expression)

    assert result == subtitle_path
    content = subtitle_path.read_text(encoding="utf-8")
    assert "[V4+ Styles]" in content
    assert f"Style: hook_emphasis,{expression.subtitle_styles.hook_emphasis.font_family}" in content
    assert f"Style: body_explainer,{expression.subtitle_styles.body_explainer.font_family}" in content
    assert "Dialogue: 0," in content
    assert "hook_emphasis" in content


def test_video_editor_composes_final_video_with_subtitle_and_audio(monkeypatch, tmp_path: Path) -> None:
    editor = VideoEditor()
    rendered_video = tmp_path / "rendered.mp4"
    subtitle_path = tmp_path / "subtitle.srt"
    bgm_path = tmp_path / "bgm.mp3"
    final_video = tmp_path / "final.mp4"
    rendered_video.write_bytes(b"rendered")
    subtitle_path.write_text("demo", encoding="utf-8")
    bgm_path.write_bytes(b"bgm")

    calls: list[tuple[str, Path, Path]] = []

    def fake_add_subtitle(input_video: Path, subtitle_file: Path, output_video: Path, subtitle_codec: str = "mov_text") -> Path:
        del subtitle_codec
        calls.append(("subtitle", input_video, output_video))
        output_video.write_bytes(b"subtitle")
        return output_video

    def fake_add_audio(
        input_video: Path,
        audio_file: Path,
        output_video: Path,
        loop_audio: bool = True,
        audio_volume: float = 0.3,
        video_audio_volume: float = 1.0,
        ducking_enabled: bool = True,
        ducking_strength: float = 0.6,
    ) -> Path:
        del audio_file, loop_audio, audio_volume, video_audio_volume, ducking_enabled, ducking_strength
        calls.append(("audio", input_video, output_video))
        output_video.write_bytes(b"final")
        return output_video

    monkeypatch.setattr(editor, "add_subtitle", fake_add_subtitle)
    monkeypatch.setattr(editor, "add_audio", fake_add_audio)

    result = editor.compose_final_video(
        rendered_video=rendered_video,
        final_video=final_video,
        subtitle_file=subtitle_path,
        burn_subtitles=True,
        background_music=bgm_path,
    )

    assert result == final_video
    assert final_video.exists()
    assert [name for name, *_ in calls] == ["subtitle", "audio"]


