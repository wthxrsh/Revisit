import logging
import re
from pathlib import Path
from typing import BinaryIO

from secondbrain.exceptions import DocumentNotFoundError
from secondbrain.models.document import Document, DocumentStatus
from secondbrain.repositories.document_repository import DocumentRepository
from secondbrain.services.processing_service import DocumentProcessingService
from secondbrain.storage.file_storage import LocalFileStorage

logger = logging.getLogger(__name__)

_SAFE_NAME = re.compile(r"[^\w.\- ]+")
_DEFAULT_FILENAME = "document.pdf"
_MAX_FILENAME_LENGTH = 255


class DocumentService:

    def __init__(
        self,
        document_repository: DocumentRepository,
        storage: LocalFileStorage,
        processing_service: DocumentProcessingService,
        process_on_upload: bool = True,
    ):
        self.document_repository = document_repository
        self.storage = storage
        self.processing_service = processing_service
        self.process_on_upload = process_on_upload

    def upload(
        self,
        user_id: int,
        filename: str | None,
        fileobj: BinaryIO,
    ) -> Document:
        safe_filename = self._safe_filename(filename)
        stored = self.storage.save_stream(fileobj)

        document = Document(
            user_id=user_id,
            original_filename=safe_filename,
            storage_key=stored.storage_key,
            file_size=stored.size,
            mime_type=stored.content_type,
            status=DocumentStatus.PENDING,
        )

        try:
            saved = self.document_repository.save(document)
        except Exception:
            self.storage.delete(stored.storage_key)
            logger.exception("Rolling back upload after database failure")
            raise

        if self.process_on_upload and saved.id is not None:
            saved = self.processing_service.process(saved.id, user_id)

        return saved

    def get(self, document_id: int, user_id: int) -> Document:
        document = self.document_repository.get_by_id(document_id, user_id)

        if document is None:
            raise DocumentNotFoundError(
                f"Document with id {document_id} not found"
            )

        return document

    def list_documents(
        self, user_id: int, limit: int = 20, offset: int = 0
    ) -> list[Document]:
        return self.document_repository.get_all(
            user_id=user_id, limit=limit, offset=offset
        )

    def count(self, user_id: int) -> int:
        return self.document_repository.count(user_id)

    def delete(self, document_id: int, user_id: int) -> None:
        document = self.get(document_id, user_id)

        self.storage.delete(document.storage_key)
        self.document_repository.delete(document_id, user_id)

        logger.info("Deleted document id=%s user_id=%s", document_id, user_id)

    def reprocess(self, document_id: int, user_id: int) -> Document:
        self.get(document_id, user_id)
        return self.processing_service.process(document_id, user_id)

    @staticmethod
    def _safe_filename(filename: str | None) -> str:
        if not filename:
            return _DEFAULT_FILENAME

        name = Path(filename).name
        name = _SAFE_NAME.sub("_", name).strip().strip(".")
        name = name[:_MAX_FILENAME_LENGTH]

        return name or _DEFAULT_FILENAME
