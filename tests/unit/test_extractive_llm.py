from secondbrain.services.llm.base import LLMSource
from secondbrain.services.llm.extractive import ExtractiveAnswerProvider


def _sources(*texts: str) -> list[LLMSource]:
    return [
        LLMSource(index=i + 1, content=text, filename="doc.pdf", page_number=1)
        for i, text in enumerate(texts)
    ]


def test_returns_grounded_answer_with_citations():
    provider = ExtractiveAnswerProvider()

    answer = provider.generate(
        "What is retrieval augmented generation?",
        _sources(
            "Retrieval augmented generation combines search with a model.",
            "Unrelated content about gardening.",
        ),
    )

    assert answer.cited_indexes == [1]
    assert "retrieval" in answer.answer.lower()


def test_no_sources_returns_refusal():
    provider = ExtractiveAnswerProvider()

    answer = provider.generate("anything", [])

    assert answer.cited_indexes == []
    assert "could not find" in answer.answer.lower()


def test_no_overlap_returns_refusal():
    provider = ExtractiveAnswerProvider()

    answer = provider.generate(
        "quantum chromodynamics",
        _sources("The cat sat on the mat."),
    )

    assert answer.cited_indexes == []
    assert "could not find" in answer.answer.lower()


def test_does_not_cite_unused_sources():
    provider = ExtractiveAnswerProvider()

    answer = provider.generate(
        "chunking",
        _sources(
            "Chunking splits documents into passages.",
            "Bananas are yellow.",
        ),
    )

    assert answer.cited_indexes == [1]
