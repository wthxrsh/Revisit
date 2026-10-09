# SecondBrain — Implementation Plan

This document records the audit findings and the phased plan that was executed to
complete the project. It also tracks what is complete and what remains limited.

## 0. Verification

- **97 tests pass** (`pytest -q`): 46 unit + 51 integration.
- Integration tests run against an isolated, on-demand `secondbrain_test` database using a
  transaction-per-test that is rolled back, so development data is never touched.
- `alembic upgrade head` creates the full schema (including the `vector` extension and the
  HNSW index) on an empty database.
- The default configuration (hashing embeddings + extractive LLM) needs no API keys and no
  network access.
- `alembic upgrade head` and `pytest -q` also run in CI against `pgvector/pgvector:pg17`.


## 1. Audit summary (starting point)

- FastAPI app with `/health`, notes CRUD, and JWT auth existed but lived in a single
  `api/app.py` module.
- Notes and users had PostgreSQL and in-memory repositories, but tests still used the
  old method signatures (before ownership) and unauthenticated API calls. Result:
  **14 failed, 5 passed**.
- `notes.id` and `users.id` already had database sequences, so IDs were effectively
  database-generated even though the client supplied the note id.
- `README.md` was a stub, there was no `docs/` directory, and there was no vector
  database support: the running `postgres:17` image had **no pgvector extension**.
- Python 3.14 with recent FastAPI/SQLAlchemy 2.x/Pydantic 2.x. `fastembed` and
  `onnxruntime` publish cp314 wheels, so a real local neural embedding provider is
  installable.

## 2. Key decisions

| Decision | Choice | Rationale |
| --- | --- | --- |
| Vector store | PostgreSQL + pgvector | Single source of truth, ownership filtering in the same transaction, no extra service to operate. |
| Embeddings | Provider interface; default deterministic `hashing`, optional `fastembed` (local neural) and `openai` | Zero-setup start and offline tests, while allowing true semantic search locally. |
| LLM | Provider interface; default deterministic `extractive`, optional `openai` | Grounded, cited answers without paid credentials; pluggable real LLM. |
| Background jobs | Synchronous processing by default, with an explicit `/process` endpoint | Local deployment, small PDFs. Avoids running a second distributed system for no benefit. |
| Note IDs | Database-generated (client no longer supplies id) | Removes client-controlled identifiers and duplicate-id edge cases. |
| Test database | Isolated `*_test` database, created on demand | Tests must never touch the development database. |

## 3. Phases

### Phase 1 — Audit and stabilize (COMPLETE)
- Expanded settings with validation and new options (upload limits, embedding/LLM
  providers, storage, CORS).
- Split API into routers (`health`, `auth`, `notes`, later `documents`, `chat`).
- Added central DI module.
- Made note ids database-generated; added tight Pydantic validation.
- Reworked the test suite into `tests/unit` and `tests/integration`.
- Switched Docker Compose to the `pgvector/pgvector:pg17` image (same Postgres major,
  data volume preserved).

### Phase 2 — Documents and uploads (COMPLETE)
- `documents` table + migration, repository, service, schemas, endpoints.
- Safe local storage: generated storage keys, streaming write, size + magic-byte
  validation, partial-write cleanup, path-traversal guards.
- Ownership enforced in repository queries.

### Phase 3 — Extraction and chunking (COMPLETE)
- `chunks` table + migration and pgvector column + HNSW index.
- `pypdf` extraction preserving page numbers; explicit errors for encrypted,
  corrupt, and empty documents.
- Word-boundary chunker with configurable size/overlap and page provenance.
- Idempotent reprocessing: prior chunks replaced atomically.

### Phase 4 — Embeddings and retrieval (COMPLETE)
- Provider-independent embedding interface (`hashing`, `fastembed`, `openai`).
- Owner-filtered, top-k, cosine-distance retrieval with a similarity threshold.

### Phase 5 — RAG assistant (COMPLETE)
- `conversations` + `messages` tables; `/chat` with grounded answers, citations,
  no-result handling, and provider-failure handling.
- Extractive local answer provider and OpenAI chat provider.

### Phase 6 — Hardening (COMPLETE)
- Consistent error envelope, structured logging, startup validation, health/readiness,
  request size limits, CI workflow, `.env.example`.

### Phase 7 — Documentation and verification (COMPLETE)
- `docs/` learning material and final verification.

## 4. Known limitations

- Processing is **synchronous**. Large PDFs block the request. A Redis-backed worker is
  the documented next step (see `docs/DECISIONS.md`).
- The default embedding provider (`hashing`) is a deterministic lexical feature-hash
  vector, **not** a neural semantic model. Use `fastembed` for true semantic search.
- The default LLM provider (`extractive`) selects sentences from retrieved passages; it
  does not generate free-form prose. Use `openai` for generation.
- Vector dimensions are fixed at migration time by `EMBEDDING_DIM`; changing the
  embedding model dimensions requires a migration and full reindex.
- No OCR: scanned/image-only PDFs are reported as having no extractable text.
- No user-deletion flow; foreign keys are owned by the user but account deletion is out
  of scope.
- Rate limiting on auth endpoints is documented but not implemented in the local build.
