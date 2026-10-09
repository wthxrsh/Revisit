import hashlib
import math
import re

from secondbrain.services.embedding.base import EmbeddingProvider

_TOKEN = re.compile(r"[a-z0-9]+")


class HashingEmbeddingProvider(EmbeddingProvider):
    """Deterministic lexical feature-hashing embedding.

    Not a neural semantic model. It is used as the default offline provider so the
    application and its tests run without network access or large downloads. Use the
    ``fastembed`` provider for true semantic embeddings.
    """

    def __init__(self, dimension: int = 384):
        self.dimension = dimension

    @property
    def name(self) -> str:
        return f"hashing-{self.dimension}"

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [self._embed(text) for text in texts]

    def embed_query(self, text: str) -> list[float]:
        return self._embed(text)

    def _embed(self, text: str) -> list[float]:
        vector = [0.0] * self.dimension

        for token in _TOKEN.findall(text.lower()):
            digest = hashlib.blake2b(
                token.encode("utf-8"), digest_size=8
            ).digest()
            index = int.from_bytes(digest[:4], "big") % self.dimension
            sign = 1.0 if digest[4] & 1 else -1.0
            vector[index] += sign

        norm = math.sqrt(sum(value * value for value in vector))
        if norm == 0.0:
            return vector

        return [value / norm for value in vector]
