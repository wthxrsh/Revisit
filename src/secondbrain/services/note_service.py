import logging

from secondbrain.clock import utc_now
from secondbrain.exceptions import InvalidNoteError, NoteNotFoundError
from secondbrain.models.note import Note
from secondbrain.repositories.base import NoteRepository

logger = logging.getLogger(__name__)

MAX_TITLE_LENGTH = 255


class NoteService:

    def __init__(self, repository: NoteRepository):
        self.repository = repository

    def create_note(
        self,
        title: str,
        content: str,
        user_id: int,
    ) -> Note:
        self._validate(title, content)

        note = Note(
            id=None,
            title=title,
            content=content,
        )

        saved_note = self.repository.save(note, user_id)
        logger.info("Note created: id=%s user_id=%s", saved_note.id, user_id)

        return saved_note

    def get_note(self, note_id: int, user_id: int) -> Note:
        note = self.repository.get_by_id(note_id, user_id)

        if note is None:
            raise NoteNotFoundError(f"Note with id {note_id} not found")

        return note

    def get_all_notes(
        self,
        user_id: int,
        limit: int = 20,
        offset: int = 0,
        search: str | None = None,
    ) -> list[Note]:
        return self.repository.get_all(
            user_id=user_id,
            limit=limit,
            offset=offset,
            search=search,
        )

    def delete_note(self, note_id: int, user_id: int) -> None:
        deleted = self.repository.delete(note_id, user_id)

        if not deleted:
            raise NoteNotFoundError(f"Note with id {note_id} not found")

        logger.info("Note deleted: id=%s user_id=%s", note_id, user_id)

    def update_note(
        self,
        note_id: int,
        title: str,
        content: str,
        user_id: int,
    ) -> Note:
        self._validate(title, content)

        existing_note = self.repository.get_by_id(note_id, user_id)
        if existing_note is None:
            raise NoteNotFoundError(f"Note with id {note_id} not found")

        existing_note.title = title
        existing_note.content = content
        existing_note.updated_at = utc_now()

        updated_note = self.repository.update(existing_note, user_id)
        if updated_note is None:
            raise NoteNotFoundError(f"Note with id {note_id} not found")

        logger.info("Note updated: id=%s user_id=%s", note_id, user_id)

        return updated_note

    @staticmethod
    def _validate(title: str, content: str) -> None:
        if not title or not title.strip():
            raise InvalidNoteError("Title cannot be empty")

        if len(title) > MAX_TITLE_LENGTH:
            raise InvalidNoteError(
                f"Title cannot exceed {MAX_TITLE_LENGTH} characters"
            )

        if not content or not content.strip():
            raise InvalidNoteError("Content cannot be empty")
