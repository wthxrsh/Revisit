import math

from secondbrain.services.embedding.hashing import HashingEmbeddingProvider


def test_dimension_is_respected():
    provider = HashingEmbeddingProvider(dimension=64)

    vector = provider.embed_query("hello world")

    assert len(vector) == 64


def test_embeddings_are_deterministic():
    provider = HashingEmbeddingProvider(dimension=128)

    first = provider.embed_query("SecondBrain knowledge base")
    second = provider.embed_query("SecondBrain knowledge base")

    assert first == second


def test_vectors_are_normalized():
    provider = HashingEmbeddingProvider(dimension=128)

    vector = provider.embed_query("normalize this vector")

    norm = math.sqrt(sum(value * value for value in vector))

    assert abs(norm - 1.0) < 1e-9


def test_empty_text_produces_zero_vector():
    provider = HashingEmbeddingProvider(dimension=32)

    vector = provider.embed_query("")

    assert vector == [0.0] * 32


def test_batch_embedding_matches_single():
    provider = HashingEmbeddingProvider(dimension=64)

    batch = provider.embed_documents(["alpha", "beta"])

    assert batch[0] == provider.embed_query("alpha")
    assert batch[1] == provider.embed_query("beta")


def test_similar_text_is_closer_than_unrelated_text():
    provider = HashingEmbeddingProvider(dimension=256)

    query = provider.embed_query("python programming language")
    related = provider.embed_query("python language for programming")
    unrelated = provider.embed_query("banana apple orange fruit")

    def similarity(a, b):
        return sum(x * y for x, y in zip(a, b))

    assert similarity(query, related) > similarity(query, unrelated)
