# Glossary

Plain-language definitions of the terms used in this project. Kept deliberately short.

## Web / API

**FastAPI** — the Python web framework used for the HTTP API. It turns typed Python
functions into routes and generates OpenAPI docs automatically.

**Router** — a group of related endpoints (`api/routers/*.py`).

**ASGI app** — the object a server runs. Here it is `secondbrain.main:app`.

**Dependency injection** — FastAPI's mechanism for providing objects a route needs
(`Depends(...)`), e.g. a database session or a service. It defines how things are built per
request.

**Pydantic** — the library that validates request/response data. Field constraints like
`min_length` produce `422` errors.

**Schema** — a Pydantic class describing a request or response shape (`api/schemas.py`).

**Middleware** — code that runs around every request (here: CORS and request-size
enforcement).

**OpenAPI / Swagger** — the machine-readable description of the API, served at
`/openapi.json`; the interactive UI is `/docs`.

**Error envelope** — the consistent error JSON: `{"error", "message", "details?"}`.

## Auth / security

**Authentication** — proving *who* you are (JWT).

**Authorization** — deciding *what* you may do (owner scoping).

**JWT (JSON Web Token)** — a signed token carrying claims. Here it carries the user id
(`sub`) and expiry (`exp`), signed with `JWT_SECRET_KEY`.

**Bearer token** — a token sent as `Authorization: Bearer <token>`.

**Hashing (passwords)** — a one-way transformation so the plaintext password is never
stored. Argon2 via `pwdlib` is used here.

**Ownership / owner scoping** — every query filters by `user_id`, so users can only see
their own data.

**Path traversal** — an attack using `../` in a filename to escape a directory. Prevented by
sanitizing names and generating storage keys.

**Magic bytes** — the first bytes of a file that identify its type; `%PDF` identifies a PDF.

## Data / database

**PostgreSQL** — the relational database.

**pgvector** — a PostgreSQL extension adding a `vector` column type and vector operators
(`<=>` = cosine distance).

**SQLAlchemy** — the Python ORM used to define tables and run queries.

**ORM model** — a Python class mapped to a table (`database/*_models.py`).

**Domain model** — a plain dataclass representing a concept, independent of storage
(`models/*.py`).

**Repository** — the only layer that runs queries; translates between ORM rows and domain
objects.

**Migration** — a versioned, reversible schema change (Alembic). `alembic upgrade head`
applies all pending ones.

**Alembic** — the migration tool for SQLAlchemy.

**Session** — a unit of work with the database, opened per request.

**Transaction** — an all-or-nothing group of statements; the test suite rolls one back per
test for isolation.

**Cascade** — automatic deletion of dependent rows; deleting a document deletes its chunks.

**`try_mark_processing`** — a conditional `UPDATE` that flips a document to `processing`
only if it is not already being processed (a concurrency guard).

**HNSW index** — a graph-based index that makes approximate nearest-neighbour search fast.

## RAG / AI

**RAG (Retrieval-Augmented Generation)** — retrieve relevant passages from your documents,
then answer using them.

**Embedding** — a fixed-length list of floats representing text, positioned so similar
meanings are close together.

**Dimension** — the length of an embedding vector (here 384).

**Vector** — the embedding array.

**Cosine similarity / distance** — a measure of the angle between two vectors. Similarity
`1 - distance`; distance `0` means identical direction.

**Chunk** — a slice of a document small enough to embed and retrieve.

**Chunking** — splitting text into chunks, here a word-boundary sliding window with overlap.

**Overlap** — the characters shared between consecutive chunks so meaning is not lost at
boundaries.

**Top-k** — retrieve the `k` most similar chunks.

**`min_similarity`** — the score below which a chunk is discarded; this is what enables
refusal.

**Context window** — the bounded amount of retrieved text given to the model
(`RAG_MAX_CONTEXT_CHARS`).

**LLM (Large Language Model)** — a model that can generate text.

**Provider** — a pluggable implementation behind an interface (embeddings or LLM).

**Extractive answer** — an answer assembled by selecting sentences from the sources (no new
text). The default provider does this.

**Grounded** — an answer that cites at least one retrieved chunk. `grounded=false` means the
assistant refused.

**Citation** — the document, page, and chunk an answer came from.

**Hallucination** — text a model invents that is not supported by the sources. The
extractive default cannot hallucinate; the OpenAI provider is instructed not to and its
citations are still checked against retrieved chunks.

**Stopword** — a common word (the, is, of) filtered out when scoring keyword overlap.

**Feature hashing** — mapping tokens to vector positions via a hash; the technique behind
the default embedding provider.

**Lexical vs. semantic** — lexical matches words; semantic matches meaning. The default
provider is lexical; `fastembed`/`openai` are semantic.

**OCR (Optical Character Recognition)** — extracting text from images/scans. Not implemented
here, so scanned PDFs are treated as empty.

## Operations

**Docker Compose** — runs PostgreSQL + pgvector locally (`docker compose up -d`).

**`.env`** — local environment variables (never committed). `.env.example` documents them.

**CI (continuous integration)** — the GitHub Actions workflow that runs migrations and tests
on every push/PR.

**Readiness vs. liveness** — `/ready` checks dependencies (database, storage); `/health` just
says the process is up.
