import logging

from secondbrain.exceptions import EmbeddingProviderError
from secondbrain.services.embedding.base import EmbeddingProvider

logger = logging.getLogger(__name__)


class FastEmbedEmbeddingProvider(EmbeddingProvider):

    def __init__(self, model_name: str):
        try:
            from fastembed import TextEmbedding
        except ImportError as error:
            raise EmbeddingProviderError(
                "The 'fastembed' package is not installed. Install it with "
                "'pip install -e .[embeddings]' or set EMBEDDING_PROVIDER=hashing."
            ) from error

        try:
            self._model = TextEmbedding(model_name=model_name)
        except Exception as error:
            raise EmbeddingProviderError(
                f"Could not load the fastembed model '{model_name}'"
            ) from error

        self._model_name = model_name
        self.dimension = self._detect_dimension()

    @property
    def name(self) -> str:
        return f"fastembed:{self._model_name}"

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []

        try:
            return [list(vector) for vector in self._model.embed(texts)]
        except Exception as error:
            logger.warning("fastembed document embedding failed")
            raise EmbeddingProviderError(
                "Embedding generation failed"
            ) from error

    def embed_query(self, text: str) -> list[float]:
        return self.embed_documents([text])[0]

    def _detect_dimension(self) -> int:
        try:
            probe = next(iter(self._model.embed(["dimension probe"])))
        except Exception as error:
            raise EmbeddingProviderError(
                "Could not determine embedding dimension"
            ) from error

        return len(list(probe))
