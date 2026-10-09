import pytest

from secondbrain.exceptions import InvalidNoteError, NoteNotFoundError
from secondbrain.services.note_service import NoteService


def test_create_note(service: NoteService):
    note = service.create_note(
        title="Python", content="Professional Python", user_id=1
    )

    assert note.id is not None
    assert note.title == "Python"
    assert note.content == "Professional Python"


def test_ids_are_unique(service: NoteService):
    first = service.create_note(title="A", content="a", user_id=1)
    second = service.create_note(title="A", content="a", user_id=1)

    assert first.id != second.id


def test_empty_title_fails(service: NoteService):
    with pytest.raises(InvalidNoteError):
        service.create_note(title="", content="content", user_id=1)


def test_whitespace_title_fails(service: NoteService):
    with pytest.raises(InvalidNoteError):
        service.create_note(title="   ", content="content", user_id=1)


def test_empty_content_fails(service: NoteService):
    with pytest.raises(InvalidNoteError):
        service.create_note(title="Title", content="", user_id=1)


def test_missing_note_fails(service: NoteService):
    with pytest.raises(NoteNotFoundError):
        service.get_note(999, user_id=1)


def test_update_enforces_ownership(service: NoteService):
    note = service.create_note(title="Mine", content="secret", user_id=1)

    with pytest.raises(NoteNotFoundError):
        service.update_note(note.id, "Hacked", "stolen", user_id=2)


def test_delete_enforces_ownership(service: NoteService):
    note = service.create_note(title="Mine", content="secret", user_id=1)

    with pytest.raises(NoteNotFoundError):
        service.delete_note(note.id, user_id=2)
