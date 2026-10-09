# Design Decisions

Short, ADR-style records: the decision, the alternatives considered, and the consequences.
When you wonder "why is it like this?", the answer should be here.

---

## ADR-1: Use PostgreSQL + pgvector as the single data store

**Status:** accepted.

**Context.** The app needs relational data (users, documents, chunks, conversations) *and*
vector similarity search over chunk embeddings.

**Options.** (a) a dedicated vector database (Qdrant/pgvector-server) alongside PostgreSQL;
(b) PostgreSQL with the `pgvector` extension only.

**Decision.** Use PostgreSQL + pgvector only.

**Consequences.**
- One service to run, back up, and migrate.
- Ownership filtering and vector search happen in **one** query and **one** transaction —
  there is no window where a chunk is indexed but not yet owner-scoped.
- Vector search is "good enough and getting better" (HNSW index) rather than best-in-class.
- Switching to a dedicated vector DB later means reworking the chunk repository only
  (services do not know how vectors are stored).

---

## ADR-2: Provider interfaces with offline defaults

**Status:** accepted.

**Context.** Real embeddings/LLMs need network access, API keys, and (for local neural
models) large downloads. That makes the app hard to run and test out of the box.

**Decision.** Define `EmbeddingProvider` and `LLMProvider` interfaces. Ship deterministic,
offline defaults (`hashing`, `extractive`) and optional real providers (`fastembed`,
`openai`) selected by environment variables.

**Consequences.**
- The app runs and the full test suite passes with **no keys and no downloads**.
- The defaults are honest about being lexical/extractive, not "fake AI".
- Switching to production quality is a config change, not a code change.
- Two code paths to maintain per capability; the interfaces keep them small.

**Why not mock the providers in tests instead?** The deterministic defaults are also used
in development and are genuinely useful, so they earn their place beyond testing.

---

## ADR-3: Database-generated note ids (no client-supplied ids)

**Status:** accepted; breaking change to the notes API.

**Context.** Earlier the client supplied `note.id`. That allowed collisions, weird
client-controlled identifiers, and a "duplicate id" error path that only existed because
the client chose ids.

**Decision.** The client sends only `title` and `content`; the database assigns `id`.

**Consequences.**
- No duplicate-id edge cases; ids are a storage concern.
- The API is simpler: `POST /notes {title, content}`.
- Old clients that sent an `id` are no longer compatible (intentional).

---

## ADR-4: Synchronous document processing

**Status:** accepted for the current scope.

**Context.** PDF processing (extract → chunk → embed) can take seconds to minutes.

**Options.** (a) a background worker + queue (Celery/RQ/Redis); (b) process synchronously in
the request.

**Decision.** Process synchronously by default (`PROCESS_ON_UPLOAD=true`), with an explicit
`POST /documents/{id}/process` endpoint and a `pending`/`processing`/`completed`/`failed`
status machine.

**Consequences.**
- No second service (Redis/worker) to run for a local, small-PDF use case.
- Large PDFs block the request — this is the main known limitation.
- The status machine and `try_mark_processing` guard are already in place, so moving to a
  worker later is mostly a matter of calling the existing service from a worker instead of
  in-request.

---

## ADR-5: Ownership enforced in the repository layer

**Status:** accepted.

**Context.** Multi-user data must never leak across users.

**Options.** (a) check ownership in services/routes; (b) enforce it in the data layer.

**Decision.** Every repository method that touches a user-owned row takes a `user_id` and
includes it in the SQL `WHERE`. Not-found and not-owned are indistinguishable (`404`).

**Consequences.**
- A new endpoint cannot accidentally skip the check by forgetting a service-level guard.
- Tests can assert isolation at the repository level (fast, no HTTP).
- Repositories carry a little more boilerplate (`user_id` parameters) — an accepted trade.

---

## ADR-6: Domain models separated from ORM models

**Status:** accepted.

**Context.** Mixing SQLAlchemy models into business logic couples the app to the ORM and
makes services hard to test without a database.

**Decision.** Domain objects are plain dataclasses (`models/`); ORM classes live only in
`database/`. Repositories translate between them.

**Consequences.**
- Services and unit tests need no database.
- The storage engine can be replaced behind the repository interface.
- A little mapping code in each repository (`_to_domain` and the reverse).

---

## ADR-7: Fix vector dimension at migration time

**Status:** accepted.

**Context.** `pgvector` columns need a fixed dimension; the HNSW index is built for it.

**Decision.** `chunks.embedding` is `vector(EMBEDDING_DIM)` (default 384), chosen when the
migration runs.

**Consequences.**
- Fast, indexable search.
- Changing to a model with a different dimension requires a migration **and**
  re-embedding every chunk. This is documented everywhere it matters.

---

## ADR-8: Local filesystem storage behind a storage abstraction

**Status:** accepted.

**Context.** Uploaded PDFs are needed at processing time.

**Options.** Object storage (S3), database BLOBs, local filesystem.

**Decision.** `LocalFileStorage` behind a small interface. It generates its own storage
keys, validates magic bytes and size, cleans up partial writes, and guards against path
traversal.

**Consequences.**
- Zero external dependencies for local use.
- Not horizontally scalable as-is; swapping to S3 means implementing the same interface.
- The client filename is display-only and sanitized, never used as a path.

---

## ADR-9: Isolated test database with transaction rollback

**Status:** accepted.

**Context.** Tests must never delete or mutate development data, and should be fast.

**Decision.** `conftest.py` points the app at `POSTGRES_TEST_DB` (default
`secondbrain_test`), creates it on demand, creates the schema once per session, and wraps
each test in a transaction that is rolled back. `join_transaction_mode="create_savepoint"`
lets code that calls `session.commit()` still be undone.

**Consequences.**
- Tests are isolated from each other and from development data.
- One shared engine; per-test work is cheap.
- The test database is a disposable artifact and can be dropped/recreated any time.

---

## ADR-10: Startup validation and a single settings object

**Status:** accepted.

**Context.** Misconfiguration (chunk overlap ≥ size, OpenAI provider without a key, missing
JWT secret) should fail loudly, not mysteriously at request time.

**Decision.** `Settings.validate()` runs at app creation and raises on invalid combinations.
All environment reading happens in `config.py`.

**Consequences.**
- Fail-fast, clear errors.
- One place to see every knob.
- Some validation (e.g. JWT secret) is relaxed under `ENVIRONMENT=test` so tests need no
  secret.
