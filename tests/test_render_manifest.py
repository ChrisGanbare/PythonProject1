"""Render manifest helpers."""

from __future__ import annotations

from pathlib import Path

from shared.content.screenplay import AudioCue, Mood, Scene, Screenplay, VisualStyle
from shared.library.render_manifest import (
    MANIFEST_SCHEMA_VERSION,
    build_fund_render_manifest_payload,
    build_render_manifest_payload,
    collect_asset_ids_from_screenplay,
    collect_viz_scene_refs_from_screenplay,
    compute_fund_reproducibility_fingerprint,
    compute_reproducibility_fingerprint,
    write_render_manifest,
)


def test_collect_asset_ids() -> None:
    sp = Screenplay(
        title="x",
        logline="l",
        topic="t",
        target_audience="a",
        mood=Mood.UPBEAT,
        visual_style=VisualStyle.CINEMATIC,
        scenes=[
            Scene(
                id="s1",
                duration_est=5,
                narration="n",
                visual_prompt="v",
                audio_cues=[AudioCue(asset_id="music_upbeat_01")],
            )
        ],
        total_duration_est=10,
    )
    assert "music_upbeat_01" in collect_asset_ids_from_screenplay(sp)


def test_write_manifest(tmp_path: Path) -> None:
    p = tmp_path / "m.json"
    write_render_manifest(p, {"schema_version": MANIFEST_SCHEMA_VERSION, "task_id": "abc"})
    assert p.read_text(encoding="utf-8").strip().startswith("{")


def test_viz_refs_and_manifest_v2(tmp_path: Path) -> None:
    sp = Screenplay(
        title="t",
        logline="l",
        topic="topic",
        target_audience="a",
        mood=Mood.NEUTRAL,
        visual_style=VisualStyle.DATA_DRIVEN,
        scenes=[
            Scene(
                id="intro",
                duration_est=5,
                narration="n",
                visual_prompt="v",
                action_directives={
                    "viz_scene_id": "loan_compare_main",
                    "chart_type": "stacked_bar",
                    "reference_style": "flourish_clarity",
                },
            )
        ],
        total_duration_est=30.0,
    )
    refs = collect_viz_scene_refs_from_screenplay(sp)
    assert refs[0]["viz_scene_id"] == "loan_compare_main"
    assert refs[0]["chart_type"] == "stacked_bar"

    vc = {"width": 1080, "height": 1920, "fps": 30, "total_duration": 30}
    fp1 = compute_reproducibility_fingerprint(
        loan={"loan_amount": 1e6},
        video_config=vc,
        viz_refs=refs,
    )
    fp2 = compute_reproducibility_fingerprint(
        loan={"loan_amount": 1e6},
        video_config=vc,
        viz_refs=refs,
    )
    assert fp1 == fp2
    assert len(fp1) == 64

    out = build_render_manifest_payload(
        task_id="tid",
        final_video=tmp_path / "out.mp4",
        platform="douyin",
        quality="draft",
        video_config=vc,
        loan={"loan_amount": 1e6},
        screenplay=sp,
        scene_schedule=None,
        viz_backend_default="matplotlib",
    )
    assert out["schema_version"] == 2
    assert out["viz"]["default_backend"] == "matplotlib"
    assert out["viz"]["reproducibility_fingerprint"] == fp1


def test_loan_fingerprint_unchanged_shape() -> None:
    """Loan 指纹结构保持不变（与历史 manifest 兼容）。"""
    fp = compute_reproducibility_fingerprint(
        loan={"loan_amount": 1.0},
        video_config={"width": 1080},
        viz_refs=[],
    )
    assert len(fp) == 64


def test_fund_fingerprint_domain() -> None:
    fp = compute_fund_reproducibility_fingerprint(
        fund={"principal": 1e6, "gross_return": 0.08, "years": 30},
        video_config={"width": 1080, "height": 1920},
    )
    assert len(fp) == 64


def test_build_fund_render_manifest_payload(tmp_path) -> None:
    p = build_fund_render_manifest_payload(
        task_id="t1",
        final_video=tmp_path / "f.mp4",
        platform="douyin",
        quality="draft",
        video_config={"width": 1080, "fps": 30, "total_duration": 30},
        fund={"principal": 1e6, "gross_return": 0.08, "years": 30},
    )
    assert p["project"] == "fund_fee_erosion"
    assert p["fund"]["principal"] == 1e6
    assert len(p["viz"]["reproducibility_fingerprint"]) == 64
