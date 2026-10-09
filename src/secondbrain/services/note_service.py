import logging
from secondbrain.exceptions import (
    InvalidNoteError,
    NoteAlreadyExistsError,
    NoteNotFoundError,
)
from secondbrain.models.note import Note
from secondbrain.repositories.base import NoteRepository
from datetime import datetime

logger = logging.getLogger(__name__)
class NoteService:

    def __init__(self, repository: NoteRepository):
        self.repository = repository

    def create_note(
            self,
            note_id: int,
            title: str,
            content: str,
            user_id: int,
    ) -> Note:

        logger.info("Creating note with id=%s", note_id)

        if self.repository.get_by_id(note_id, user_id) is not None:
            logger.warning("Duplicate note id=%s", note_id)

            raise NoteAlreadyExistsError(
                f"Note with id {note_id} already exists"
            )

        if not title.strip():
            logger.warning("Rejected note id=%s: empty title", note_id)
            raise InvalidNoteError("Title cannot be empty")

        if not content.strip():
            logger.warning("Rejected note id=%s: empty content", note_id)
            raise InvalidNoteError("Content cannot be empty")

        note = Note(
            id=note_id,
            title=title,
            content=content,
        )

        saved_note = self.repository.save(note, user_id)
        logger.info("Note created successfully: id=%s", note_id)

        return saved_note

    def get_note(self, note_id: int, user_id: int) -> Note:
        note = self.repository.get_by_id(note_id, user_id)

        if note is None:
            raise NoteNotFoundError(
                f"Note with id {note_id} not found"
            )

        logger.info("Fetching note id=%s for user_id=%s", note_id, user_id)
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
            raise NoteNotFoundError(
                f"Note with id {note_id} not found"
            )

    def update_note(
            self,
            note_id: int,
            title: str,
            content: str,
            user_id: int,
    ) -> Note:

        if not title.strip():
            raise InvalidNoteError("Title cannot be empty")

        if not content.strip():
            raise InvalidNoteError("Content cannot be empty")

        existing_note = self.repository.get_by_id(note_id, user_id)
        if existing_note is None:
            raise NoteNotFoundError(
                f"Note with id {note_id} not found"
            )

        existing_note.title = title
        existing_note.content = content
        existing_note.updated_at = datetime.now()

        updated_note = self.repository.update(existing_note, user_id)
        if updated_note is None:
            raise NoteNotFoundError(
                f"Note with id {note_id} not found"
            )

        logger.info("Note updated successfully: id=%s", note_id)

        return updated_note