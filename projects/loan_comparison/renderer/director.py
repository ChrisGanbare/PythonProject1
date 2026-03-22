"""Director: Translates a Screenplay into concrete renderer instructions."""

from __future__ import annotations

from typing import Any, Dict

from shared.content.render_timeline import build_render_timeline
from shared.content.screenplay import Screenplay, Scene, Mood, VisualStyle

from .viz_presets import apply_loan_main_chart_directives

class Director:
    """The creative director logic.
    Decides HOW a scene looks (colors, fonts, easing) based on the screenplay's WHAT and WHY.
    """

    def __init__(self, screenplay: Screenplay):
        self.screenplay = screenplay
        self.renderer_config = {
            "fps": 30,
            "width": 1080,
            "height": 1920,
            "theme": self._resolve_theme(screenplay.visual_style),
            "scenes": []
        }

    def _resolve_theme(self, style: VisualStyle) -> Dict[str, Any]:
        """Maps abstract style to concrete color palette and fonts."""
        # Simple mock mapping. In reality, this would query a theme library.
        if style == VisualStyle.MINIMALIST:
            return {
                "background": "#F5F5F7",
                "primary": "#1D1D1F",
                "secondary": "#86868B",
                "font_title": "Source Han Sans SC",
                "font_body": "Source Han Sans SC",
            }
        elif style == VisualStyle.DATA_DRIVEN:
            return {
                "background": "#0D0D1A",
                "primary": "#4F9EFF",
                "secondary": "#FF7F35",
                "accent": "#FBBF24",
                "font_title": "Microsoft YaHei",
                "font_body": "Microsoft YaHei",
            }
        elif style == VisualStyle.CINEMATIC:  # Dark mode default
             return {
                "background": "#0D0D1A", # Reusing existing dark theme for now
                "primary": "#4F9EFF",
                "secondary": "#FF7F35",
                "accent": "#FBBF24",
                "font_title": "Microsoft YaHei", # Fixed for now as in old code
                "font_body": "Arial"
            }
        # Fallback
        return {
             "background": "#FFFFFF",
             "primary": "#000000"
        }

    @staticmethod
    def _truncate_text(text: str | None, limit: int = 42) -> str:
        value = (text or "").strip()
        if len(value) <= limit:
            return value
        return value[: max(0, limit - 1)].rstrip() + "…"

    @staticmethod
    def _scene_text(scene: Scene | None, fallback: str = "") -> str:
        if scene is None:
            return fallback
        return Director._truncate_text(scene.narration or fallback)

    def direct(self) -> Dict[str, Any]:
        """Process the screenplay and output a render manifest."""
        
        # Global mood adjustments
        base_mood = self.screenplay.mood
        
        for scene in self.screenplay.scenes:
            scene_instruction = self._direct_scene(scene, base_mood)
            self.renderer_config["scenes"].append(scene_instruction)

        return self.renderer_config

    def _direct_scene(self, scene: Scene, base_mood: Mood) -> Dict[str, Any]:
        """Translate a single scene."""
        scene_config = {
            "id": scene.id,
            "duration": scene.duration_est,
            "narration": scene.narration,
            "visuals": [],
            "audio": []
        }

        # Translate mood to animation pacing
        pacing = "normal"
        if scene.mood == Mood.EAGER or scene.mood == Mood.DRAMATIC:
             pacing = "fast" # e.g., shorter transitions
        elif scene.mood == Mood.CALM:
             pacing = "slow"

        scene_config["pacing"] = pacing

        # Process Visuals
        for visual in scene.visuals:
            # Here logic would adapt visual style overrides based on scene mood
            # e.g., if mood is dramatic, make red text pulse faster
            v_spec = visual.model_dump()
            if scene.mood == Mood.DRAMATIC:
                v_spec["style"]["animation_speed"] = 2.0
            
            scene_config["visuals"].append(v_spec)

        return scene_config

    def export_legacy_config(self, total_seconds: int | float | None = None, fps: int | None = None) -> Dict[str, Any]:
        """
        Exports a flat config compatible with the OLD renderer (impl.py).
        This acts as an adapter layer until impl.py is fully rewritten.
        """
        # Extract key colors from determined theme
        theme = self.renderer_config["theme"]
        
        return {
            "theme_colors": {
                "bg_dark": theme.get("background"),
                "primary_blue": theme.get("primary"),
                "secondary_orange": theme.get("secondary")
            },
            # We assume the OLD renderer only supports one main data visualization scene for now context
            # So we pass global style overrides
            "font_config": {
                "title": theme.get("font_title"),
                "body": theme.get("font_body")
            },
            "render_expression": self.export_legacy_render_expression(total_seconds=total_seconds, fps=fps),
        }

    def export_legacy_render_expression(self, total_seconds: int | float | None = None, fps: int | None = None) -> Dict[str, Any]:
        """Map screenplay semantics onto the old renderer's accepted expression keys."""
        scenes = self.screenplay.scenes
        hook_scene = scenes[0] if len(scenes) > 0 else None
        setup_scene = scenes[1] if len(scenes) > 1 else hook_scene
        climax_scene = scenes[2] if len(scenes) > 2 else setup_scene
        conclusion_scene = scenes[-1] if scenes else None

        if self.screenplay.total_duration_est <= 45:
            variant = "short"
        else:
            variant = "standard"

        scene_behavior = {
            "hook_mode": "hero-spotlight" if self.screenplay.mood in {Mood.DRAMATIC, Mood.EAGER} else "context-lead",
            "hook_support_density": "balanced",
            "setup_density": "full-context" if self.screenplay.visual_style == VisualStyle.DATA_DRIVEN else "balanced",
            "comparison_window_months": 60,
            "show_reference_guides": True,
            "conclusion_mode": "cta-spotlight" if conclusion_scene and conclusion_scene.mood in {Mood.DRAMATIC, Mood.UPBEAT} else "summary-band",
            "conclusion_reveal_order": ["headline", "body", "badge", "footer"],
            "conclusion_card_scale": 1.0,
        }

        visual_focus = " / ".join(
            part for part in [
                self._truncate_text(hook_scene.visual_prompt if hook_scene else "", 24),
                self._truncate_text(climax_scene.visual_prompt if climax_scene else "", 24),
            ] if part
        )

        timeline_payload = None
        if total_seconds is not None and fps is not None:
            timeline_payload = build_render_timeline(
                self.screenplay,
                total_secs=total_seconds,
                fps=fps,
            ).model_dump(exclude_none=True)

        expr: Dict[str, Any] = {
            "title_text": self._truncate_text(self.screenplay.title, 36),
            "hook_text": self._scene_text(hook_scene, self.screenplay.logline),
            "summary_text": self._scene_text(setup_scene, self.screenplay.logline),
            "conclusion_title": self._truncate_text(conclusion_scene.id.replace("_", " ").title() if conclusion_scene else "最终建议", 22),
            "conclusion_body": self._scene_text(conclusion_scene, self.screenplay.logline),
            "accent_label": self._scene_text(climax_scene, self.screenplay.logline),
            "variant": variant,
            "scene_behavior": scene_behavior,
            "visual_focus": visual_focus or self._truncate_text(self.screenplay.logline, 28),
            "timeline": timeline_payload,
        }
        return apply_loan_main_chart_directives(self.screenplay, expr)

