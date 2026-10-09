from secondbrain.models.note import Note
from secondbrain.repositories.in_memory_note_repository import (
    InMemoryNoteRepository,
)


def test_save_note(repository: InMemoryNoteRepository):
    note = Note(
        id=1,
        title="Python",
        content="Learning professional Python",
    )

    saved_note = repository.save(note)

    assert saved_note == note
    assert repository.get_by_id(1) == note


def test_get_nonexistent_note(repository: InMemoryNoteRepository):
    result = repository.get_by_id(999)

    assert result is None


def test_delete_note(repository: InMemoryNoteRepository):
    note = Note(
        id=1,
        title="Python",
        content="Learning professional Python",
    )

    repository.save(note)

    result = repository.delete(1)

    assert result is True
    assert repository.get_by_id(1) is None


def test_delete_nonexistent_note(repository: InMemoryNoteRepository):
    result = repository.delete(999)

    assert result is False