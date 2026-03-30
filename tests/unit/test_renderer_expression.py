"""Renderer expression propagation tests."""

from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

from shared.ai.content.render_mapping import build_render_expression
from shared.ai.content.ai_planner import ai_planner
from shared.ai.content.schemas import ContentBrief, ContentStyle, ContentVariant
from loan_comparison.renderer.animation import generate_loan_animation
from loan_comparison.renderer.animation import resolve_scene_schedule_sidecar_path
from loan_comparison.entrypoints import run_scene_schedule_preview
from fund_fee_erosion.renderer.animation import generate_fund_animation


def _sample_expression(platform: str = "douyin"):
    from shared.ai.content.planner import build_content_plan

    plan = build_content_plan(
        ContentBrief(
            topic="测试标题",
            platform=platform,
            style=ContentStyle.TECH,
            variant=ContentVariant.SHORT,
            total_duration=30,
            hook_fact="开场钩子",
            setup_fact="展开信息",
            climax_fact="高潮信息",
            conclusion_fact="结论信息",
            call_to_action="行动建议",
        )
    )
    return build_render_expression(plan)


def test_generate_loan_animation_passes_render_expression(monkeypatch, tmp_path: Path) -> None:
    captured_env: dict[str, str] = {}
    output_file = tmp_path / "loan.mp4"

    def fake_run(command, cwd, env, capture_output, text, encoding, errors):
        del command, cwd, capture_output, text, encoding, errors
        captured_env.update(env)
        output_file.write_bytes(b"video")
        return SimpleNamespace(returncode=0, stdout="ok", stderr="")

    monkeypatch.setattr("loan_comparison.renderer.animation.subprocess.run", fake_run)

    result = generate_loan_animation(
        output_file=output_file,
        render_expression=_sample_expression(),
    )

    assert result == output_file
    assert "VIDEO_RENDER_EXPRESSION" in captured_env
    assert "测试标题" in captured_env["VIDEO_RENDER_EXPRESSION"]
    payload = json.loads(captured_env["VIDEO_RENDER_EXPRESSION"])
    assert payload["theme"]["theme_name"]
    assert payload["theme"]["panel_color"]
    assert payload["card"]["background_color"]
    assert payload["safe_area"]["platform"] == "douyin"
    assert payload["safe_area"]["bottom_px"] == 300
    assert payload["safe_area"]["subtitle_band_top"] < 1.0
    assert payload["scene_copy_band"]["platform"] == "douyin"
    assert payload["scene_copy_band"]["orientation"] == "vertical"
    assert payload["scene_copy_band"]["full"]["h"] > payload["scene_copy_band"]["compact"]["h"]
    assert payload["scene_copy_band"]["background_color"]
    assert payload["scene_copy_band"]["border_color"]
    assert payload["scene_copy_band"]["headline_color"]
    assert payload["scene_copy_band"]["detail_color"]
    assert payload["scene_copy_band"]["full_fill_alpha"] > 0
    assert payload["subtitle_layout"]["platform"] == "douyin"
    assert payload["subtitle_layout"]["anchor"] == "bottom"
    assert payload["subtitle_styles"]["hook_emphasis"]["style_token"] == "hook_emphasis"
    assert payload["subtitle_cues"][0]["style_token"] == "hook_emphasis"
    assert payload["cover"]["title_text"] == "测试标题"
    assert payload["cover"]["highlight_text"]
    assert payload["scene_behavior"]["hook_mode"] == "hero-spotlight"
    assert payload["scene_behavior"]["comparison_window_months"] > 0
    assert payload["typography"]["font_family"]
    assert payload["typography"]["font_fallbacks"]
    assert payload["typography"]["title_weight"]
    assert payload["typography"]["body_line_height"] > 1.0
    assert payload["typography"]["title_size"] > payload["typography"]["body_size"]
    assert payload["layout"]["hook_layout"]
    assert payload["visual_cues"]["conclusion_focus"]
    assert payload["visual_focus"]
    assert payload["typography"]["title_scale"] > 0
    assert payload["card"]["border_width"] > 0


def test_generate_fund_animation_passes_render_expression(monkeypatch, tmp_path: Path) -> None:
    captured_env: dict[str, str] = {}
    output_file = tmp_path / "fund.mp4"

    def fake_run(command, cwd, env, capture_output, text, encoding, errors):
        del command, cwd, capture_output, text, encoding, errors
        captured_env.update(env)
        output_file.write_bytes(b"video")
        return SimpleNamespace(returncode=0, stdout="ok", stderr="")

    monkeypatch.setattr("fund_fee_erosion.renderer.animation.subprocess.run", fake_run)

    result = generate_fund_animation(
        output_file=output_file,
        render_expression=_sample_expression(),
    )

    assert result == output_file
    assert "VIDEO_RENDER_EXPRESSION" in captured_env
    assert "测试标题" in captured_env["VIDEO_RENDER_EXPRESSION"]
    payload = json.loads(captured_env["VIDEO_RENDER_EXPRESSION"])
    assert payload["theme"]["theme_name"]
    assert payload["theme"]["muted_text_color"]
    assert payload["card"]["title_color"]
    assert payload["safe_area"]["frame_width"] == 1080
    assert payload["safe_area"]["frame_height"] == 1920
    assert payload["scene_copy_band"]["compact"]["headline_scale"] > 0
    assert payload["scene_copy_band"]["side_padding_ratio"] >= 0
    assert payload["scene_copy_band"]["compact_fill_alpha"] >= payload["scene_copy_band"]["full_fill_alpha"]
    assert payload["subtitle_layout"]["max_width_ratio"] > 0.7
    assert payload["subtitle_styles"]["conclusion_cta"]["text_color"]
    assert payload["subtitle_cues"][-1]["style_token"] == "conclusion_cta"
    assert payload["cover"]["layout"]
    assert payload["scene_behavior"]["conclusion_mode"]
    assert payload["scene_behavior"]["conclusion_reveal_order"]
    assert payload["typography"]["numeric_font_family"]
    assert payload["typography"]["subtitle_weight"]
    assert payload["typography"]["caption_line_height"] > 1.0
    assert payload["typography"]["subtitle_size"] > 0
    assert payload["layout"]["chart_focus"]
    assert payload["visual_cues"]["hook_focus"]
    assert payload["visual_focus"]
    assert payload["typography"]["summary_scale"] > 0
    assert payload["card"]["boxstyle"]


def test_generate_loan_animation_merges_screenplay_timeline(monkeypatch, tmp_path: Path) -> None:
    captured_env: dict[str, str] = {}
    output_file = tmp_path / "screenplay-loan.mp4"

    def fake_run(command, cwd, env, capture_output, text, encoding, errors):
        del command, cwd, capture_output, text, encoding, errors
        captured_env.update(env)
        output_file.write_bytes(b"video")
        return SimpleNamespace(returncode=0, stdout="ok", stderr="")

    monkeypatch.setattr("loan_comparison.renderer.animation.subprocess.run", fake_run)

    screenplay_result = ai_planner.preview_screenplay(
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
    )

    result = generate_loan_animation(
        output_file=output_file,
        width=720,
        height=1280,
        duration=6,
        fps=24,
        loan_amount=1_000_000,
        annual_rate=0.045,
        loan_years=30,
        screenplay=screenplay_result.screenplay,
    )

    assert result == output_file
    payload = json.loads(captured_env["VIDEO_RENDER_EXPRESSION"])
    assert payload["title_text"]
    assert payload["hook_text"]
    assert payload["timeline"]["phases"]
    assert payload["timeline"]["scenes"]
    assert payload["timeline"]["total_frames"] == 6 * 24
    assert {phase["role"] for phase in payload["timeline"]["phases"]} >= {"intro", "main", "conclusion"}
    assert payload["timeline"]["scenes"][0]["scene_id"] == "scene_01_hook"
    assert payload["timeline"]["scenes"][0]["scene_label"] == "Hook"
    assert payload["timeline"]["scenes"][0]["scene_ids"][0] == "scene_01_hook"
    assert payload["timeline"]["scenes"][0]["narration"]
    assert payload["timeline"]["scenes"][0]["visual_prompt"]
    assert payload["timeline"]["scenes"][0]["mood"]
    assert payload["timeline"]["scenes"][0]["pacing_token"] == "hook_reveal"
    assert payload["timeline"]["scenes"][-1]["scene_ids"][0] == "scene_04_conclusion"

    sidecar_path = resolve_scene_schedule_sidecar_path(output_file)
    assert sidecar_path.exists()
    schedule_payload = json.loads(sidecar_path.read_text(encoding="utf-8"))
    assert schedule_payload["total_frames"] == 6 * 24
    assert schedule_payload["scenes"][0]["scene_id"] == "scene_01_hook"
    assert schedule_payload["log_lines"][0].startswith("scene_schedule :: role=intro")


def test_generate_loan_animation_preserves_explicit_render_expression_when_merging_screenplay(
    monkeypatch,
    tmp_path: Path,
) -> None:
    captured_env: dict[str, str] = {}
    output_file = tmp_path / "screenplay-merge-loan.mp4"

    def fake_run(command, cwd, env, capture_output, text, encoding, errors):
        del command, cwd, capture_output, text, encoding, errors
        captured_env.update(env)
        output_file.write_bytes(b"video")
        return SimpleNamespace(returncode=0, stdout="ok", stderr="")

    monkeypatch.setattr("loan_comparison.renderer.animation.subprocess.run", fake_run)

    screenplay_result = ai_planner.preview_screenplay(
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
    )

    render_expression = _sample_expression()
    result = generate_loan_animation(
        output_file=output_file,
        width=720,
        height=1280,
        duration=6,
        fps=24,
        loan_amount=1_000_000,
        annual_rate=0.045,
        loan_years=30,
        screenplay=screenplay_result.screenplay,
        render_expression=render_expression,
    )

    assert result == output_file
    payload = json.loads(captured_env["VIDEO_RENDER_EXPRESSION"])
    assert payload["title_text"] == "测试标题"
    assert payload["theme"]["theme_name"] == render_expression.theme.theme_name
    assert payload["safe_area"]["bottom_px"] == 300
    assert payload["timeline"]["total_frames"] == 6 * 24
    assert payload["timeline"]["scenes"][1]["scene_id"] == "scene_02_setup"
    assert payload["timeline"]["scenes"][1]["scene_label"] == "Setup"
    assert payload["timeline"]["scenes"][1]["narration"]
    assert payload["timeline"]["scenes"][1]["visual_prompt"]
    assert payload["timeline"]["scenes"][1]["mood"]
    assert payload["timeline"]["scenes"][1]["pacing_token"] == "compare_build"
    assert payload["timeline"]["scenes"][1]["scene_ids"][0] == "scene_02_setup"
    assert payload["scene_copy_band"]["label_color"]
    assert payload["scene_copy_band"]["accent_color"]


def test_run_scene_schedule_preview_returns_dashboard_ready_payload() -> None:
    result = run_scene_schedule_preview(platform="douyin", duration=6, fps=24, style="tech", topic="时间线预览")

    assert result["platform"] == "douyin"
    assert result["duration"] == 6
    assert result["fps"] == 24
    schedule = result["scene_schedule"]
    assert schedule["total_frames"] == 6 * 24
    assert schedule["scenes"]
    assert schedule["scenes"][0]["scene_id"] == "scene_01_hook"
    assert schedule["log_lines"][0].startswith("scene_schedule :: role=intro")


