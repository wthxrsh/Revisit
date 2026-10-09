from secondbrain.config import Settings
from secondbrain.exceptions import ProviderError
from secondbrain.services.embedding.base import EmbeddingProvider
from secondbrain.services.embedding.hashing import HashingEmbeddingProvider


def build_embedding_provider(settings: Settings) -> EmbeddingProvider:
    provider = settings.embedding_provider

    if provider == "hashing":
        return HashingEmbeddingProvider(dimension=settings.embedding_dim)

    if provider == "fastembed":
        from secondbrain.services.embedding.fastembed_provider import (
            FastEmbedEmbeddingProvider,
        )

        return FastEmbedEmbeddingProvider(model_name=settings.embedding_model)

    if provider == "openai":
        from secondbrain.services.embedding.openai_provider import (
            OpenAIEmbeddingProvider,
        )

        return OpenAIEmbeddingProvider(
            api_key=settings.openai_api_key,
            model=settings.embedding_model,
            dimension=settings.embedding_dim,
            base_url=settings.openai_base_url,
            timeout=settings.provider_timeout_seconds,
        )

    raise ProviderError(f"Unknown embedding provider: {provider}")
