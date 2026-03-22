"""Loan main chart directives -> render_expression.layout."""

from __future__ import annotations

from shared.content.screenplay import Mood, Scene, Screenplay, VisualStyle

from loan_comparison.renderer.viz_presets import (
    LOAN_COMPARE_MAIN_VIZ_ID,
    apply_loan_main_chart_directives,
)


def _base_expr() -> dict:
    return {
        "title_text": "T",
        "scene_behavior": {"comparison_window_months": 60},
        "layout": {},
    }


def test_no_viz_scene_unchanged() -> None:
    sp = Screenplay(
        title="x",
        logline="l",
        topic="t",
        target_audience="a",
        mood=Mood.NEUTRAL,
        visual_style=VisualStyle.DATA_DRIVEN,
        scenes=[
            Scene(id="s1", duration_est=5, narration="n", visual_prompt="v"),
        ],
        total_duration_est=30.0,
    )
    b = _base_expr()
    assert apply_loan_main_chart_directives(sp, b) == b


def test_loan_compare_main_sets_chart_focus() -> None:
    sp = Screenplay(
        title="x",
        logline="l",
        topic="t",
        target_audience="a",
        mood=Mood.NEUTRAL,
        visual_style=VisualStyle.DATA_DRIVEN,
        scenes=[
            Scene(
                id="main_data",
                duration_est=12,
                narration="n",
                visual_prompt="v",
                action_directives={
                    "viz_scene_id": LOAN_COMPARE_MAIN_VIZ_ID,
                    "chart_type": "trend_gap",
                    "comparison_window_months": 120,
                    "reference_style": "flourish_clarity",
                },
            )
        ],
        total_duration_est=30.0,
    )
    out = apply_loan_main_chart_directives(sp, _base_expr())
    assert out["layout"]["chart_focus"] == "trend-gap"
    assert out["scene_behavior"]["comparison_window_months"] == 120
    assert out["scene_behavior"]["show_reference_guides"] is True
    assert out["scene_behavior"]["setup_density"] == "full-context"
