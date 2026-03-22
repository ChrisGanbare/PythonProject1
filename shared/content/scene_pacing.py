"""Scene pacing token registry and helpers."""

from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class ScenePacingProfile:
    token: str
    speed: float = 1.0
    window: float = 1.0
    branch_delay: float = 1.0
    reveal: float = 1.0

    def to_dict(self) -> dict[str, float | str]:
        return dict(asdict(self))


SCENE_PACING_REGISTRY: dict[str, ScenePacingProfile] = {
    "hook_reveal": ScenePacingProfile("hook_reveal", speed=1.15, window=0.90, branch_delay=0.82, reveal=1.12),
    "intro_setup": ScenePacingProfile("intro_setup", speed=1.04, window=1.00, branch_delay=1.00, reveal=1.00),
    "intro_glide": ScenePacingProfile("intro_glide", speed=0.92, window=1.05, branch_delay=1.12, reveal=0.94),
    "compare_build": ScenePacingProfile("compare_build", speed=0.94, window=1.18, branch_delay=1.00, reveal=0.96),
    "compare_steady": ScenePacingProfile("compare_steady", speed=1.00, window=1.00, branch_delay=1.00, reveal=1.00),
    "compare_surge": ScenePacingProfile("compare_surge", speed=1.18, window=0.72, branch_delay=0.88, reveal=1.16),
    "conclusion_cta": ScenePacingProfile("conclusion_cta", speed=1.14, window=0.90, branch_delay=0.94, reveal=1.18),
    "conclusion_hold": ScenePacingProfile("conclusion_hold", speed=0.92, window=1.08, branch_delay=1.08, reveal=0.92),
    "steady": ScenePacingProfile("steady", speed=1.00, window=1.00, branch_delay=1.00, reveal=1.00),
}


def resolve_scene_pacing_token(role: str, scene_id: str, mood: str | None) -> str:
    normalized_id = scene_id.lower()
    normalized_mood = (mood or "").lower()

    if role == "intro":
        if any(token in normalized_id for token in ("hook", "opening", "intro")):
            return "hook_reveal"
        return "intro_glide" if normalized_mood == "calm" else "intro_setup"

    if role == "main":
        if "setup" in normalized_id:
            return "compare_build"
        if any(token in normalized_id for token in ("climax", "reveal", "peak")):
            return "compare_surge"
        return "compare_steady"

    if role == "conclusion":
        if "cta" in normalized_id or normalized_mood in {"dramatic", "upbeat", "eager"}:
            return "conclusion_cta"
        return "conclusion_hold"

    return "steady"


def get_scene_pacing_profile(token: str | None) -> ScenePacingProfile:
    normalized = (token or "steady").strip().lower() or "steady"
    return SCENE_PACING_REGISTRY.get(normalized, SCENE_PACING_REGISTRY["steady"])

