"""Pre-approval checks for screenplays."""

from __future__ import annotations

from shared.ai.content.screenplay import Screenplay


class ScreenplayValidationError(ValueError):
    """Raised when a screenplay fails validation."""


def validate_screenplay_for_approval(screenplay: Screenplay, *, max_scenes: int = 24) -> None:
    """Lightweight gate before marking a version as approved."""
    if not screenplay.scenes:
        raise ScreenplayValidationError("剧本至少包含一个场景")
    if len(screenplay.scenes) > max_scenes:
        raise ScreenplayValidationError(f"场景数量过多（>{max_scenes}），请精简后再定稿")

    for scene in screenplay.scenes:
        if not str(scene.narration or "").strip():
            raise ScreenplayValidationError(f"场景 {scene.id} 缺少旁白文案")
        if not str(scene.visual_prompt or "").strip():
            raise ScreenplayValidationError(f"场景 {scene.id} 缺少画面描述 visual_prompt")

    if screenplay.total_duration_est is not None and screenplay.total_duration_est < 3:
        raise ScreenplayValidationError("预估总时长过短，请检查 total_duration_est")
