import re

from secondbrain.services.llm.base import LLMAnswer, LLMProvider, LLMSource

_WORD = re.compile(r"[a-z0-9]+")
_SENTENCE = re.compile(r"(?<=[.!?])\s+")

_STOPWORDS = {
    "the", "a", "an", "and", "or", "but", "if", "then", "than", "that",
    "this", "these", "those", "is", "are", "was", "were", "be", "been",
    "being", "to", "of", "in", "on", "at", "by", "for", "with", "about",
    "as", "into", "from", "it", "its", "you", "your", "i", "we", "they",
    "he", "she", "do", "does", "did", "can", "could", "should", "would",
    "what", "which", "who", "whom", "how", "when", "where", "why", "not",
    "no", "yes", "there", "their", "them", "his", "her", "our", "my",
    "me", "us", "also", "very",
}


class ExtractiveAnswerProvider(LLMProvider):
    """Deterministic, offline answer provider.

    Selects the sentences from retrieved passages that best overlap with the
    question and returns them with the source indexes they came from. It does not
    generate new prose; it is a grounded fallback for local development and tests.
    """

    def __init__(self, max_sentences: int = 3):
        self.max_sentences = max_sentences

    @property
    def name(self) -> str:
        return "extractive"

    def generate(
        self, question: str, sources: list[LLMSource]
    ) -> LLMAnswer:
        if not sources:
            return self._no_answer()

        keywords = self._keywords(question)
        scored_sentences: list[tuple[int, int, str]] = []

        for source in sources:
            for sentence in self._sentences(source.content):
                score = self._overlap(sentence, keywords)
                if score > 0:
                    scored_sentences.append((score, source.index, sentence))

        if not scored_sentences:
            return self._no_answer()

        scored_sentences.sort(key=lambda item: item[0], reverse=True)
        selected = scored_sentences[: self.max_sentences]

        parts = [sentence for _, _, sentence in selected]
        cited = []
        for _, source_index, _ in selected:
            if source_index not in cited:
                cited.append(source_index)

        answer = "Based on your documents: " + " ".join(parts)

        return LLMAnswer(answer=answer, cited_indexes=sorted(cited))

    @staticmethod
    def _no_answer() -> LLMAnswer:
        return LLMAnswer(
            answer=(
                "I could not find sufficient information in your knowledge "
                "base to answer that question."
            ),
            cited_indexes=[],
        )

    @staticmethod
    def _keywords(question: str) -> set[str]:
        return {
            word
            for word in _WORD.findall(question.lower())
            if word not in _STOPWORDS and len(word) > 1
        }

    @staticmethod
    def _sentences(text: str) -> list[str]:
        return [
            sentence.strip()
            for sentence in _SENTENCE.split(text)
            if sentence.strip()
        ]

    @staticmethod
    def _overlap(sentence: str, keywords: set[str]) -> int:
        words = set(_WORD.findall(sentence.lower()))
        return len(words & keywords)
