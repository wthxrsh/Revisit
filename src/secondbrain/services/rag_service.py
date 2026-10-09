import logging
from dataclasses import dataclass

from secondbrain.exceptions import ValidationError
from secondbrain.models.chunk import ScoredChunk
from secondbrain.models.conversation import Citation, Conversation, Message
from secondbrain.repositories.chunk_repository import ChunkRepository
from secondbrain.repositories.conversation_repository import (
    ConversationRepository,
)
from secondbrain.services.embedding.base import EmbeddingProvider
from secondbrain.services.llm.base import LLMProvider, LLMSource

logger = logging.getLogger(__name__)

NO_ANSWER_TEXT = (
    "I could not find sufficient information in your knowledge base to "
    "answer that question."
)
SNIPPET_LENGTH = 240
MAX_CONVERSATION_TITLE_LENGTH = 255


@dataclass
class RagAnswer:
    conversation_id: int
    message_id: int
    answer: str
    citations: list[Citation]
    grounded: bool


class RagService:

    def __init__(
        self,
        chunk_repository: ChunkRepository,
        conversation_repository: ConversationRepository,
        embedding_provider: EmbeddingProvider,
        llm_provider: LLMProvider,
        top_k: int = 5,
        min_similarity: float = 0.0,
        max_context_chars: int = 6000,
    ):
        self.chunk_repository = chunk_repository
        self.conversation_repository = conversation_repository
        self.embedding_provider = embedding_provider
        self.llm_provider = llm_provider
        self.top_k = top_k
        self.min_similarity = min_similarity
        self.max_context_chars = max_context_chars

    def ask(
        self,
        user_id: int,
        question: str,
        conversation_id: int | None = None,
        top_k: int | None = None,
        document_ids: list[int] | None = None,
    ) -> RagAnswer:
        question = (question or "").strip()
        if not question:
            raise ValidationError("Question cannot be empty")

        conversation = self._resolve_conversation(
            user_id, conversation_id, question
        )

        self.conversation_repository.add_message(
            conversation.id,
            Message(role="user", content=question),
        )

        query_embedding = self.embedding_provider.embed_query(question)

        scored_chunks = self.chunk_repository.search(
            user_id=user_id,
            query_embedding=query_embedding,
            top_k=top_k or self.top_k,
            min_similarity=self.min_similarity,
            document_ids=document_ids,
        )

        sources, source_map = self._build_context(scored_chunks)

        if not sources:
            return self._store_answer(
                conversation.id, NO_ANSWER_TEXT, [], grounded=False
            )

        llm_answer = self.llm_provider.generate(question, sources)

        citations = [
            self._to_citation(source_map[index])
            for index in llm_answer.cited_indexes
            if index in source_map
        ]

        return self._store_answer(
            conversation.id,
            llm_answer.answer,
            citations,
            grounded=bool(citations),
        )

    def _resolve_conversation(
        self, user_id: int, conversation_id: int | None, question: str
    ) -> Conversation:
        if conversation_id is not None:
            conversation = self.conversation_repository.get_by_id(
                conversation_id, user_id
            )
            if conversation is None:
                raise ValidationError(
                    f"Conversation with id {conversation_id} not found"
                )
            return conversation

        return self.conversation_repository.create(
            Conversation(
                user_id=user_id,
                title=question[:MAX_CONVERSATION_TITLE_LENGTH],
            )
        )

    def _build_context(
        self, scored_chunks: list[ScoredChunk]
    ) -> tuple[list[LLMSource], dict[int, ScoredChunk]]:
        sources: list[LLMSource] = []
        source_map: dict[int, ScoredChunk] = {}
        used_chars = 0

        for scored in scored_chunks:
            content = scored.chunk.content
            if sources and used_chars + len(content) > self.max_context_chars:
                break

            index = len(sources) + 1
            sources.append(
                LLMSource(
                    index=index,
                    content=content,
                    filename=scored.filename,
                    page_number=scored.chunk.page_number,
                )
            )
            source_map[index] = scored
            used_chars += len(content)

        return sources, source_map

    def _store_answer(
        self,
        conversation_id: int,
        answer: str,
        citations: list[Citation],
        grounded: bool,
    ) -> RagAnswer:
        message = self.conversation_repository.add_message(
            conversation_id,
            Message(
                role="assistant",
                content=answer,
                citations=[citation.__dict__ for citation in citations],
            ),
        )

        return RagAnswer(
            conversation_id=conversation_id,
            message_id=message.id,
            answer=answer,
            citations=citations,
            grounded=grounded,
        )

    @staticmethod
    def _to_citation(scored: ScoredChunk) -> Citation:
        content = scored.chunk.content
        snippet = content[:SNIPPET_LENGTH]
        if len(content) > SNIPPET_LENGTH:
            snippet += "..."

        return Citation(
            document_id=scored.document_id,
            filename=scored.filename,
            page_number=scored.chunk.page_number,
            chunk_id=scored.chunk.id,
            chunk_index=scored.chunk.chunk_index,
            snippet=snippet,
        )
