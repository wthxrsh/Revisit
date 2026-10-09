# Architecture

This document explains how SecondBrain is put together and why. Read it after the
[README](../README.md) and before the [codebase tour](CODEBASE_TOUR.md).

## 1. The big picture

SecondBrain is a layered web service. Each layer only knows about the layer beneath it.

```
┌─────────────────────────────────────────────────────────────────────┐
│ HTTP client (curl, browser, /docs)                                  │
└───────────────────────────────┬─────────────────────────────────────┘
                                │
┌───────────────────────────────▼─────────────────────────────────────┐
│ API layer  (src/secondbrain/api/)                                   │
│  • app.py            – create_app(): wiring, middleware, handlers   │
│  • routers/*.py      – HTTP endpoints, request/response shapes      │
│  • schemas.py        – Pydantic request/response models             │
│  • auth_dependencies – extracts the current User from the JWT       │
│  • dependencies.py   – builds services/repositories per request     │
│  • exception_handlers– maps domain errors to HTTP responses         │
└───────────────────────────────┬─────────────────────────────────────┘
                                │ calls services
┌───────────────────────────────▼─────────────────────────────────────┐
│ Service layer  (src/secondbrain/services/)                          │
│  • note_service, auth_service, document_service,                    │
│    processing_service, rag_service, conversation_service            │
│  • processing/       – pdf_extractor, chunker                       │
│  • embedding/        – provider interface + hashing/fastembed/openai│
│  • llm/              – provider interface + extractive/openai       │
│  Business rules live here. No SQL, no HTTP.                         │
└───────────────────────────────┬─────────────────────────────────────┘
                                │ calls repositories
┌───────────────────────────────▼─────────────────────────────────────┐
│ Repository layer  (src/secondbrain/repositories/)                   │
│  The ONLY place that speaks SQL / the ORM.                          │
│  One abstract interface + one (or more) implementations per entity. │
└───────────────────────────────┬─────────────────────────────────────┘
                                │ SQLAlchemy ORM
┌───────────────────────────────▼─────────────────────────────────────┐
│ Persistence  (src/secondbrain/database/)                            │
│  • connection.py  – engine, session factory, Base                   │
│  • *_models.py    – SQLAlchemy ORM classes (tables)                 │
│  PostgreSQL + pgvector (single source of truth)                     │
└─────────────────────────────────────────────────────────────────────┘
```

Around both layers sit two cross-cutting concerns:

- **Domain models** (`src/secondbrain/models/`): plain `@dataclass` objects
  (`Note`, `User`, `Document`, `Chunk`, `Conversation`, `Message`, `Citation`). They carry
  data between layers and are **not** tied to the database.
- **Exceptions** (`src/secondbrain/exceptions.py`): a small hierarchy rooted at
  `SecondBrainError`. Services raise these; the API maps them to HTTP codes in one place.

## 2. Why two sets of models?

This is the single most important design idea in the codebase.

| | Domain models (`models/`) | Database models (`database/*_models.py`) |
| --- | --- | --- |
| Technology | `@dataclass` | SQLAlchemy ORM |
| Example fields | `Note(id, title, content, ...)` | `NoteModel` with `mapped_column(...)` |
| Knows about SQL? | No | Yes |
| Used by | Everything | Only repositories |

Repositories **translate** between the two (`._to_domain(...)` and the reverse). The rest of
the app depends on the domain models, so services and routes never import SQLAlchemy types.
This keeps the business logic testable without a database and lets the storage layer change
independently.

## 3. Request lifecycle (a typical authenticated write)

Take `POST /notes`:

1. **Routing** — FastAPI matches `api/routers/notes.py::create_note`.
2. **Auth** — the route depends on `get_current_user`
   (`api/auth_dependencies.py`). It:
   - reads the `Authorization: Bearer <jwt>` header,
   - decodes and validates the JWT (`services/jwt_service.py`),
   - loads the `User` from the database by id,
   - raises `401` if anything is missing or invalid.
3. **Dependency injection** — `get_note_service` (`api/dependencies.py`) builds a
   `NoteService` backed by a `PostgresNoteRepository` bound to the request's DB session.
   The session itself comes from `get_db` (`database/dependencies.py`), which opens a
   session, yields it, and always closes it afterwards.
4. **Validation** — the body is parsed into `CreateNoteRequest` (Pydantic). Field-level
   errors become `422` automatically.
5. **Service** — `NoteService.create_note` validates the title/content, builds a `Note`
   with `id=None`, and calls the repository.
6. **Repository** — `PostgresNoteRepository.save` inserts a `NoteModel`, commits, refreshes
   to read the **database-generated id**, and returns a domain `Note`.
7. **Response** — the route returns the `Note`; FastAPI serializes it via
   `NoteResponse` (`from_attributes=True` reads the dataclass attributes).

Errors raised anywhere in steps 3–6 that derive from `SecondBrainError` are turned into a
consistent JSON envelope by `domain_error_handler`:

```json
{ "error": "not_found", "message": "Note with id 5 not found" }
```

## 4. Ownership and security model

Security is enforced at multiple layers, deliberately:

- **Authentication** — every non-public route depends on `get_current_user`. Missing or
  invalid tokens produce `401` with a `WWW-Authenticate: Bearer` header.
- **Authorization (owner scoping)** — every repository method that reads or mutates a
  user-owned row takes a `user_id` and includes `where(user_id = :user_id)` in the SQL.
  A mismatch simply returns "not found", so users cannot even learn that another user's
  resource exists.
- **Password storage** — passwords are hashed with Argon2 via `pwdlib`
  (`services/password_service.py`). Plaintext is never stored or logged.
- **File storage** — uploads are written through `storage/file_storage.py`, which:
  - accepts streams (never trusts a client-provided size),
  - checks the PDF magic bytes (`%PDF`),
  - enforces a maximum size and deletes any partial file on failure,
  - generates its own storage key (the client filename is only kept for display and is
    sanitized), preventing path traversal.
- **Request size** — a middleware rejects oversized requests early (`413`).
- **Configuration** — `config.py::Settings.validate()` fails fast at startup if, for
  example, `CHUNK_OVERLAP >= CHUNK_SIZE` or an OpenAI provider is selected without a key.
  In production (`ENVIRONMENT != test`) a missing `JWT_SECRET_KEY` is a hard error.

## 5. Data model

```
users ─┬─< notes
       ├─< documents ─< chunks
       └─< conversations ─< messages
```

- `users(id, email unique, password_hash, created_at)`
- `notes(id, user_id→users, title, content, created_at, updated_at)`
- `documents(id, user_id→users, original_filename, storage_key unique, file_size,
  mime_type, status, error_message, page_count, created_at, updated_at, processed_at)`
- `chunks(id, document_id→documents, user_id→users, chunk_index, page_number, page_end,
  content, embedding vector(384), created_at)` with a unique `(document_id, chunk_index)`
  constraint and an HNSW index on `embedding`.
- `conversations(id, user_id→users, title, created_at)`
- `messages(id, conversation_id→conversations, role, content, citations jsonb, created_at)`

The vector column is defined by `settings.embedding_dim` and is frozen at migration time.
`document_id` and `user_id` both have `ON DELETE CASCADE`.

The migration chain (in order):

1. `99e9bdeef790` — create `users`.
2. `b0412a229f25` — create `notes`.
3. `7269842c0ece` — add note ownership (`notes.user_id`).
4. `afd8abcc560d` — add `documents`, `chunks`, `conversations`, `messages`, the `vector`
   extension, and the HNSW index.

## 6. Document processing pipeline

Processing is **synchronous** by default (`PROCESS_ON_UPLOAD=true`), so an upload returns
once the document is indexed. There is also an explicit `POST /documents/{id}/process` for
reprocessing.

```
upload bytes
   │
   ▼
LocalFileStorage.save_stream      validates magic bytes + size, stores under a key
   │
   ▼
documents row (status=pending)
   │
   ▼
DocumentProcessingService.process
   │  try_mark_processing()   ← atomic guard: only one worker can flip pending→processing
   ├─ PdfTextExtractor.extract  per-page text (errors: encrypted / corrupt / empty)
   ├─ TextChunker.chunk_pages   word-boundary windows with overlap + page provenance
   ├─ EmbeddingProvider.embed_documents
   ├─ ChunkRepository.replace_for_document   delete old chunks, insert new (idempotent)
   └─ document.status = completed | failed (with error_message)
```

The `try_mark_processing` guard is implemented as a single conditional `UPDATE ... WHERE
status != 'processing'` and returns whether a row was affected. This makes concurrent
processing attempts safe without application-level locks.

## 7. Retrieval and the RAG assistant

```
POST /chat {question}
   │
   ▼
RagService.ask
   ├─ resolve/create conversation, store the user message
   ├─ embed the question
   ├─ ChunkRepository.search  ── SQL:
   │      SELECT ..., 1 - (embedding <=> :q) AS score
   │      WHERE user_id = :me AND embedding IS NOT NULL [AND document_id IN (...)]
   │      ORDER BY embedding <=> :q  LIMIT :k
   ├─ build a bounded context (max_context_chars)
   ├─ LLMProvider.generate(question, sources)
   ├─ map cited source indexes back to Chunk/Document rows → Citations
   └─ store the assistant message (answer + citations) and return ChatResponse
```

Key properties:

- Retrieval is **owner-filtered** in SQL, so a user can never retrieve another user's
  chunks even if they pass `document_ids`.
- `min_similarity` gates weak matches; if nothing qualifies, the service returns a
  fixed "I could not find…" answer with `grounded=false` and no citations.
- `grounded` is `true` only when the provider actually cited at least one retrieved chunk.
- The optional `document_ids` filter narrows the search to specific documents.

See [RAG_EXPLAINED.md](RAG_EXPLAINED.md) for the concepts and the exact algorithms.

## 8. Configuration and dependency injection

`config.py` is a single `Settings` object read from environment variables (with
`.env` support) and validated at import/startup. Everything that is environment-dependent
(upload limits, chunk size, providers, model names, retrieval parameters, storage path,
CORS) comes from there — there are no scattered `os.getenv` calls in the rest of the code.

`api/dependencies.py` is the composition root. It defines:

- `get_db` — one DB session per request (from `database/dependencies.py`).
- Repository/service factories that take `get_db`.
- `@lru_cache` provider singletons (`get_embedding_provider`, `get_llm_provider`,
  `get_file_storage`, `get_pdf_extractor`, `get_text_chunker`).

Because dependencies are plain functions, tests override them with
`app.dependency_overrides` (for example to point `get_db` at a test session).

## 9. Error handling

`exceptions.py` defines the hierarchy; `api/exception_handlers.py` maps it to HTTP:

| Exception (or base) | HTTP | `error` code |
| --- | --- | --- |
| `NotFoundError` | 404 | `not_found` |
| `ValidationError` | 400 | `validation_error` |
| `ConflictError` | 409 | `conflict` |
| `AuthenticationError` | 401 | `unauthorized` |
| `InvalidCredentialsError` | 401 | `invalid_credentials` |
| `FileTooLargeError` | 413 | `file_too_large` |
| `UnsupportedFileTypeError` | 415 | `unsupported_media_type` |
| `ProviderError` | 503 | `provider_error` |
| `RequestValidationError` | 422 | `request_validation_error` |
| any unhandled exception | 500 | `internal_error` |

Every error response has the same shape: `{"error": ..., "message": ...}`. The unhandled
handler logs the full traceback but returns a generic message, so internals never leak to
clients.
