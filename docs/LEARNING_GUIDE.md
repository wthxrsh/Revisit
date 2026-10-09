# Learning Guide

This guide is for you if you know some Python but are newer to FastAPI, SQLAlchemy, or
retrieval-augmented generation (RAG). It gives you a **reading order** and, at each step,
**what to understand** and **what to try**.

The goal is not to memorize the code but to be able to answer: *"If I wanted to change X,
where would I go, and why is it built that way?"*

---

## Before you start

Have the app running (see the [README](../README.md) Quickstart). You will learn much
faster if you can call the API and watch the logs while you read.

Useful commands:

```bash
docker compose up -d          # database
alembic upgrade head          # create schema
uvicorn secondbrain.main:app --reload   # run the API (watch the logs)
pytest tests/unit -q          # fast feedback while reading
```

Open <http://127.0.0.1:8000/docs> to try requests interactively.

---

## Day 1 — Get the shape of the project

Read, in order:

1. [`README.md`](../README.md) — what the product does.
2. [`docs/ARCHITECTURE.md`](ARCHITECTURE.md) — the layer diagram and request lifecycle.
3. [`docs/GLOSSARY.md`](GLOSSARY.md) — keep it open; look up words as you meet them.

Then answer these questions out loud:

- What are the four main layers, and which one is allowed to write SQL?
- What is the difference between a *domain model* and a *database model*?
- Where does authentication happen, and where does authorization happen?

**Try it:** start the server, call `GET /health` and `GET /ready`. Which one needs the
database?

---

## Day 2 — Configuration and the API boundary

Read:

1. `src/secondbrain/config.py` — every knob and the `validate()` rules.
2. `src/secondbrain/api/app.py` — how the app is assembled.
3. `src/secondbrain/api/routers/health.py` and `auth.py`.
4. `src/secondbrain/api/schemas.py` — the request/response contracts.

Understand: settings are read once and validated at startup; routers are thin; Pydantic
schemas define and enforce the API shape.

**Try it:** change `MAX_UPLOAD_SIZE_MB` in `.env`, restart, and confirm uploads over the
limit fail. Then break a rule (e.g. set `CHUNK_OVERLAP` larger than `CHUNK_SIZE`) and see
the app refuse to start.

---

## Day 3 — Auth and ownership

Read:

1. `src/secondbrain/services/password_service.py` — why hashing matters.
2. `src/secondbrain/services/jwt_service.py` — what a token contains.
3. `src/secondbrain/api/auth_dependencies.py` — how a token becomes a `User`.
4. `src/secondbrain/services/auth_service.py` — register/login.
5. `src/secondbrain/repositories/postgres_note_repository.py` — note the `user_id` in
   every query.
6. `tests/integration/test_notes_api.py` — the ownership tests.

Understand: authentication answers *who are you*; authorization answers *may you touch
this row*. The second is enforced in repositories, so it cannot be forgotten in a service.

**Try it:** register two users, create a note as user A, and try to read it as user B.
You should get `404`, not `403` — the API does not reveal that the note exists.

---

## Day 4 — Documents, storage, and processing

Read:

1. `src/secondbrain/storage/file_storage.py` — safe file handling.
2. `src/secondbrain/services/document_service.py` — upload orchestration.
3. `src/secondbrain/services/processing/pdf_extractor.py` — PDF → text per page.
4. `src/secondbrain/services/processing/chunker.py` — text → overlapping chunks.
5. `src/secondbrain/services/processing_service.py` — the pipeline and status machine.
6. `tests/unit/test_chunker.py` and `tests/integration/test_documents_api.py`.

Understand: why the storage key is generated (not the client filename); why chunking
tracks page numbers; why `try_mark_processing` is a conditional `UPDATE`.

**Try it:** upload `tests/fixtures/sample.pdf`, then look at the database:

```bash
docker compose exec postgres psql -U secondbrain -d secondbrain \
  -c "select id, status, page_count from documents;" \
  -c "select chunk_index, page_number, left(content, 40) from chunks;"
```

---

## Day 5 — Embeddings and retrieval

Read:

1. `src/secondbrain/services/embedding/base.py` — the interface.
2. `src/secondbrain/services/embedding/hashing.py` — the default (and its honest docstring).
3. `src/secondbrain/repositories/postgres_chunk_repository.py::search` — the vector query.
4. `src/secondbrain/services/embedding/fastembed_provider.py` and `openai_provider.py`.
5. `tests/unit/test_hashing_embedding.py`.

Understand: what a vector is, what cosine similarity measures, and why the *same* provider
must be used for documents and queries. Be able to explain why the default provider is
"lexical, not semantic".

**Try it:** install the real embeddings (`pip install -e ".[embeddings]"`), set
`EMBEDDING_PROVIDER=fastembed`, re-process a document, and compare retrieval quality for a
query that uses different words than the document.

---

## Day 6 — The RAG loop

Read:

1. `src/secondbrain/services/rag_service.py` — the whole loop.
2. `src/secondbrain/services/llm/base.py` — `LLMSource` and `LLMAnswer`.
3. `src/secondbrain/services/llm/extractive.py` — how citations are produced offline.
4. `src/secondbrain/services/llm/openai_provider.py` — a real generative provider.
5. `tests/integration/test_rag_api.py` — grounded, refusal, and isolation tests.
6. [`docs/RAG_EXPLAINED.md`](RAG_EXPLAINED.md).

Understand: retrieval ≠ generation; `grounded` means "we cited a retrieved chunk"; the
`min_similarity` threshold is what lets the assistant refuse.

**Try it:** ask a question unrelated to your documents and observe `grounded=false`. Then
set `RETRIEVAL_MIN_SIMILARITY` fairly high and ask a vaguely related question.

---

## Day 7 — Databases, migrations, and tests

Read:

1. `src/secondbrain/database/connection.py`.
2. `alembic/versions/*.py` in order.
3. `alembic/env.py`.
4. `tests/conftest.py` — especially `db_engine`, `db_session`, and `client`.
5. `docs/DECISIONS.md` and `docs/REVIEW_ROADMAP.md`.

Understand: why tests use an isolated database and a transaction-per-test; how a migration
chain is built; why vector dimensions are fixed at migration time.

**Try it:** add a trivial column to `notes` (e.g. `is_pinned`), generate a migration with
`alembic revision --autogenerate -m "add is_pinned to notes"`, inspect it, and apply it.
Then roll it back with `alembic downgrade -1`.

---

## Study habits that work for this repo

- **Follow one request end-to-end** and write down every file it touches. Do it for
  `POST /notes` and for `POST /chat`.
- **Trace a test.** When a test passes, explain *which line of production code it proves*.
- **Change something small and predict the failure** before you run the tests.
- Keep the [GLOSSARY](GLOSSARY.md) nearby. If you cannot define a term in one sentence, it
  is worth a detour.

When you are ready to extend the project, go to
[`docs/REVIEW_ROADMAP.md`](REVIEW_ROADMAP.md).
