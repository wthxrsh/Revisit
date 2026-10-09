from secondbrain.models.note import Note
from secondbrain.repositories.postgres_note_repository import (
    PostgresNoteRepository,
)


def test_save_and_get_note(db_session):
    repository = PostgresNoteRepository(db_session)

    note = Note(
        id=1000,
        title="PostgreSQL",
        content="Learning SQLAlchemy",
    )

    repository.save(note)

    result = repository.get_by_id(1000)

    assert result is not None
    assert result.id == 1000
    assert result.title == "PostgreSQL"
    assert result.content == "Learning SQLAlchemy"