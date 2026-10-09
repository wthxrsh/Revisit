# Revisit

Revisit (formerly SecondBrain) is a small but complete **personal knowledge base** built
with FastAPI, PostgreSQL, PostgreSQL + pgvector, and a **Next.js** front end.

It lets a user:

1. Register and log in (JWT).
2. Store private notes.
3. Upload PDF documents.
4. Have each PDF extracted, split into chunks, and embedded into vectors.
5. Ask questions and get answers **grounded in their own documents**, with citations.

Every resource is **owner-scoped**: a user can only ever read, update, or delete their
own notes, documents, chunks, and conversations. This is enforced in the database
queries themselves, not only in the API layer.

The web client lives in [`frontend/`](frontend/README.md) — a minimal, interactive
Next.js + TypeScript + Tailwind UI with subtle motion (`motion`).

> This project is intentionally built as a **learning codebase**. The code favors clear
> layering over cleverness, and the `docs/` folder explains every concept. If you are new
> to FastAPI / SQLAlchemy / RAG, start with
> [`docs/LEARNING_GUIDE.md`](docs/LEARNING_GUIDE.md).

---

## Quickstart

### 1. Start PostgreSQL (with pgvector)

```bash
docker compose up -d
```

The compose file uses the `pgvector/pgvector:pg17` image (PostgreSQL 17 + the
`pgvector` extension) and exposes port **5435**.

### 2. Create a virtual environment and install

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

### 3. Configure the environment

```bash
cp .env.example .env
# edit .env and set a real JWT_SECRET_KEY (at least 32 characters)
```

### 4. Apply migrations

```bash
alembic upgrade head
```

This creates the tables **and** the `vector` extension and the HNSW vector index.

### 5. Run the API

```bash
uvicorn secondbrain.main:app --reload
```

Open <http://127.0.0.1:8000/docs> for the interactive API documentation.

### 6. Try it

```bash
# register
curl -s localhost:8000/auth/register \
  -H 'content-type: application/json' \
  -d '{"email":"me@example.com","password":"password123"}'

# log in and capture the token
TOKEN=$(curl -s localhost:8000/auth/login \
  -H 'content-type: application/json' \
  -d '{"email":"me@example.com","password":"password123"}' | python -c 'import sys,json;print(json.load(sys.stdin)["access_token"])')

# create a note
curl -s localhost:8000/notes \
  -H "authorization: Bearer $TOKEN" -H 'content-type: application/json' \
  -d '{"title":"First note","content":"Hello world"}'

# upload a PDF
curl -s localhost:8000/documents \
  -H "authorization: Bearer $TOKEN" \
  -F 'file=@my-document.pdf'

# ask a question
curl -s localhost:8000/chat \
  -H "authorization: Bearer $TOKEN" -H 'content-type: application/json' \
  -d '{"question":"What is this document about?"}'
```

See [`docs/API_GUIDE.md`](docs/API_GUIDE.md) for the full endpoint reference.

---

## Frontend (Revisit UI)

A minimal Next.js + TypeScript + Tailwind client with subtle motion lives in
[`frontend/`](frontend/).

```bash
cd frontend
npm install
npm run dev          # http://localhost:3000
```

It talks to the API at `NEXT_PUBLIC_API_URL` (default `http://127.0.0.1:8000`,
configurable in `frontend/.env.local`). For the browser to call the API, set an allowed
origin in the backend `.env`:

```bash
CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
```

and restart the backend. See [`frontend/README.md`](frontend/README.md) for details.

---

## How it works (30-second version)

```
Client ──HTTP──▶ FastAPI router ──▶ Service ──▶ Repository ──▶ PostgreSQL (+ pgvector)
                       │                 │
                       │                 └──▶ Embedding provider / LLM provider
                       │
                       └── JWT auth + owner checks on every request
```

- **Routers** validate input and shape output (`api/`).
- **Services** hold business rules and orchestration (`services/`).
- **Repositories** are the only code that talks to the database (`repositories/`).
- **Domain models** are plain dataclasses (`models/`); **database models** are SQLAlchemy
  ORM classes (`database/`).
- **Embeddings and LLM** are behind small interfaces with pluggable providers.

Read [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) for the full picture.

---

## Providers (embeddings and LLM)

Both are pluggable and default to **offline, deterministic** implementations so the app
and its tests run with no network access and no API keys.

| Provider | `EMBEDDING_PROVIDER` | Notes |
| --- | --- | --- |
| Hashing (default) | `hashing` | Deterministic lexical feature-hashing vector. Fast, offline, **not** neural/semantic. |
| fastembed | `fastembed` | Real local neural embeddings (`BAAI/bge-small-en-v1.5`, 384-dim). Requires `pip install -e ".[embeddings]"`. |
| OpenAI | `openai` | Remote embeddings. Requires `OPENAI_API_KEY`. |

| Provider | `LLM_PROVIDER` | Notes |
| --- | --- | --- |
| Extractive (default) | `extractive` | Selects the best-matching sentences from retrieved passages and cites them. Deterministic, offline, not generative. |
| OpenAI | `openai` | Generates prose from the retrieved context. Requires `OPENAI_API_KEY`. |
| Groq | `groq` | Generates prose via Groq's OpenAI-compatible API. Requires `GROQ_API_KEY` and `LLM_MODEL` (e.g. `openai/gpt-oss-120b`). |

The default configuration gives you a working, fully offline RAG pipeline. Swap providers
in `.env` to see the same pipeline with real semantic search and real generation.

### Using Groq

```bash
LLM_PROVIDER=groq
LLM_MODEL=openai/gpt-oss-120b
GROQ_API_KEY=your-groq-key
# GROQ_BASE_URL=https://api.groq.com/openai/v1   # optional override
```

Groq does not provide embeddings, so keep `EMBEDDING_PROVIDER=hashing` for offline use or
switch to `fastembed` for real local semantic search. `LLM_MODEL` must be a model id that
your Groq account can use; list the available ones with:

```bash
curl https://api.groq.com/openai/v1/models -H "Authorization: Bearer $GROQ_API_KEY"
```

---

## Testing

```bash
pytest              # everything
pytest tests/unit   # fast, no database
pytest tests/integration   # requires PostgreSQL
```

Integration tests use an **isolated** database (`POSTGRES_TEST_DB`, default
`secondbrain_test`) that is created on demand. They never touch your development data.

---

## Documentation

| Document | What it covers |
| --- | --- |
| [docs/LEARNING_GUIDE.md](docs/LEARNING_GUIDE.md) | A guided path to read and understand the codebase. |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | Layers, request lifecycle, data model, security. |
| [docs/CODEBASE_TOUR.md](docs/CODEBASE_TOUR.md) | A file-by-file walk-through. |
| [docs/API_GUIDE.md](docs/API_GUIDE.md) | Every endpoint with examples. |
| [docs/RAG_EXPLAINED.md](docs/RAG_EXPLAINED.md) | Chunking, embeddings, retrieval, prompting, citations. |
| [docs/DECISIONS.md](docs/DECISIONS.md) | Why the design is the way it is (ADR-style). |
| [docs/REVIEW_ROADMAP.md](docs/REVIEW_ROADMAP.md) | What to review next and how to extend the project. |
| [docs/GLOSSARY.md](docs/GLOSSARY.md) | Plain-language definitions of the jargon. |
| [docs/IMPLEMENTATION_PLAN.md](docs/IMPLEMENTATION_PLAN.md) | The plan used to build the project and its limitations. |

---

## Known limitations

- Document processing is **synchronous**; large PDFs block the request. A background
  worker is the natural next step.
- The default embedding provider is **lexical, not semantic** (by design, for offline use).
- The default LLM provider **does not generate**; it extracts. Use `groq` or `openai` for prose.
- Vector dimensions are fixed at migration time (`EMBEDDING_DIM`), so switching embedding
  models with a different size requires a migration and a reindex.
- No OCR: scanned/image-only PDFs have no extractable text and are reported as empty.
- No account-deletion flow.

See [`docs/IMPLEMENTATION_PLAN.md`](docs/IMPLEMENTATION_PLAN.md#known-limitations) for the
complete list.
