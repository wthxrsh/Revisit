import logging

import httpx

from secondbrain.exceptions import EmbeddingProviderError
from secondbrain.services.embedding.base import EmbeddingProvider

logger = logging.getLogger(__name__)


class OpenAIEmbeddingProvider(EmbeddingProvider):

    def __init__(
        self,
        api_key: str,
        model: str,
        dimension: int,
        base_url: str = "https://api.openai.com/v1",
        timeout: float = 30.0,
    ):
        if not api_key:
            raise EmbeddingProviderError("OPENAI_API_KEY is not configured")

        self.dimension = dimension
        self._model = model
        self._base_url = base_url.rstrip("/")
        self._client = httpx.Client(
            base_url=self._base_url,
            timeout=timeout,
            headers={"Authorization": f"Bearer {api_key}"},
        )

    @property
    def name(self) -> str:
        return f"openai:{self._model}"

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []

        try:
            response = self._client.post(
                "/embeddings",
                json={"model": self._model, "input": texts},
            )
            response.raise_for_status()
            payload = response.json()
        except httpx.HTTPError as error:
            logger.warning("OpenAI embedding request failed")
            raise EmbeddingProviderError(
                "Embedding provider request failed"
            ) from error

        data = sorted(payload["data"], key=lambda item: item["index"])
        return [item["embedding"] for item in data]

    def embed_query(self, text: str) -> list[float]:
        return self.embed_documents([text])[0]
