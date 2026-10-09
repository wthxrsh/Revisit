# Codebase Tour

A guided, file-by-file walk-through. Use it as a map while you read the code. Paths are
relative to the repository root.

```
.
├── alembic/                     database migrations
├── docs/                        this documentation
├── src/secondbrain/             the application package
├── tests/                       unit + integration tests
├── docker-compose.yml           PostgreSQL + pgvector
├── pyproject.toml               dependencies, pytest config
└── .env.example                 all environment variables, documented
```

## `src/secondbrain/__init__.py`
Package marker.

## `src/secondbrain/config.py`
The single source of truth for configuration.

- `Settings` reads every environment variable (via `os.getenv`, with `python-dotenv`
  loading `.env`).
- Convenience properties: `max_upload_size_bytes`, `max_request_size_bytes`.
- `validate()` performs cross-field checks and raises `ValueError` on misconfiguration
  (chunk overlap vs. size, provider/API-key consistency, missing JWT secret outside tests).
- `get_settings()` is `lru_cache`d; `settings` is the shared instance.

**Read this first** — almost every other module depends on it.

## `src/secondbrain/logging_config.py`
`configure_logging()` sets up a consistent log format and level from `LOG_LEVEL`. Called
once at app startup.

## `src/secondbrain/clock.py`
`utc_now()` returns the current UTC time as a naive `datetime` (matching the naive
database columns). Centralizes time so it is easy to change — and so no module calls the
deprecated `datetime.utcnow()`.

## `src/secondbrain/exceptions.py`
The domain exception hierarchy:

```
SecondBrainError
├── NotFoundError        → NoteNotFoundError, DocumentNotFoundError, ConversationNotFoundError
├── ValidationError      → InvalidNoteError, InvalidRegistrationError,
│                          UnsupportedFileTypeError, FileTooLargeError
├── ConflictError        → NoteAlreadyExistsError, UserAlreadyExistsError
├── AuthenticationError  → InvalidCredentialsError
├── ProcessingError      → StorageError, CorruptedDocumentError,
│                          EncryptedDocumentError, EmptyDocumentError
└── ProviderError        → EmbeddingProviderError, LLMProviderError
```

Services raise these; the API layer translates them (see `api/exception_handlers.py`).

## `src/secondbrain/main.py`
Exposes the ASGI `app` object (`app = create_app()`), used by
`uvicorn secondbrain.main:app`.

## `src/secondbrain/models/`  (domain models)
Plain dataclasses, one per concept. No SQL, no framework imports.

| File | Contents |
| --- | --- |
| `note.py` | `Note` |
| `user.py` | `User` |
| `document.py` | `Document` + `DocumentStatus` constants |
| `chunk.py` | `Chunk` (with `embedding: list[float] | None`) and `ScoredChunk` (chunk + similarity + filename) |
| `conversation.py` | `Citation`, `Message`, `Conversation` |

`None`-able `id` fields express "not yet persisted".

## `src/secondbrain/database/`  (persistence)
- `connection.py` — `build_database_url()`, the SQLAlchemy `engine` (with
  `pool_pre_ping`), `SessionLocal` (`expire_on_commit=False`), and `Base`.
- `dependencies.py` — `get_db()`: the FastAPI dependency that yields a session and closes
  it. This is the override point tests use.
- `__init__.py` — imports all model modules so `Base.metadata` is complete.
- `models.py` — `NoteModel`.
- `user_models.py` — `UserModel`.
- `document_models.py` — `DocumentModel`.
- `chunk_models.py` — `ChunkModel` (uses `pgvector.sqlalchemy.Vector`).
- `conversation_models.py` — `ConversationModel`, `MessageModel` (citations stored as
  `JSONB`).

Each ORM class maps 1:1 to a table and holds *no* business logic.

## `src/secondbrain/repositories/`
The **only** layer that contains SQL/ORM queries. Each entity has an abstract interface
(a `Protocol`/ABC in the small `*_repository.py` files) and implementations.

| File | Role |
| --- | --- |
| `base.py` | `NoteRepository` interface |
| `in_memory_note_repository.py` | In-memory implementation, used by unit tests |
| `postgres_note_repository.py` | SQL implementation with owner filtering |
| `user_repository.py` / `postgres_user_repository.py` | Users |
| `document_repository.py` / `postgres_document_repository.py` | Documents, incl. `try_mark_processing` |
| `chunk_repository.py` / `postgres_chunk_repository.py` | Bulk replace + **vector search** |
| `conversation_repository.py` / `postgres_conversation_repository.py` | Conversations + messages |

Patterns worth studying:

- Repositories convert ORM rows to domain objects via a private `_to_domain(...)`.
- Every read/write of a user-owned row includes `user_id` in the `WHERE` clause
  (owner scoping).
- `PostgresChunkRepository.search` is where RAG meets SQL: `1 - (embedding <=> :q)` is the
  cosine similarity and `embedding <=> :q` is the cosine distance used for ordering.

## `src/secondbrain/services/`
Business rules and orchestration. No HTTP, no SQL.

| File | Responsibility |
| --- | --- |
| `note_service.py` | Create/get/list/update/delete notes with validation |
| `auth_service.py` | Register (normalize email, hash password) and login (issue JWT) |
| `password_service.py` | Argon2 hashing/verification via `pwdlib` |
| `jwt_service.py` | Encode/decode access tokens (`sub` = user id, `exp`) |
| `document_service.py` | Upload orchestration: store file → save row → (optionally) process; delete; reprocess |
| `processing_service.py` | Extract → chunk → embed → store, with status transitions |
| `rag_service.py` | The RAG loop: retrieve, build context, call the LLM, build citations |
| `conversation_service.py` | List/get/delete conversations and their messages |
| `processing/pdf_extractor.py` | `pypdf` extraction into `PageText`; typed errors |
| `processing/chunker.py` | Word-boundary sliding-window chunker with page provenance |
| `embedding/base.py` | `EmbeddingProvider` interface (`embed_query`, `embed_documents`, `name`) |
| `embedding/hashing.py` | Default deterministic lexical provider |
| `embedding/fastembed_provider.py` | Optional local neural provider |
| `embedding/openai_provider.py` | Optional remote provider |
| `embedding/factory.py` | `build_embedding_provider(settings)` |
| `llm/base.py` | `LLMProvider`, `LLMSource`, `LLMAnswer` |
| `llm/extractive.py` | Default offline answer provider |
| `llm/openai_provider.py` | Optional generative provider |
| `llm/factory.py` | `build_llm_provider(settings)` |

## `src/secondbrain/storage/file_storage.py`
`LocalFileStorage`: safe local storage of uploads. Handles magic-byte checks, streaming
writes with a size cap, unique key generation, partial-file cleanup, deletion, and
path-traversal protection. `StoredFile` is the returned value.

## `src/secondbrain/api/`
The HTTP boundary.

- `app.py` — `create_app()`: configures logging, validates settings, creates `FastAPI`,
  registers middleware (CORS if configured, request-size enforcement), registers exception
  handlers, and includes routers.
- `schemas.py` — Pydantic request/response models with tight constraints.
- `auth_dependencies.py` — `get_current_user` (JWT → `User`), and the shared
  `bearer_scheme`.
- `dependencies.py` — the composition root: builds services/repositories per request and
  caches stateless providers.
- `exception_handlers.py` — domain/validation/HTTP/unhandled handlers producing the JSON
  error envelope.
- `routers/health.py` — `/health`, `/ready`.
- `routers/auth.py` — `/auth/register`, `/auth/login`.
- `routers/notes.py` — notes CRUD.
- `routers/documents.py` — upload, list, get, status, process, delete.
- `routers/chat.py` — `/chat`, conversations list/get/delete.

## `alembic/`
- `env.py` — imports `secondbrain.database` so all models register, then runs migrations.
- `versions/99e9bdeef790_*.py` — users.
- `versions/b0412a229f25_*.py` — notes.
- `versions/7269842c0ece_*.py` — note ownership.
- `versions/afd8abcc560d_*.py` — documents/chunks/conversations + `vector` extension +
  HNSW index.

## `tests/`
- `conftest.py` — all fixtures:
  - sets test env vars **before** importing the app,
  - points the app at an isolated test database (`POSTGRES_TEST_DB`),
  - `db_engine` (create DB/schema once per session), `db_session` (per-test transaction
    rolled back afterwards), `client` (TestClient with `get_db` overridden),
    `registered_user` / `second_user` (real register+login through the API),
  - `repository` / `service` (in-memory, for unit tests).
- `unit/` — pure logic: notes, password hashing, JWT, chunker, embeddings, extractive LLM,
  file storage. No database.
- `integration/` — auth, notes, documents, RAG/chat, health, and postgres repositories.
  Require PostgreSQL; marked with `@pytest.mark.integration`.
- `fixtures/` — `sample.pdf`, `empty.pdf`, `encrypted.pdf` and the script that generates
  them (`generate_fixtures.py`).

## Root files
- `docker-compose.yml` — PostgreSQL 17 + pgvector, port 5435, healthcheck, named volume.
- `pyproject.toml` — dependencies, optional `embeddings`/`dev` extras, pytest config and
  markers.
- `.env.example` — every supported environment variable with defaults.
- `.github/workflows/tests.yml` — CI: spin up pgvector, install, run migrations, run tests.
