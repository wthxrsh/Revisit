from sqlalchemy import func, select, update
from sqlalchemy.orm import Session

from secondbrain.clock import utc_now
from secondbrain.database.document_models import DocumentModel
from secondbrain.models.document import Document, DocumentStatus
from secondbrain.repositories.document_repository import DocumentRepository


class PostgresDocumentRepository(DocumentRepository):

    def __init__(self, session: Session):
        self.session = session

    def save(self, document: Document) -> Document:
        model = DocumentModel(
            user_id=document.user_id,
            original_filename=document.original_filename,
            storage_key=document.storage_key,
            file_size=document.file_size,
            mime_type=document.mime_type,
            status=document.status,
            error_message=document.error_message,
            page_count=document.page_count,
            created_at=document.created_at,
            updated_at=document.updated_at,
            processed_at=document.processed_at,
        )

        self.session.add(model)
        self.session.commit()
        self.session.refresh(model)

        return self._to_domain(model)

    def get_by_id(self, document_id: int, user_id: int) -> Document | None:
        statement = select(DocumentModel).where(
            DocumentModel.id == document_id,
            DocumentModel.user_id == user_id,
        )

        model = self.session.scalar(statement)

        return self._to_domain(model) if model else None

    def get_for_update(
        self, document_id: int, user_id: int
    ) -> Document | None:
        statement = (
            select(DocumentModel)
            .where(
                DocumentModel.id == document_id,
                DocumentModel.user_id == user_id,
            )
            .with_for_update()
        )

        model = self.session.scalar(statement)

        return self._to_domain(model) if model else None

    def get_all(
        self,
        user_id: int,
        limit: int = 20,
        offset: int = 0,
    ) -> list[Document]:
        statement = (
            select(DocumentModel)
            .where(DocumentModel.user_id == user_id)
            .order_by(DocumentModel.created_at.desc(), DocumentModel.id.desc())
            .limit(limit)
            .offset(offset)
        )

        models = self.session.scalars(statement).all()

        return [self._to_domain(model) for model in models]

    def try_mark_processing(self, document_id: int, user_id: int) -> bool:
        statement = (
            update(DocumentModel)
            .where(
                DocumentModel.id == document_id,
                DocumentModel.user_id == user_id,
                DocumentModel.status != DocumentStatus.PROCESSING,
            )
            .values(
                status=DocumentStatus.PROCESSING,
                error_message=None,
                updated_at=utc_now(),
            )
        )

        result = self.session.execute(statement)
        self.session.commit()

        return (result.rowcount or 0) == 1

    def update(self, document: Document) -> Document:
        model = self.session.get(DocumentModel, document.id)

        if model is None:
            raise ValueError(f"Document {document.id} no longer exists")

        model.status = document.status
        model.error_message = document.error_message
        model.page_count = document.page_count
        model.processed_at = document.processed_at
        model.updated_at = document.updated_at

        self.session.commit()
        self.session.refresh(model)

        return self._to_domain(model)

    def delete(self, document_id: int, user_id: int) -> bool:
        statement = select(DocumentModel).where(
            DocumentModel.id == document_id,
            DocumentModel.user_id == user_id,
        )

        model = self.session.scalar(statement)

        if model is None:
            return False

        self.session.delete(model)
        self.session.commit()

        return True

    def count(self, user_id: int) -> int:
        statement = select(func.count(DocumentModel.id)).where(
            DocumentModel.user_id == user_id,
        )

        return self.session.scalar(statement) or 0

    @staticmethod
    def _to_domain(model: DocumentModel) -> Document:
        return Document(
            id=model.id,
            user_id=model.user_id,
            original_filename=model.original_filename,
            storage_key=model.storage_key,
            file_size=model.file_size,
            mime_type=model.mime_type,
            status=model.status,
            error_message=model.error_message,
            page_count=model.page_count,
            created_at=model.created_at,
            updated_at=model.updated_at,
            processed_at=model.processed_at,
        )
