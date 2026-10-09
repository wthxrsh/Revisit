import re
from bisect import bisect_right
from dataclasses import dataclass

from secondbrain.services.processing.pdf_extractor import PageText

_WORD = re.compile(r"\S+")
_PAGE_SEPARATOR = "\n\n"


@dataclass
class TextChunk:
    index: int
    text: str
    page_number: int | None
    page_end: int | None


class TextChunker:

    def __init__(self, chunk_size: int, chunk_overlap: int):
        if chunk_size <= 0:
            raise ValueError("chunk_size must be positive")

        if chunk_overlap < 0:
            raise ValueError("chunk_overlap cannot be negative")

        if chunk_overlap >= chunk_size:
            raise ValueError("chunk_overlap must be smaller than chunk_size")

        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def chunk_pages(self, pages: list[PageText]) -> list[TextChunk]:
        combined, starts, page_numbers = self._combine(pages)

        if not combined.strip():
            return []

        words = [(match.start(), match.end()) for match in _WORD.finditer(combined)]
        if not words:
            return []

        chunks: list[TextChunk] = []
        index = 0
        start_word = 0
        total_words = len(words)

        while start_word < total_words:
            end_word = start_word
            start_char = words[start_word][0]

            while (
                end_word < total_words
                and words[end_word][1] - start_char < self.chunk_size
            ):
                end_word += 1

            if end_word == start_word:
                end_word = start_word + 1

            end_char = words[end_word - 1][1]
            text = combined[start_char:end_char].strip()

            if text:
                chunks.append(
                    TextChunk(
                        index=index,
                        text=text,
                        page_number=self._page_at(starts, page_numbers, start_char),
                        page_end=self._page_at(
                            starts, page_numbers, end_char - 1
                        ),
                    )
                )
                index += 1

            if end_word >= total_words:
                break

            next_word = start_word + 1
            while (
                next_word < end_word
                and end_char - words[next_word][0] > self.chunk_overlap
            ):
                next_word += 1

            start_word = next_word

        return chunks

    @staticmethod
    def _combine(
        pages: list[PageText],
    ) -> tuple[str, list[int], list[int]]:
        pieces: list[str] = []
        starts: list[int] = []
        page_numbers: list[int] = []
        offset = 0

        for page in pages:
            if not page.text:
                continue

            pieces.append(page.text)
            starts.append(offset)
            page_numbers.append(page.page_number)
            offset += len(page.text)

            pieces.append(_PAGE_SEPARATOR)
            offset += len(_PAGE_SEPARATOR)

        return "".join(pieces), starts, page_numbers

    @staticmethod
    def _page_at(
        starts: list[int], page_numbers: list[int], char_position: int
    ) -> int | None:
        if not starts:
            return None

        index = bisect_right(starts, char_position) - 1
        if index < 0:
            index = 0

        return page_numbers[index]
