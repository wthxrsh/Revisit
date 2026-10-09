import pytest

from secondbrain.services.processing.chunker import TextChunker
from secondbrain.services.processing.pdf_extractor import PageText


def test_rejects_invalid_configuration():
    with pytest.raises(ValueError):
        TextChunker(chunk_size=100, chunk_overlap=100)

    with pytest.raises(ValueError):
        TextChunker(chunk_size=0, chunk_overlap=0)


def test_chunks_do_not_exceed_size_budget():
    pages = [PageText(page_number=1, text="word " * 500)]
    chunker = TextChunker(chunk_size=100, chunk_overlap=20)

    chunks = chunker.chunk_pages(pages)

    assert len(chunks) > 1
    for chunk in chunks:
        assert chunk.text
        assert len(chunk.text) <= 100 + 20


def test_chunks_are_ordered_and_indexed():
    pages = [PageText(page_number=1, text="alpha beta gamma " * 100)]
    chunker = TextChunker(chunk_size=80, chunk_overlap=10)

    chunks = chunker.chunk_pages(pages)

    assert [chunk.index for chunk in chunks] == list(range(len(chunks)))


def test_page_provenance_is_preserved():
    pages = [
        PageText(page_number=1, text="first page content " * 40),
        PageText(page_number=2, text="second page content " * 40),
    ]
    chunker = TextChunker(chunk_size=200, chunk_overlap=50)

    chunks = chunker.chunk_pages(pages)

    assert chunks[0].page_number == 1
    assert any(chunk.page_number == 2 for chunk in chunks)
    for chunk in chunks:
        assert chunk.page_end >= chunk.page_number


def test_empty_pages_return_no_chunks():
    chunker = TextChunker(chunk_size=100, chunk_overlap=10)

    assert chunker.chunk_pages([PageText(page_number=1, text="")]) == []
    assert chunker.chunk_pages([]) == []


def test_single_word_longer_than_chunk_size():
    pages = [PageText(page_number=1, text="a" * 500)]
    chunker = TextChunker(chunk_size=50, chunk_overlap=5)

    chunks = chunker.chunk_pages(pages)

    assert len(chunks) == 1
    assert chunks[0].text == "a" * 500
