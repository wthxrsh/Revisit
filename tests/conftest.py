import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from secondbrain.database.connection import Base, DATABASE_URL
from secondbrain.database.models import NoteModel
from secondbrain.repositories.in_memory_note_repository import (
    InMemoryNoteRepository,
)
from secondbrain.services.note_service import NoteService


@pytest.fixture
def repository() -> InMemoryNoteRepository:
    return InMemoryNoteRepository()


@pytest.fixture
def service(
    repository: InMemoryNoteRepository,
) -> NoteService:
    return NoteService(repository)


@pytest.fixture
def db_session():
    engine = create_engine(DATABASE_URL)

    Base.metadata.create_all(bind=engine)

    TestingSessionLocal = sessionmaker(
        bind=engine,
        autoflush=False,
        autocommit=False,
    )

    session = TestingSessionLocal()

    try:
        yield session
    finally:
        session.rollback()
        session.close()

        with TestingSessionLocal() as cleanup_session:
            cleanup_session.query(NoteModel).delete()
            cleanup_session.commit()

        engine.dispose()