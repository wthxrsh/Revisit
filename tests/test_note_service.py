import pytest

from secondbrain.exceptions import (
    InvalidNoteError,
    NoteAlreadyExistsError,
    NoteNotFoundError,
)
from secondbrain.services.note_service import NoteService


def test_create_note(service: NoteService):
    note = service.create_note(
        1,
        "Python",
        "Professional Python",
    )

    assert note.id == 1
    assert note.title == "Python"
    assert note.content == "Professional Python"


def test_duplicate_note_fails(service: NoteService):
    service.create_note(
        1,
        "Python",
        "Professional Python",
    )

    with pytest.raises(NoteAlreadyExistsError):
        service.create_note(
            1,
            "Another",
            "Another note",
        )


def test_empty_title_fails(service: NoteService):
    with pytest.raises(InvalidNoteError):
        service.create_note(
            1,
            "",
            "Some content",
        )


def test_empty_content_fails(service: NoteService):
    with pytest.raises(InvalidNoteError):
        service.create_note(
            1,
            "Python",
            "",
        )


def test_missing_note_fails(service: NoteService):
    with pytest.raises(NoteNotFoundError):
        service.get_note(999)