from types import SimpleNamespace

import pytest

from secondbrain.exceptions import LLMProviderError, ProviderError
from secondbrain.services.llm.extractive import ExtractiveAnswerProvider
from secondbrain.services.llm.factory import build_llm_provider
from secondbrain.services.llm.openai_provider import OpenAIChatProvider


def _settings(**overrides):
    defaults = {
        "llm_provider": "extractive",
        "llm_model": "llama-3.3-70b-versatile",
        "openai_api_key": "",
        "openai_base_url": "https://api.openai.com/v1",
        "groq_api_key": "",
        "groq_base_url": "https://api.groq.com/openai/v1",
        "provider_timeout_seconds": 30,
    }
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


def test_extractive_provider():
    provider = build_llm_provider(_settings(llm_provider="extractive"))

    assert isinstance(provider, ExtractiveAnswerProvider)


def test_groq_provider_uses_groq_credentials():
    provider = build_llm_provider(
        _settings(llm_provider="groq", groq_api_key="test-key")
    )

    assert isinstance(provider, OpenAIChatProvider)
    assert provider.name == "groq:llama-3.3-70b-versatile"
    assert "api.groq.com" in str(provider._client.base_url)


def test_groq_requires_api_key():
    with pytest.raises(LLMProviderError):
        build_llm_provider(_settings(llm_provider="groq", groq_api_key=""))


def test_unknown_provider_raises():
    with pytest.raises(ProviderError):
        build_llm_provider(_settings(llm_provider="does-not-exist"))
