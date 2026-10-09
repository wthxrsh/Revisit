from abc import ABC, abstractmethod

from secondbrain.models.chunk import Chunk, ScoredChunk


class ChunkRepository(ABC):

    @abstractmethod
    def replace_for_document(
        self,
        document_id: int,
        user_id: int,
        chunks: list[Chunk],
    ) -> int:
        pass

    @abstractmethod
    def get_by_document(
        self,
        document_id: int,
        user_id: int,
    ) -> list[Chunk]:
        pass

    @abstractmethod
    def search(
        self,
        user_id: int,
        query_embedding: list[float],
        top_k: int = 5,
        min_similarity: float = 0.0,
        document_ids: list[int] | None = None,
    ) -> list[ScoredChunk]:
        pass

    @abstractmethod
    def delete_for_document(self, document_id: int) -> int:
        pass

    @abstractmethod
    def count_for_user(self, user_id: int) -> int:
        pass
