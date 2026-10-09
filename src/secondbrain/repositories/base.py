from abc import ABC, abstractmethod

from secondbrain.models.note import Note


class NoteRepository(ABC):

    @abstractmethod
    def save(self, note: Note, user_id: int) -> Note:
        pass

    @abstractmethod
    def get_by_id(self, note_id: int, user_id: int) -> Note | None:
        pass

    @abstractmethod
    def get_all(
            self,
            user_id: int,
            limit: int = 20,
            offset: int = 0,
            search: str | None = None,
    ) -> list[Note]:
        pass

    @abstractmethod
    def delete(self, note_id: int, user_id: int) -> bool:
        pass

    @abstractmethod
    def update(self, note: Note, user_id: int) -> Note | None:
        pass