"""AI screenplay planner orchestrator."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from shared.ops.config.settings import settings
from shared.ai.content.providers import provider_registry
from shared.ai.content.providers.openai_compatible import OpenAICompatibleScreenplayProvider
from shared.ai.content.screenplay import Screenplay


@dataclass(frozen=True)
class ScreenplayGenerationResult:
    screenplay: Screenplay
    provider_used: str
    requested_provider: str | None
    fallback_used: bool = False


class AIPlanner:
    """Provider-agnostic screenplay planner."""

    def __init__(self) -> None:
        self._ensure_builtin_providers()

    def _ensure_builtin_providers(self) -> None:
        if settings.api.openai_compatible_base_url and settings.api.openai_compatible_api_key:
            provider_registry.register(
                OpenAICompatibleScreenplayProvider(
                    base_url=settings.api.openai_compatible_base_url,
                    api_key=settings.api.openai_compatible_api_key,
                    model=settings.api.openai_compatible_model,
                )
            )

    def list_available_providers(self) -> list[dict[str, object]]:
        enabled = set(settings.api.screenplay_enabled_providers)
        default_name = settings.api.screenplay_provider_default
        fallback_name = settings.api.screenplay_provider_fallback
        return [
            {
                "name": descriptor.name,
                "description": descriptor.description,
                "supports_remote": descriptor.supports_remote,
                "enabled": descriptor.name in enabled,
                "is_default": descriptor.name == default_name,
                "is_fallback": descriptor.name == fallback_name,
            }
            for descriptor in provider_registry.list_descriptors()
        ]

    def _resolve_provider_name(self, requested_provider: str | None = None) -> str:
        enabled = set(settings.api.screenplay_enabled_providers)
        if requested_provider and settings.api.screenplay_allow_provider_override and requested_provider in enabled:
            return requested_provider
        default_name = settings.api.screenplay_provider_default
        if default_name not in enabled:
            raise ValueError(f"default screenplay provider '{default_name}' is not enabled")
        return default_name

    def preview_screenplay(
        self,
        *,
        topic: str,
        style: str = "cinematic",
        target_audience: str = "中文自媒体观众",
        platform: str | None = None,
        provider_name: str | None = None,
        context: dict[str, Any] | None = None,
    ) -> ScreenplayGenerationResult:
        requested_name = provider_name
        chosen_name = self._resolve_provider_name(provider_name)
        chosen_provider = provider_registry.require(chosen_name)

        try:
            screenplay = chosen_provider.generate(
                topic=topic,
                style=style,
                target_audience=target_audience,
                platform=platform,
                context=context,
            )
            return ScreenplayGenerationResult(
                screenplay=screenplay,
                provider_used=chosen_name,
                requested_provider=requested_name,
                fallback_used=False,
            )
        except Exception:
            fallback_name = settings.api.screenplay_provider_fallback
            if fallback_name == chosen_name:
                raise
            fallback_provider = provider_registry.require(fallback_name)
            screenplay = fallback_provider.generate(
                topic=topic,
                style=style,
                target_audience=target_audience,
                platform=platform,
                context=context,
            )
            screenplay.metadata["fallback_reason"] = f"provider '{chosen_name}' failed"
            return ScreenplayGenerationResult(
                screenplay=screenplay,
                provider_used=fallback_name,
                requested_provider=requested_name,
                fallback_used=True,
            )

    def generate_screenplay(
        self,
        topic: str,
        style: str = "cinematic",
        provider_name: str | None = None,
        target_audience: str = "中文自媒体观众",
        platform: str | None = None,
        context: dict[str, Any] | None = None,
    ) -> Screenplay:
        return self.preview_screenplay(
            topic=topic,
            style=style,
            provider_name=provider_name,
            target_audience=target_audience,
            platform=platform,
            context=context,
        ).screenplay

    def revise_screenplay(
        self,
        *,
        screenplay: Screenplay,
        provider_name: str | None = None,
        edit_instruction: str | None = None,
        title: str | None = None,
        logline: str | None = None,
        scene_narration_overrides: dict[str, str] | None = None,
    ) -> ScreenplayGenerationResult:
        requested_name = provider_name
        chosen_name = self._resolve_provider_name(provider_name)
        chosen_provider = provider_registry.require(chosen_name)

        try:
            updated = chosen_provider.revise(
                screenplay=screenplay,
                edit_instruction=edit_instruction,
                title=title,
                logline=logline,
                scene_narration_overrides=scene_narration_overrides,
            )
            return ScreenplayGenerationResult(
                screenplay=updated,
                provider_used=chosen_name,
                requested_provider=requested_name,
                fallback_used=False,
            )
        except Exception:
            fallback_name = settings.api.screenplay_provider_fallback
            if fallback_name == chosen_name:
                raise
            fallback_provider = provider_registry.require(fallback_name)
            updated = fallback_provider.revise(
                screenplay=screenplay,
                edit_instruction=edit_instruction,
                title=title,
                logline=logline,
                scene_narration_overrides=scene_narration_overrides,
            )
            updated.metadata["fallback_reason"] = f"provider '{chosen_name}' revise failed"
            return ScreenplayGenerationResult(
                screenplay=updated,
                provider_used=fallback_name,
                requested_provider=requested_name,
                fallback_used=True,
            )


ai_planner = AIPlanner()
