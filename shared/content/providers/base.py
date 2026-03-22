"""Provider contract for screenplay generation."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

from shared.content.screenplay import Screenplay


@dataclass(frozen=True)
class ProviderDescriptor:
    name: str
    description: str
    supports_remote: bool = False


class ScreenplayProvider(ABC):
    """Abstract screenplay provider."""

    descriptor: ProviderDescriptor

    @abstractmethod
    def generate(
        self,
        *,
        topic: str,
        style: str,
        target_audience: str,
        platform: str | None = None,
        context: dict[str, Any] | None = None,
    ) -> Screenplay:
        raise NotImplementedError

    def revise(
        self,
        *,
        screenplay: Screenplay,
        edit_instruction: str | None = None,
        title: str | None = None,
        logline: str | None = None,
        scene_narration_overrides: dict[str, str] | None = None,
    ) -> Screenplay:
        updated = screenplay.model_copy(deep=True)
        if title:
            updated.title = title
        if logline:
            updated.logline = logline
        if scene_narration_overrides:
            for scene in updated.scenes:
                if scene.id in scene_narration_overrides:
                    scene.narration = scene_narration_overrides[scene.id]
        if edit_instruction:
            updated.metadata["edit_instruction"] = edit_instruction
        return updated

