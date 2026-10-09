from abc import ABC, abstractmethod


class EmbeddingProvider(ABC):

    dimension: int

    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @abstractmethod
    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        pass

    @abstractmethod
    def embed_query(self, text: str) -> list[float]:
        pass
