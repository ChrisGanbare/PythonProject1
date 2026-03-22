"""Loan comparison: bind screenplay `action_directives` to impl.py layout knobs."""

from __future__ import annotations

from typing import Any

from shared.content.screenplay import Screenplay

# 与 manifest `viz.scene_refs`、剧本约定一致：标记「贷款对比主图」场景
LOAN_COMPARE_MAIN_VIZ_ID = "loan_compare_main"

# chart_type（剧本侧） -> impl.py 的 LAYOUT_HINTS.chart_focus
_CHART_TYPE_TO_FOCUS: dict[str, str] = {
    "dual_cumulative": "balanced",  # 双累计曲线 + 经典分区（默认主图）
    "stacked_bar": "single-compare",
    "single_compare": "single-compare",
    "gap_emphasis": "trend-gap",
    "trend_gap": "trend-gap",
}


def apply_loan_main_chart_directives(screenplay: Screenplay, render_expression: dict[str, Any]) -> dict[str, Any]:
    """
    若某场景的 `viz_scene_id == loan_compare_main`，则把 `chart_type` 等写入
    `render_expression.layout` / `scene_behavior`，供 impl 主图区使用。
    """
    target = None
    for scene in screenplay.scenes:
        ad = scene.action_directives or {}
        if ad.get("viz_scene_id") == LOAN_COMPARE_MAIN_VIZ_ID:
            target = ad
            break
    if target is None:
        return render_expression

    out = {**render_expression}
    layout = dict(out.get("layout") or {})
    scene_behavior = dict(out.get("scene_behavior") or {})

    raw_type = str(target.get("chart_type") or "dual_cumulative").lower().replace("-", "_")
    chart_focus = _CHART_TYPE_TO_FOCUS.get(raw_type, "balanced")
    layout["chart_focus"] = chart_focus

    if "comparison_window_months" in target:
        try:
            scene_behavior["comparison_window_months"] = int(target["comparison_window_months"])
        except (TypeError, ValueError):
            pass

    ref = str(target.get("reference_style") or "").lower()
    if ref in {"flourish_clarity", "nyt_guides", "data_news_dense"}:
        scene_behavior["show_reference_guides"] = True
        scene_behavior.setdefault("setup_density", "full-context")

    out["layout"] = layout
    out["scene_behavior"] = scene_behavior
    return out
