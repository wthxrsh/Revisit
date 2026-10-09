from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from secondbrain.database.chunk_models import ChunkModel
from secondbrain.database.document_models import DocumentModel
from secondbrain.models.chunk import Chunk, ScoredChunk
from secondbrain.repositories.chunk_repository import ChunkRepository


class PostgresChunkRepository(ChunkRepository):

    def __init__(self, session: Session):
        self.session = session

    def replace_for_document(
        self,
        document_id: int,
        user_id: int,
        chunks: list[Chunk],
    ) -> int:
        self.session.execute(
            delete(ChunkModel).where(
                ChunkModel.document_id == document_id,
                ChunkModel.user_id == user_id,
            )
        )

        models = [
            ChunkModel(
                document_id=document_id,
                user_id=user_id,
                chunk_index=chunk.chunk_index,
                page_number=chunk.page_number,
                page_end=chunk.page_end,
                content=chunk.content,
                embedding=chunk.embedding,
                created_at=chunk.created_at,
            )
            for chunk in chunks
        ]

        self.session.add_all(models)
        self.session.commit()

        return len(models)

    def get_by_document(
        self,
        document_id: int,
        user_id: int,
    ) -> list[Chunk]:
        statement = (
            select(ChunkModel)
            .where(
                ChunkModel.document_id == document_id,
                ChunkModel.user_id == user_id,
            )
            .order_by(ChunkModel.chunk_index)
        )

        models = self.session.scalars(statement).all()

        return [self._to_domain(model) for model in models]

    def search(
        self,
        user_id: int,
        query_embedding: list[float],
        top_k: int = 5,
        min_similarity: float = 0.0,
        document_ids: list[int] | None = None,
    ) -> list[ScoredChunk]:
        distance = ChunkModel.embedding.cosine_distance(query_embedding)
        similarity = (1 - distance).label("score")

        statement = (
            select(ChunkModel, DocumentModel.original_filename, similarity)
            .join(
                DocumentModel,
                ChunkModel.document_id == DocumentModel.id,
            )
            .where(
                ChunkModel.user_id == user_id,
                ChunkModel.embedding.is_not(None),
            )
        )

        if document_ids:
            statement = statement.where(
                ChunkModel.document_id.in_(document_ids)
            )

        if min_similarity > 0.0:
            statement = statement.where(similarity >= min_similarity)

        statement = statement.order_by(distance).limit(top_k)

        rows = self.session.execute(statement).all()

        results: list[ScoredChunk] = []
        for model, filename, score in rows:
            results.append(
                ScoredChunk(
                    chunk=self._to_domain(model),
                    score=float(score),
                    document_id=model.document_id,
                    filename=filename,
                )
            )

        return results

    def delete_for_document(self, document_id: int) -> int:
        result = self.session.execute(
            delete(ChunkModel).where(ChunkModel.document_id == document_id)
        )
        self.session.commit()
        return result.rowcount or 0

    def count_for_user(self, user_id: int) -> int:
        statement = select(func.count(ChunkModel.id)).where(
            ChunkModel.user_id == user_id,
        )

        return self.session.scalar(statement) or 0

    @staticmethod
    def _to_domain(model: ChunkModel) -> Chunk:
        return Chunk(
            id=model.id,
            document_id=model.document_id,
            user_id=model.user_id,
            chunk_index=model.chunk_index,
            page_number=model.page_number,
            page_end=model.page_end,
            content=model.content,
            embedding=list(model.embedding) if model.embedding is not None else None,
            created_at=model.created_at,
        )
