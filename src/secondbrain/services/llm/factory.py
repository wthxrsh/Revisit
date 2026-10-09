from secondbrain.config import Settings
from secondbrain.exceptions import ProviderError
from secondbrain.services.llm.base import LLMProvider
from secondbrain.services.llm.extractive import ExtractiveAnswerProvider


def build_llm_provider(settings: Settings) -> LLMProvider:
    provider = settings.llm_provider

    if provider == "extractive":
        return ExtractiveAnswerProvider()

    if provider == "openai":
        from secondbrain.services.llm.openai_provider import OpenAIChatProvider

        return OpenAIChatProvider(
            api_key=settings.openai_api_key,
            model=settings.llm_model,
            base_url=settings.openai_base_url,
            timeout=settings.provider_timeout_seconds,
        )

    if provider == "groq":
        from secondbrain.services.llm.openai_provider import OpenAIChatProvider

        return OpenAIChatProvider(
            api_key=settings.groq_api_key,
            model=settings.llm_model,
            base_url=settings.groq_base_url,
            timeout=settings.provider_timeout_seconds,
            provider_label="groq",
        )

    raise ProviderError(f"Unknown LLM provider: {provider}")
