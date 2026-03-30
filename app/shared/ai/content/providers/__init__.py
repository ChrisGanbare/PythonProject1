"""Built-in screenplay providers."""

from shared.ai.content.providers.mock import mock_provider
from shared.ai.content.providers.registry import provider_registry

provider_registry.register(mock_provider)

__all__ = ["provider_registry", "mock_provider"]

