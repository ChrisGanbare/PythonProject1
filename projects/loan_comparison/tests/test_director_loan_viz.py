"""Director + loan_compare_main integration."""

from __future__ import annotations

from shared.content.screenplay import Mood, Scene, Screenplay, VisualStyle

from loan_comparison.renderer.director import Director
from loan_comparison.renderer.viz_presets import LOAN_COMPARE_MAIN_VIZ_ID


def test_export_legacy_includes_chart_focus_from_directives() -> None:
    sp = Screenplay(
        title="贷款对比",
        logline="L",
        topic="t",
        target_audience="a",
        mood=Mood.NEUTRAL,
        visual_style=VisualStyle.DATA_DRIVEN,
        scenes=[
            Scene(id="scene_01_hook", duration_est=5, narration="n", visual_prompt="v"),
            Scene(
                id="scene_02_main",
                duration_est=10,
                narration="n",
                visual_prompt="v",
                action_directives={
                    "viz_scene_id": LOAN_COMPARE_MAIN_VIZ_ID,
                    "chart_type": "single_compare",
                },
            ),
            Scene(id="scene_03_out", duration_est=5, narration="n", visual_prompt="v"),
        ],
        total_duration_est=30.0,
    )
    d = Director(sp)
    d.direct()
    legacy = d.export_legacy_config(total_seconds=30, fps=30)
    rex = legacy["render_expression"]
    assert rex["layout"]["chart_focus"] == "single-compare"
