import logging

from secondbrain.clock import utc_now
from secondbrain.exceptions import (
    ConflictError,
    DocumentNotFoundError,
    EmptyDocumentError,
    ProcessingError,
    ProviderError,
    StorageError,
)
from secondbrain.models.chunk import Chunk
from secondbrain.models.document import Document, DocumentStatus
from secondbrain.repositories.chunk_repository import ChunkRepository
from secondbrain.repositories.document_repository import DocumentRepository
from secondbrain.services.embedding.base import EmbeddingProvider
from secondbrain.services.processing.chunker import TextChunker
from secondbrain.services.processing.pdf_extractor import PdfTextExtractor
from secondbrain.storage.file_storage import LocalFileStorage

logger = logging.getLogger(__name__)

UNEXPECTED_ERROR_MESSAGE = "Unexpected error while processing the document"


class DocumentProcessingService:

    def __init__(
        self,
        document_repository: DocumentRepository,
        chunk_repository: ChunkRepository,
        storage: LocalFileStorage,
        extractor: PdfTextExtractor,
        chunker: TextChunker,
        embedding_provider: EmbeddingProvider,
    ):
        self.document_repository = document_repository
        self.chunk_repository = chunk_repository
        self.storage = storage
        self.extractor = extractor
        self.chunker = chunker
        self.embedding_provider = embedding_provider

    def process(self, document_id: int, user_id: int) -> Document:
        document = self.document_repository.get_by_id(document_id, user_id)

        if document is None:
            raise DocumentNotFoundError(
                f"Document with id {document_id} not found"
            )

        if not self.document_repository.try_mark_processing(document_id, user_id):
            raise ConflictError(
                "This document is already being processed"
            )

        logger.info("Processing document id=%s user_id=%s", document_id, user_id)

        try:
            self._run(document, user_id)
        except (ProcessingError, ProviderError) as error:
            self._fail(document, str(error))
        except Exception:
            logger.exception(
                "Unexpected processing failure for document id=%s", document_id
            )
            self._fail(document, UNEXPECTED_ERROR_MESSAGE)

        refreshed = self.document_repository.get_by_id(document_id, user_id)
        return refreshed if refreshed else document

    def _run(self, document: Document, user_id: int) -> None:
        path = self.storage.path_for(document.storage_key)

        if not path.exists():
            raise StorageError("The stored file is missing")

        pages = self.extractor.extract(path)
        text_chunks = self.chunker.chunk_pages(pages)

        if not text_chunks:
            raise EmptyDocumentError("No content could be indexed")

        embeddings = self.embedding_provider.embed_documents(
            [chunk.text for chunk in text_chunks]
        )

        if len(embeddings) != len(text_chunks):
            raise ProviderError("Embedding count did not match chunk count")

        domain_chunks = [
            Chunk(
                chunk_index=text_chunk.index,
                content=text_chunk.text,
                page_number=text_chunk.page_number,
                page_end=text_chunk.page_end,
                document_id=document.id,
                user_id=user_id,
                embedding=embedding,
            )
            for text_chunk, embedding in zip(text_chunks, embeddings)
        ]

        count = self.chunk_repository.replace_for_document(
            document.id, user_id, domain_chunks
        )

        self._complete(document, page_count=len(pages))
        logger.info(
            "Indexed document id=%s into %s chunks", document.id, count
        )

    def _complete(self, document: Document, page_count: int) -> None:
        document.status = DocumentStatus.COMPLETED
        document.error_message = None
        document.page_count = page_count
        document.processed_at = utc_now()
        document.updated_at = utc_now()
        self.document_repository.update(document)

    def _fail(self, document: Document, message: str) -> None:
        document.status = DocumentStatus.FAILED
        document.error_message = message[:1000]
        document.updated_at = utc_now()
        self.document_repository.update(document)
        logger.warning(
            "Document id=%s failed processing: %s", document.id, message
        )
