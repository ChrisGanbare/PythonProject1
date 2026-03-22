"""Registry for screenplay providers."""

from __future__ import annotations

from typing import Iterable

from shared.content.providers.base import ProviderDescriptor, ScreenplayProvider


class ProviderRegistry:
    def __init__(self) -> None:
        self._providers: dict[str, ScreenplayProvider] = {}

    def register(self, provider: ScreenplayProvider) -> None:
        self._providers[provider.descriptor.name] = provider

    def get(self, name: str) -> ScreenplayProvider | None:
        return self._providers.get(name)

    def require(self, name: str) -> ScreenplayProvider:
        provider = self.get(name)
        if provider is None:
            supported = ", ".join(sorted(self._providers))
            raise ValueError(f"unsupported screenplay provider '{name}'. Supported: {supported}")
        return provider

    def list_descriptors(self) -> list[ProviderDescriptor]:
        return [provider.descriptor for provider in self._providers.values()]

    def names(self) -> list[str]:
        return sorted(self._providers)

    def enabled(self, names: Iterable[str]) -> list[ProviderDescriptor]:
        allow = set(names)
        return [descriptor for descriptor in self.list_descriptors() if descriptor.name in allow]


provider_registry = ProviderRegistry()

