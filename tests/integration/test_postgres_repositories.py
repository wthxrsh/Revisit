import pytest

from secondbrain.models.document import Document, DocumentStatus
from secondbrain.repositories.postgres_document_repository import (
    PostgresDocumentRepository,
)
from secondbrain.repositories.postgres_note_repository import (
    PostgresNoteRepository,
)
from secondbrain.repositories.postgres_user_repository import (
    PostgresUserRepository,
)
from secondbrain.models.note import Note
from secondbrain.models.user import User

pytestmark = pytest.mark.integration


@pytest.fixture
def user_id(db_session):
    repository = PostgresUserRepository(db_session)
    user = repository.save(
        User(id=None, email="repo-user@example.com", password_hash="hash")
    )
    return user.id


def test_note_round_trip_with_generated_id(db_session, user_id):
    repository = PostgresNoteRepository(db_session)

    saved = repository.save(
        Note(id=None, title="DB note", content="persisted"), user_id
    )

    assert saved.id is not None
    assert repository.get_by_id(saved.id, user_id).title == "DB note"


def test_note_ownership_filter(db_session, user_id):
    repository = PostgresNoteRepository(db_session)
    saved = repository.save(
        Note(id=None, title="Private", content="secret"), user_id
    )

    assert repository.get_by_id(saved.id, user_id=user_id + 1) is None


def test_document_status_transition_guard(db_session, user_id):
    repository = PostgresDocumentRepository(db_session)
    document = repository.save(
        Document(
            user_id=user_id,
            original_filename="a.pdf",
            storage_key="key-1",
            file_size=10,
            mime_type="application/pdf",
            status=DocumentStatus.PENDING,
        )
    )

    assert repository.try_mark_processing(document.id, user_id) is True
    assert repository.try_mark_processing(document.id, user_id) is False
