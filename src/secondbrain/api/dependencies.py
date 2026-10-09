from functools import lru_cache

from fastapi import Depends
from sqlalchemy.orm import Session

from secondbrain.config import settings
from secondbrain.database.dependencies import get_db
from secondbrain.repositories.postgres_chunk_repository import (
    PostgresChunkRepository,
)
from secondbrain.repositories.postgres_conversation_repository import (
    PostgresConversationRepository,
)
from secondbrain.repositories.postgres_document_repository import (
    PostgresDocumentRepository,
)
from secondbrain.repositories.postgres_note_repository import (
    PostgresNoteRepository,
)
from secondbrain.repositories.postgres_user_repository import (
    PostgresUserRepository,
)
from secondbrain.services.auth_service import AuthService
from secondbrain.services.conversation_service import ConversationService
from secondbrain.services.document_service import DocumentService
from secondbrain.services.embedding.base import EmbeddingProvider
from secondbrain.services.embedding.factory import build_embedding_provider
from secondbrain.services.llm.base import LLMProvider
from secondbrain.services.llm.factory import build_llm_provider
from secondbrain.services.note_service import NoteService
from secondbrain.services.processing.chunker import TextChunker
from secondbrain.services.processing.pdf_extractor import PdfTextExtractor
from secondbrain.services.processing_service import DocumentProcessingService
from secondbrain.services.rag_service import RagService
from secondbrain.storage.file_storage import LocalFileStorage


@lru_cache
def get_embedding_provider() -> EmbeddingProvider:
    return build_embedding_provider(settings)


@lru_cache
def get_llm_provider() -> LLMProvider:
    return build_llm_provider(settings)


@lru_cache
def get_file_storage() -> LocalFileStorage:
    return LocalFileStorage(
        base_path=settings.document_storage_path,
        max_size_bytes=settings.max_upload_size_bytes,
    )


@lru_cache
def get_pdf_extractor() -> PdfTextExtractor:
    return PdfTextExtractor()


@lru_cache
def get_text_chunker() -> TextChunker:
    return TextChunker(
        chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap,
    )


def get_note_service(db: Session = Depends(get_db)) -> NoteService:
    return NoteService(PostgresNoteRepository(db))


def get_auth_service(db: Session = Depends(get_db)) -> AuthService:
    return AuthService(PostgresUserRepository(db))


def get_document_processing_service(
    db: Session = Depends(get_db),
) -> DocumentProcessingService:
    return DocumentProcessingService(
        document_repository=PostgresDocumentRepository(db),
        chunk_repository=PostgresChunkRepository(db),
        storage=get_file_storage(),
        extractor=get_pdf_extractor(),
        chunker=get_text_chunker(),
        embedding_provider=get_embedding_provider(),
    )


def get_document_service(
    db: Session = Depends(get_db),
) -> DocumentService:
    return DocumentService(
        document_repository=PostgresDocumentRepository(db),
        storage=get_file_storage(),
        processing_service=get_document_processing_service(db),
        process_on_upload=settings.process_on_upload,
    )


def get_conversation_service(
    db: Session = Depends(get_db),
) -> ConversationService:
    return ConversationService(PostgresConversationRepository(db))


def get_rag_service(db: Session = Depends(get_db)) -> RagService:
    return RagService(
        chunk_repository=PostgresChunkRepository(db),
        conversation_repository=PostgresConversationRepository(db),
        embedding_provider=get_embedding_provider(),
        llm_provider=get_llm_provider(),
        top_k=settings.retrieval_top_k,
        min_similarity=settings.retrieval_min_similarity,
        max_context_chars=settings.rag_max_context_chars,
    )
