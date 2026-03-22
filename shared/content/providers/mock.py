"""Built-in mock screenplay provider."""

from __future__ import annotations

from shared.content.providers.base import ProviderDescriptor, ScreenplayProvider
from shared.content.screenplay import AudioCue, Mood, Scene, Screenplay, VisualElement, VisualStyle


class MockScreenplayProvider(ScreenplayProvider):
    descriptor = ProviderDescriptor(
        name="mock",
        description="Built-in deterministic screenplay provider for local preview and fallback.",
        supports_remote=False,
    )

    def generate(
        self,
        *,
        topic: str,
        style: str,
        target_audience: str,
        platform: str | None = None,
        context: dict | None = None,
    ) -> Screenplay:
        context = context or {}
        lower_style = style.lower()
        mood = Mood.NEUTRAL
        if "dramatic" in lower_style:
            mood = Mood.DRAMATIC
        elif "upbeat" in lower_style:
            mood = Mood.UPBEAT
        elif "calm" in lower_style:
            mood = Mood.CALM

        visual_style = VisualStyle.CINEMATIC
        if "minimal" in lower_style:
            visual_style = VisualStyle.MINIMALIST
        elif "data" in lower_style or "tech" in lower_style:
            visual_style = VisualStyle.DATA_DRIVEN

        interest_diff = context.get("interest_difference_text", "差额很大")
        cheaper = context.get("which_is_cheaper", "等额本金")
        loan_text = context.get("loan_amount_text", "100万")
        years_text = context.get("loan_years_text", "30年")

        scenes = [
            Scene(
                id="scene_01_hook",
                duration_est=5.0,
                narration=f"{loan_text}贷款，{years_text}下来，利息差距可能远超你的预期。",
                visual_prompt="贷款合同、房屋剪影与高压数字构成的开场冲击画面。",
                mood=Mood.SERIOUS,
                visuals=[
                    VisualElement(
                        type="text",
                        content="别只盯月供",
                        style={"color": "#FF4D4F", "font_size": 120, "position": "center"},
                    ),
                    VisualElement(
                        type="text",
                        content=topic,
                        style={"font_size": 58, "position": "lower_center"},
                    ),
                ],
                audio_cues=[AudioCue(asset_id="music_upbeat_01", volume=0.35)],
            ),
            Scene(
                id="scene_02_setup",
                duration_est=8.0,
                narration="我们把等额本息和等额本金放在同一条时间轴上，直接看累计利息变化。",
                visual_prompt="双线累计利息走势、同画布对比。",
                mood=Mood.NEUTRAL,
                action_directives={
                    "viz_scene_id": "loan_compare_main",
                    "chart_type": "dual_cumulative",
                },
                visuals=[
                    VisualElement(
                        type="chart",
                        content="loan_comparison_data",
                        style={"type": "line_compare", "focus": "interest_gap"},
                    ),
                ],
            ),
            Scene(
                id="scene_03_climax",
                duration_est=8.0,
                narration=f"到贷款后期，这笔差额会被放大到 {interest_diff}，真正更省的是 {cheaper}。",
                visual_prompt="高亮差额数字、线图分叉加速拉大。",
                mood=Mood.DRAMATIC if mood == Mood.NEUTRAL else mood,
                visuals=[
                    VisualElement(
                        type="text",
                        content=interest_diff,
                        style={"color": "#F43F5E", "font_size": 150, "animation": "pulse"},
                    ),
                ],
            ),
            Scene(
                id="scene_04_conclusion",
                duration_est=5.0,
                narration=f"如果现金流允许，优先考虑 {cheaper}。先看现金流，再看总利息。",
                visual_prompt="结论卡片、行动建议、品牌收尾。",
                mood=Mood.CALM,
                visuals=[
                    VisualElement(
                        type="text",
                        content=f"更省利息：{cheaper}",
                        style={"color": "#22D47E", "font_size": 80},
                    ),
                ],
            ),
        ]

        return Screenplay(
            title=f"{topic} | 数据可视化脚本",
            logline=f"面向{target_audience}的 {topic} 数据叙事短视频脚本。",
            topic=topic,
            target_audience=target_audience,
            mood=mood,
            visual_style=visual_style,
            scenes=scenes,
            total_duration_est=sum(scene.duration_est for scene in scenes),
            metadata={"provider": "mock", "platform": platform or "unknown", **context},
        )


mock_provider = MockScreenplayProvider()

