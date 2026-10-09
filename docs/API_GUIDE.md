# API Guide

Base URL in development: `http://127.0.0.1:8000`.

All endpoints except `/health`, `/ready`, `/auth/register`, and `/auth/login` require a
JWT in the `Authorization` header:

```
Authorization: Bearer <access_token>
```

All error responses share the envelope:

```json
{ "error": "<code>", "message": "<human readable>", "details": "<optional>" }
```

Interactive docs are served at `/docs` (Swagger UI) and `/openapi.json`.

---

## Health

### `GET /health`
Liveness. Does not touch the database.

```bash
curl -s localhost:8000/health
# {"status":"ok"}
```

### `GET /ready`
Readiness. Checks the database and that the storage directory is writable. Returns `503`
if any check fails.

```bash
curl -s localhost:8000/ready
# {"status":"ready","checks":{"database":"ok","storage":"ok"}}
```

---

## Auth

### `POST /auth/register` → `201`
Body: `{ "email": string, "password": string }` (password 8–128 chars).

```bash
curl -s localhost:8000/auth/register \
  -H 'content-type: application/json' \
  -d '{"email":"me@example.com","password":"password123"}'
# {"id":1,"email":"me@example.com","created_at":"..."}
```

Errors: `409` if the email exists, `422` for invalid email or too-short password.

### `POST /auth/login` → `200`
Body: `{ "email": string, "password": string }`. Email is case-insensitive.

```bash
curl -s localhost:8000/auth/login \
  -H 'content-type: application/json' \
  -d '{"email":"me@example.com","password":"password123"}'
# {"access_token":"eyJ...","token_type":"bearer"}
```

Errors: `401` for unknown email or wrong password.

---

## Notes

### `POST /notes` → `201`
Body: `{ "title": string (1–255 chars), "content": string (non-empty) }`.

```bash
curl -s localhost:8000/notes \
  -H "authorization: Bearer $TOKEN" -H 'content-type: application/json' \
  -d '{"title":"Reading list","content":"Finish the RAG docs"}'
# {"id":1,"title":"Reading list","content":"Finish the RAG docs","created_at":"...","updated_at":"..."}
```

The `id` is **assigned by the database**; do not send one.

### `GET /notes` → `200`
Query parameters:

| Name | Default | Constraints |
| --- | --- | --- |
| `limit` | 20 | 1–100 |
| `offset` | 0 | ≥ 0 |
| `search` | — | 1–200 chars, matches title or content (case-insensitive) |

```bash
curl -s "localhost:8000/notes?search=rag&limit=10" -H "authorization: Bearer $TOKEN"
```

### `GET /notes/{note_id}` → `200` / `404`

### `PUT /notes/{note_id}` → `200` / `404`
Body: `{ "title": string, "content": string }` (full replacement).

### `DELETE /notes/{note_id}` → `200` / `404`
Returns `{ "message": "Note deleted successfully" }`.

> Another user's note id returns `404`, not `403` — the API never reveals that someone
> else's note exists.

---

## Documents

### `POST /documents` → `201`
`multipart/form-data` with a `file` field. Must be a PDF (`%PDF` magic bytes). The file is
stored, a row is created, and — with the default `PROCESS_ON_UPLOAD=true` — it is processed
**before the response returns**.

```bash
curl -s localhost:8000/documents \
  -H "authorization: Bearer $TOKEN" \
  -F 'file=@my-document.pdf'
# {
#   "id":1,"original_filename":"my-document.pdf","file_size":12345,
#   "mime_type":"application/pdf","status":"completed","page_count":2,
#   "error_message":null,"created_at":"...","updated_at":"...","processed_at":"..."
# }
```

`status` is one of `pending`, `processing`, `completed`, `failed`. A document that cannot
be indexed (empty/encrypted/corrupt) still returns `201` but with `status:"failed"` and an
`error_message`.

Errors: `415` (not a PDF), `413` (too large), `401` (unauthenticated).

### `GET /documents` → `200`
Query: `limit` (1–100, default 20), `offset` (≥ 0). Owner-scoped.

### `GET /documents/{document_id}` → `200` / `404`

### `GET /documents/{document_id}/status` → `200` / `404`
Returns the same shape as `GET /documents/{id}` (a convenience alias for polling).

### `POST /documents/{document_id}/process` → `200` / `404`
Re-runs extraction/chunking/embedding. Idempotent: existing chunks are replaced atomically.
Returns `409` if the document is already being processed.

### `DELETE /documents/{document_id}` → `200` / `404`
Removes the stored file and the row (chunks cascade).

---

## Chat (RAG)

### `POST /chat` → `200`
Body:

```json
{
  "question": "What is retrieval augmented generation?",
  "conversation_id": null,
  "top_k": null,
  "document_ids": null
}
```

- `question` — required, 1–4000 chars.
- `conversation_id` — omit to start a new conversation; pass an id to continue one.
- `top_k` — optional override, 1–20.
- `document_ids` — optional list to restrict retrieval to specific documents. Ownership is
  still enforced, so ids you do not own yield no results.

```bash
curl -s localhost:8000/chat \
  -H "authorization: Bearer $TOKEN" -H 'content-type: application/json' \
  -d '{"question":"What is retrieval augmented generation?"}'
# {
#   "conversation_id":1,"message_id":2,
#   "answer":"Based on your documents: Retrieval augmented generation combines ...",
#   "grounded":true,
#   "citations":[{"document_id":1,"filename":"sample.pdf","page_number":2,
#                 "chunk_id":3,"chunk_index":2,"snippet":"Retrieval augmented ..."}]
# }
```

- `grounded:false` means no retrieved chunk was cited; `citations` is empty and the answer
  is a fixed "I could not find…" message.
- If the LLM/embedding provider fails, the API returns `503` (`provider_error`).

### `GET /conversations` → `200`
Query: `limit` (1–100, default 20), `offset` (≥ 0). Owner-scoped.

### `GET /conversations/{conversation_id}` → `200` / `404`
Returns `{ "conversation": {...}, "messages": [...] }`, oldest message first.

### `DELETE /conversations/{conversation_id}` → `200` / `404`
Deletes the conversation and its messages.

---

## Status codes at a glance

| Code | Meaning here |
| --- | --- |
| 200 | Success (reads, updates, deletes, login, chat) |
| 201 | Resource created (register, note, document) |
| 400 | Domain validation failed (e.g. whitespace-only title) |
| 401 | Missing/invalid token, or bad login credentials |
| 404 | Not found **or** not owned by you |
| 409 | Conflict (duplicate email, already processing) |
| 413 | Payload/file too large |
| 415 | Unsupported upload type |
| 422 | Request schema validation failed (Pydantic) |
| 500 | Unexpected server error |
| 503 | Provider unavailable, or not ready |

---

## Using the OpenAPI schema

FastAPI generates a complete OpenAPI document from the code:

- Swagger UI: `/docs`
- ReDoc: `/redoc`
- Raw schema: `/openapi.json`

This is generated automatically from `api/schemas.py` and the router signatures, so it
never drifts from the implementation.
