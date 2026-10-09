# RAG Explained

**RAG** stands for **Retrieval-Augmented Generation**. Instead of asking a language model
to answer from its own memory (which may be wrong or out of date), you first **retrieve**
relevant passages from your own documents, then ask the model to answer **using only those
passages**. The retrieved text "augments" the model's prompt.

This document explains the concepts and then the exact algorithms SecondBrain uses. The
code is in `src/secondbrain/services/rag_service.py`, `services/processing/`, and
`services/embedding/`, `services/llm/`.

---

## 1. The pipeline

```
                 upload time (offline)                 query time (online)
─────────────────────────────────────────────  ─────────────────────────────
PDF ─▶ text per page ─▶ chunks ─▶ embeddings   question ─▶ embedding
                                      │                          │
                                      ▼                          ▼
                                store vectors  ◀── cosine similarity search ──┐
                                      │                                     │
                                      └────────────▶ top-k chunks ──────────┘
                                                          │
                                                          ▼
                                             build a bounded context string
                                                          │
                                                          ▼
                                             LLM (or extractive) answers
                                                          │
                                                          ▼
                                          answer + citations → user
```

The two halves share one thing: **the same embedding model** must turn both documents and
questions into vectors, or the comparison is meaningless.

---

## 2. Chunking

You cannot embed an entire PDF as one vector: retrieval would be too coarse and would not
fit the model's context window. So the text is split into **chunks**.

`services/processing/chunker.py` implements a **word-boundary sliding window**:

- Pages are concatenated (with page markers) so chunks can span page boundaries, while
  each chunk records the `page_number` and `page_end` it covers.
- A chunk grows word by word until adding the next word would exceed `CHUNK_SIZE`
  characters.
- The next chunk starts so that it **overlaps** the previous one by about
  `CHUNK_OVERLAP` characters. Overlap preserves meaning that would otherwise be split
  across a boundary.
- If a single "word" is longer than `CHUNK_SIZE`, it becomes its own chunk (we never split
  mid-word).

Configuration: `CHUNK_SIZE` (default 1000), `CHUNK_OVERLAP` (default 200). The settings
validator refuses to start if overlap ≥ size.

**Why page provenance matters:** it turns a retrieved chunk into a citation like
"sample.pdf, page 2".

---

## 3. Embeddings

An **embedding** maps text to a fixed-length list of floats (a **vector**) such that
similar meanings land near each other. "Near" is measured with **cosine similarity**, which
compares the *angle* between two vectors (ignoring length).

### The default provider: lexical feature hashing

`services/embedding/hashing.py` is deliberately simple and **not** a neural network:

1. Lowercase and tokenize into alphanumeric words.
2. For each token, hash it (`blake2b`) into an index in `[0, dimension)` and a sign.
3. Accumulate `+1`/`-1` into that position.
4. Normalize the vector to unit length.

This is a **bag-of-words feature hash**: texts that share words get similar vectors; texts
that share only *meaning* do not. Its advantages:

- fully deterministic and offline,
- no model download, no API key, tiny and fast,
- perfect for tests and for a first runnable version.

Its honest limitation: it does **not** understand synonyms. "car" and "automobile" are
unrelated to it. That is why the docstring calls it lexical, not semantic.

### Real semantic providers

- `embedding/fastembed_provider.py` — `BAAI/bge-small-en-v1.5`, 384 dimensions, runs
  locally. Install with `pip install -e ".[embeddings]"` and set
  `EMBEDDING_PROVIDER=fastembed`.
- `embedding/openai_provider.py` — remote embeddings; set `OPENAI_API_KEY` and
  `EMBEDDING_PROVIDER=openai` (also set `EMBEDDING_DIM` to the model's dimension).

All providers implement the same interface (`embedding/base.py`):
`embed_query(text) -> vector` and `embed_documents(texts) -> [vector]`.

> **Dimension coupling.** The `chunks.embedding` column is `vector(EMBEDDING_DIM)` and the
> HNSW index is built for that size. Switching to a model with a different dimension
> requires a migration and re-embedding all chunks (`POST /documents/{id}/process`).

---

## 4. Vector search in PostgreSQL

SecondBrain does not run a separate vector database. It uses the **pgvector** extension, so
chunks and their vectors live in the same transactions and the same `user_id` ownership
rules as everything else.

The query is in `repositories/postgres_chunk_repository.py::search`:

```sql
SELECT chunks.*, documents.original_filename,
       1 - (chunks.embedding <=> :query) AS score
FROM chunks
JOIN documents ON chunks.document_id = documents.id
WHERE chunks.user_id = :user_id
  AND chunks.embedding IS NOT NULL
  [AND chunks.document_id IN (:document_ids)]
  [AND 1 - (chunks.embedding <=> :query) >= :min_similarity]
ORDER BY chunks.embedding <=> :query     -- cosine distance, ascending
LIMIT :top_k;
```

- `<=>` is pgvector's **cosine distance** (`1 - cosine_similarity`).
- Ordering by distance ascending = most similar first.
- `min_similarity` (default `0.0`) drops weak matches. This is what lets the assistant say
  "I don't know" instead of answering from noise.
- An **HNSW index** (`ix_chunks_embedding_hnsw`) makes nearest-neighbour search fast as the
  table grows.

Critically, `WHERE chunks.user_id = :user_id` is always present, so retrieval can never
cross user boundaries.

---

## 5. Building the context

`RagService._build_context` turns the top-k `ScoredChunk`s into numbered sources:

```
[1] (sample.pdf, page 2)
Retrieval augmented generation combines search with a language model.

[2] (sample.pdf, page 1)
SecondBrain is a personal knowledge management system.
```

It stops adding sources once `RAG_MAX_CONTEXT_CHARS` (default 6000) would be exceeded, so
the prompt stays bounded. Each source remembers which chunk/document it came from, so
citations can be reconstructed later.

---

## 6. Answering

Two providers implement `llm/base.py`:

### Extractive (default)

`services/llm/extractive.py` does **not** generate prose:

1. Extract keywords from the question (dropping stopwords).
2. Split every source into sentences.
3. Score each sentence by how many keywords it shares with the question.
4. Return the top `max_sentences` (default 3), prefixed with "Based on your documents: ",
   and report the source indexes they came from.
5. If no sentence overlaps the question, return the fixed "I could not find…" answer with
   no citations.

It is deterministic, offline, and cannot hallucinate — it only ever quotes retrieved text.

### OpenAI

`services/llm/openai_provider.py` sends a system prompt that instructs the model to answer
**only** from the numbered context, to cite sources as `[n]`, and to refuse when the answer
is not present. It then parses the cited indexes out of the response.

Both providers return `LLMAnswer(answer, cited_indexes)`.

---

## 7. Grounding and citations

Back in `RagService.ask`:

- Each cited index is looked up in the `source_map` and converted to a `Citation`
  (`document_id`, `filename`, `page_number`, `chunk_id`, `chunk_index`, `snippet`).
- `grounded = bool(citations)`. In other words, **grounded means the answer cites at least
  one chunk that was actually retrieved for this question.** This is a real, checkable
  signal, not a claim by the model.
- If no sources were retrieved, or the provider produced no citations, the answer is the
  fixed refusal and `grounded=false`.

The assistant message (answer + citations as JSON) and the user message are both persisted,
so conversations can be replayed via `GET /conversations/{id}`.

---

## 8. Failure modes and limitations (be honest about them)

| Situation | What happens |
| --- | --- |
| No documents / no matching chunks | Fixed refusal, `grounded=false` |
| Weak lexical match, default provider | Irrelevant chunks may be retrieved; the extractive provider then refuses because no sentence overlaps |
| Encrypted / empty / corrupt PDF | Document `status=failed` with `error_message` |
| Embedding or LLM provider error | `503 provider_error` |
| Synonyms with the default provider | Missed (lexical, not semantic) — use `fastembed`/`openai` |
| Big PDF | Blocks the request (synchronous processing) |
| Scanned PDF (images) | No extractable text → treated as empty; no OCR |

---

## 9. Where to look in the code

| Concept | File |
| --- | --- |
| Extract text per page | `services/processing/pdf_extractor.py` |
| Split into overlapping chunks | `services/processing/chunker.py` |
| Run the pipeline | `services/processing_service.py` |
| Embedding interface | `services/embedding/base.py` |
| Default embedding algorithm | `services/embedding/hashing.py` |
| Vector similarity query | `repositories/postgres_chunk_repository.py::search` |
| RAG orchestration | `services/rag_service.py` |
| Extractive answering | `services/llm/extractive.py` |
| OpenAI answering | `services/llm/openai_provider.py` |
| End-to-end tests | `tests/integration/test_rag_api.py` |
