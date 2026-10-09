from abc import ABC, abstractmethod

from secondbrain.models.document import Document


class DocumentRepository(ABC):

    @abstractmethod
    def save(self, document: Document) -> Document:
        pass

    @abstractmethod
    def get_by_id(self, document_id: int, user_id: int) -> Document | None:
        pass

    @abstractmethod
    def get_for_update(
        self, document_id: int, user_id: int
    ) -> Document | None:
        pass

    @abstractmethod
    def get_all(
        self,
        user_id: int,
        limit: int = 20,
        offset: int = 0,
    ) -> list[Document]:
        pass

    @abstractmethod
    def try_mark_processing(self, document_id: int, user_id: int) -> bool:
        pass

    @abstractmethod
    def update(self, document: Document) -> Document:
        pass

    @abstractmethod
    def delete(self, document_id: int, user_id: int) -> bool:
        pass

    @abstractmethod
    def count(self, user_id: int) -> int:
        pass
