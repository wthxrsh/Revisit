from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class LLMSource:
    index: int
    content: str
    filename: str
    page_number: int | None


@dataclass
class LLMAnswer:
    answer: str
    cited_indexes: list[int]


class LLMProvider(ABC):

    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @abstractmethod
    def generate(
        self, question: str, sources: list[LLMSource]
    ) -> LLMAnswer:
        pass
