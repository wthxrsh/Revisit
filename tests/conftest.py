import os
import tempfile

os.environ.setdefault("ENVIRONMENT", "test")
os.environ.setdefault("EMBEDDING_PROVIDER", "hashing")
os.environ.setdefault("LLM_PROVIDER", "extractive")
os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key-not-for-production-1234567890")
os.environ.setdefault("JWT_ALGORITHM", "HS256")
os.environ.setdefault(
    "DOCUMENT_STORAGE_PATH",
    tempfile.mkdtemp(prefix="secondbrain-test-storage-"),
)

_TEST_DB = os.environ.get("POSTGRES_TEST_DB", "secondbrain_test")
_ADMIN_DB = os.environ.get("POSTGRES_ADMIN_DB", "postgres")
os.environ["POSTGRES_DB"] = _TEST_DB

import pytest  # noqa: E402
from sqlalchemy import create_engine, text  # noqa: E402
from sqlalchemy.exc import OperationalError  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402

from secondbrain.database.connection import (  # noqa: E402
    Base,
    build_database_url,
)
from secondbrain.repositories.in_memory_note_repository import (  # noqa: E402
    InMemoryNoteRepository,
)
from secondbrain.services.note_service import NoteService  # noqa: E402

import secondbrain.database  # noqa: E402,F401  (register all models)


@pytest.fixture
def repository() -> InMemoryNoteRepository:
    return InMemoryNoteRepository()


@pytest.fixture
def service(repository: InMemoryNoteRepository) -> NoteService:
    return NoteService(repository)


@pytest.fixture(scope="session")
def db_engine():
    from secondbrain.config import settings

    admin_url = build_database_url(database=_ADMIN_DB)

    try:
        admin_engine = create_engine(admin_url, isolation_level="AUTOCOMMIT")
        with admin_engine.connect() as connection:
            exists = connection.execute(
                text("SELECT 1 FROM pg_database WHERE datname = :name"),
                {"name": settings.postgres_db},
            ).scalar()

            if not exists:
                connection.execute(
                    text(f'CREATE DATABASE "{settings.postgres_db}"')
                )

        admin_engine.dispose()
    except OperationalError as error:
        pytest.skip(f"PostgreSQL is not available: {error}")

    engine = create_engine(build_database_url(), future=True)

    with engine.connect() as connection:
        connection.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        connection.commit()

    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)

    yield engine

    engine.dispose()


@pytest.fixture
def db_session(db_engine):
    connection = db_engine.connect()
    transaction = connection.begin()

    session_factory = sessionmaker(
        bind=connection,
        join_transaction_mode="create_savepoint",
        autoflush=False,
        expire_on_commit=False,
    )

    session = session_factory()

    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()


@pytest.fixture
def client(db_session):
    from fastapi.testclient import TestClient

    from secondbrain.api.app import app
    from secondbrain.database.dependencies import get_db

    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app, raise_server_exceptions=False) as test_client:
        yield test_client

    app.dependency_overrides.clear()


@pytest.fixture
def registered_user(client):
    import uuid

    email = f"user-{uuid.uuid4().hex}@example.com"
    password = "password123"

    register = client.post(
        "/auth/register", json={"email": email, "password": password}
    )
    assert register.status_code == 201, register.text

    login = client.post(
        "/auth/login", json={"email": email, "password": password}
    )
    assert login.status_code == 200, login.text

    token = login.json()["access_token"]

    return {
        "email": email,
        "password": password,
        "id": register.json()["id"],
        "headers": {"Authorization": f"Bearer {token}"},
    }


@pytest.fixture
def second_user(client):
    import uuid

    email = f"user-{uuid.uuid4().hex}@example.com"
    password = "password123"

    register = client.post(
        "/auth/register", json={"email": email, "password": password}
    )
    assert register.status_code == 201, register.text

    login = client.post(
        "/auth/login", json={"email": email, "password": password}
    )
    token = login.json()["access_token"]

    return {
        "email": email,
        "password": password,
        "id": register.json()["id"],
        "headers": {"Authorization": f"Bearer {token}"},
    }
