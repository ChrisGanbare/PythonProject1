"""Render timeline tests."""

from __future__ import annotations

from shared.ai.content.ai_planner import ai_planner
from shared.ai.content.render_timeline import build_render_timeline


def _sample_screenplay():
    return ai_planner.preview_screenplay(
        topic="时间线测试",
        style="tech",
        target_audience="测试用户",
        platform="douyin",
        context={
            "interest_difference_text": "14.7万",
            "which_is_cheaper": "等额本金",
            "loan_amount_text": "100万",
            "loan_years_text": "30年",
        },
    ).screenplay


def test_build_render_timeline_scene_segments_cover_total_frames() -> None:
    timeline = build_render_timeline(_sample_screenplay(), total_secs=6, fps=24)

    assert timeline.total_frames == 144
    assert timeline.scenes
    assert timeline.scenes[0].start_frame == 0
    assert timeline.scenes[0].scene_id == "scene_01_hook"
    assert timeline.scenes[0].scene_label == "Hook"
    assert timeline.scenes[0].scene_ids == [timeline.scenes[0].scene_id]
    assert timeline.scenes[0].narration
    assert timeline.scenes[0].visual_prompt
    assert timeline.scenes[0].mood
    assert timeline.scenes[0].pacing_token == "hook_reveal"
    assert timeline.scenes[-1].end_frame == timeline.total_frames
    assert sum(segment.duration_frames for segment in timeline.scenes) == timeline.total_frames

    for previous, current in zip(timeline.scenes, timeline.scenes[1:]):
        assert previous.end_frame == current.start_frame
        assert previous.duration_frames > 0
        assert current.scene_id == current.scene_ids[0]
        assert current.scene_label
        assert current.narration
        assert current.visual_prompt
        assert current.mood
        assert current.pacing_token


def test_render_timeline_resolves_phase_and_scene_by_frame() -> None:
    timeline = build_render_timeline(_sample_screenplay(), total_secs=6, fps=24)

    assert timeline.get_phase_for_frame(0).role == "intro"
    assert timeline.get_scene_for_frame(0).scene_id == "scene_01_hook"
    assert timeline.get_scene_for_frame(0).scene_label == "Hook"
    assert timeline.get_scene_for_frame(0).pacing_token == "hook_reveal"
    assert timeline.get_scene_for_frame(0).scene_ids[0] == "scene_01_hook"

    main_start = timeline.get_phase("main").start_frame
    main_scene = timeline.get_scene_for_frame(main_start)
    assert timeline.get_phase_for_frame(main_start).role == "main"
    assert main_scene is not None
    assert main_scene.scene_label
    assert main_scene.narration
    assert main_scene.visual_prompt
    assert main_scene.mood
    assert main_scene.pacing_token in {"compare_build", "compare_surge"}
    assert main_scene.scene_ids[0] in {"scene_02_setup", "scene_03_climax"}

    assert timeline.get_phase_for_frame(-10).role == "intro"
    assert timeline.get_scene_for_frame(999).scene_id == "scene_04_conclusion"
    assert timeline.get_scene_for_frame(999).scene_label == "Conclusion"
    assert timeline.get_scene_for_frame(999).pacing_token in {"conclusion_hold", "conclusion_cta"}
    assert timeline.get_scene_for_frame(999).scene_ids[0] == "scene_04_conclusion"
    assert timeline.get_phase_for_frame(timeline.total_frames - 1).role == "conclusion"


def test_render_timeline_emits_stable_scene_schedule_log_lines() -> None:
    timeline = build_render_timeline(_sample_screenplay(), total_secs=6, fps=24)

    records = timeline.scene_schedule_records()
    lines = timeline.scene_schedule_log_lines()

    assert len(records) == len(timeline.scenes)
    assert len(lines) == len(timeline.scenes)
    assert records[0]["scene_id"] == "scene_01_hook"
    assert records[0]["pacing_token"] == "hook_reveal"
    assert records[0]["mood"]
    assert records[0]["visual_prompt"]
    assert records[0]["duration_seconds"] > 0
    assert records[-1]["scene_id"] == "scene_04_conclusion"
    assert lines[0].startswith("scene_schedule :: role=intro :: scene_id=scene_01_hook")
    assert " :: token=hook_reveal :: " in lines[0]
    assert " :: label=Conclusion :: " in lines[-1]

    exported = timeline.export_schedule_payload()
    assert exported["scenes"][0]["mood"]
    assert exported["scenes"][0]["visual_prompt"]


