# Review Roadmap

You have a working, tested codebase. This document tells you **what is already solid**,
**what to review critically**, and **how to extend it** in a sensible order.

---

## 1. What is solid (and how it is verified)

| Area | Verified by |
| --- | --- |
| Ownership isolation for notes, documents, chunks, conversations | `tests/integration/test_*_api.py` cross-user tests |
| Auth (register/login, token validation) | `tests/integration/test_auth_api.py`, `tests/unit/test_jwt_service.py` |
| Password hashing (no plaintext) | `tests/unit/test_password_service.py`, `test_auth_api.py::test_only_password_hash_is_stored` |
| Safe file uploads (type/size/traversal/partial cleanup) | `tests/unit/test_file_storage.py`, `test_documents_api.py` |
| Chunking correctness (size, overlap, page provenance) | `tests/unit/test_chunker.py` |
| Embeddings (determinism, normalization, similarity ordering) | `tests/unit/test_hashing_embedding.py` |
| Grounded answers, refusal, citation isolation | `tests/integration/test_rag_api.py` |
| Migrations (fresh DB) | `alembic upgrade head` on an empty database |
| Error envelope | `test_health.py`, exception handler tests via API responses |

Run everything with:

```bash
pytest -q          # 97 tests
```

---

## 2. Code review checklist (do this yourself)

Go through the code and confirm each of the following. These are the questions a reviewer
would ask.

**Security**
- [ ] Is every user-owned query filtered by `user_id`? (grep repositories for `where(`.)
- [ ] Can an unauthenticated request reach any non-public route?
- [ ] Is any secret ever logged or returned? (Check `logging` calls and responses.)
- [ ] Can a malicious filename escape the storage directory? (See `_safe_filename` and
      `path_for`.)
- [ ] Are error messages free of internal details (tracebacks, SQL)?

**Correctness**
- [ ] Are chunk counts always consistent with embeddings? (`processing_service` checks.)
- [ ] Is reprocessing idempotent? (`replace_for_document` deletes then inserts.)
- [ ] Can two concurrent processing runs corrupt a document? (`try_mark_processing`.)
- [ ] Does retrieval respect `min_similarity` and `top_k`?

**Design**
- [ ] Does any service import SQLAlchemy or FastAPI types? (It should not.)
- [ ] Does any router contain business logic? (It should not.)
- [ ] Is configuration read anywhere other than `config.py`?

**Tests**
- [ ] Does each test assert behavior, not implementation details?
- [ ] Do integration tests clean up after themselves? (Transaction rollback.)
- [ ] Is there a test for each error path you added?

---

## 3. Prioritized improvements

### High value, low risk

1. **`min_similarity` default.** It is `0.0`, which means every question retrieves `top_k`
   chunks even for unrelated questions. With the lexical default the extractive provider
   still refuses, but with a real embedding model a small positive threshold (e.g. `0.2`)
   would make retrieval cleaner. *Try it and measure.*
2. **Upload deduplication.** The unique `storage_key` prevents overwriting, but the same
   PDF can be uploaded twice. A content hash column would let you detect duplicates.
3. **Note list does not paginate total counts.** Add a `count` endpoint or a total in a
   response envelope if the UI needs it.

### Medium value

4. **Background processing.** Move `DocumentProcessingService.process` behind a queue
   (RQ/Celery/Arq). The status machine is already in place. This removes the main
   limitation.
5. **Streaming/limits for very large PDFs.** Even with a worker, cap pages/characters.
6. **Structured JSON logging with request ids.** Currently logs are human-readable lines.
7. **Pagination envelope.** `limit`/`offset` with no total makes infinite scroll awkward.

### Larger

8. **OCR for scanned PDFs** (e.g. `ocrmypdf`/Tesseract) before extraction.
9. **Re-embedding migration tool.** A command that re-processes all documents when
   `EMBEDDING_DIM`/model changes.
10. **Account deletion** with cascade of documents, chunks, conversations, and stored
    files.

---

## 4. Extension exercises (learn by building)

Ordered roughly by difficulty. Each maps to a concrete idea in `DECISIONS.md`.

### Beginner

1. **Add a `GET /documents/{id}/chunks` endpoint** for debugging what was indexed.
   - Add a repository method, a service method, a schema, a route, and a test.
2. **Add a `tags` list to notes.** Requires: migration, ORM column (e.g. `ARRAY` or JSONB),
   domain field, schema field, and tests.
3. **Add `GET /notes/{id}` to return `404` vs a new `PinnedNoteResponse`.** Practice
   backwards-compatible API design.

### Intermediate

4. **Add a second embedding provider** (e.g. Cohere/Voyage) behind the existing interface
   and wire it in the factory. No service should change.
5. **Implement rate limiting** on `/auth/login` (slowapi or a small token bucket). Test the
   429 path.
6. **Add a `search_documents_by_similarity` helper** that returns document-level scores by
   aggregating chunk scores.

### Advanced

7. **Move processing to a worker.** Add a queue, a worker entry point that calls
   `DocumentProcessingService.process`, a new status transition, and tests using an
   in-memory queue. Verify the API returns `pending` immediately and the status flips to
   `completed`.
8. **Add a re-ranking step.** Retrieve top-20 by vector similarity, then re-rank with a
   cross-encoder (or the extractive overlap score) and keep the top-5.
9. **Evaluate retrieval.** Build a small labelled set (question → expected document/page)
   and measure recall@k for `hashing` vs `fastembed`. This is the honest way to decide
   whether to pay for a real embedding model.

---

## 5. How to approach a change (a repeatable method)

1. **Write the failing test first.** For a bug: reproduce it. For a feature: describe the
   expected behavior.
2. **Decide the layer.** Database change? Migration + ORM + repository. Business rule?
   Service. HTTP shape? Schema + router.
3. **Keep the layers clean.** If you feel tempted to import SQLAlchemy in a service, add a
   repository method instead.
4. **Enforce ownership in the query**, not only in the service.
5. **Run `pytest -q`.** Both unit and integration must stay green.
6. **Update the docs.** If you change behavior, `README.md` and the relevant `docs/*.md`
   are part of the change.

---

## 6. Where to start tomorrow

If you only do one thing: **read `services/rag_service.py` and
`repositories/postgres_chunk_repository.py::search` side by side, then experiment with
`RETRIEVAL_TOP_K` and `RETRIEVAL_MIN_SIMILARITY`.** That pair is the heart of the product,
and the fastest way to build genuine intuition for RAG is to watch retrieval change as you
turn those two knobs.
