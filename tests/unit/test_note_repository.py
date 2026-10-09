from secondbrain.models.note import Note
from secondbrain.repositories.in_memory_note_repository import (
    InMemoryNoteRepository,
)


def test_save_assigns_id(repository: InMemoryNoteRepository):
    note = Note(id=None, title="Python", content="Learning")

    saved = repository.save(note, user_id=1)

    assert saved.id is not None
    assert repository.get_by_id(saved.id, user_id=1) == saved


def test_get_nonexistent_note(repository: InMemoryNoteRepository):
    assert repository.get_by_id(999, user_id=1) is None


def test_delete_note(repository: InMemoryNoteRepository):
    saved = repository.save(
        Note(id=None, title="Python", content="Learning"), user_id=1
    )

    assert repository.delete(saved.id, user_id=1) is True
    assert repository.get_by_id(saved.id, user_id=1) is None


def test_delete_nonexistent_note(repository: InMemoryNoteRepository):
    assert repository.delete(999, user_id=1) is False


def test_ownership_is_enforced(repository: InMemoryNoteRepository):
    saved = repository.save(
        Note(id=None, title="Private", content="Secret"), user_id=1
    )

    assert repository.get_by_id(saved.id, user_id=2) is None
    assert repository.delete(saved.id, user_id=2) is False
    assert repository.update(saved, user_id=2) is None
    assert repository.get_all(user_id=2) == []


def test_search_and_pagination(repository: InMemoryNoteRepository):
    repository.save(Note(id=None, title="Alpha", content="x"), user_id=1)
    repository.save(Note(id=None, title="Beta", content="alpha"), user_id=1)
    repository.save(Note(id=None, title="Gamma", content="y"), user_id=1)

    matches = repository.get_all(user_id=1, search="alpha")

    assert len(matches) == 2

    page = repository.get_all(user_id=1, limit=2, offset=0)

    assert len(page) == 2
