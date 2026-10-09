from secondbrain.exceptions import ConversationNotFoundError
from secondbrain.models.conversation import Conversation, Message
from secondbrain.repositories.conversation_repository import (
    ConversationRepository,
)


class ConversationService:

    def __init__(self, conversation_repository: ConversationRepository):
        self.conversation_repository = conversation_repository

    def list_conversations(
        self, user_id: int, limit: int = 20, offset: int = 0
    ) -> list[Conversation]:
        return self.conversation_repository.get_all(
            user_id=user_id, limit=limit, offset=offset
        )

    def get(
        self, conversation_id: int, user_id: int
    ) -> tuple[Conversation, list[Message]]:
        conversation = self.conversation_repository.get_by_id(
            conversation_id, user_id
        )

        if conversation is None:
            raise ConversationNotFoundError(
                f"Conversation with id {conversation_id} not found"
            )

        messages = self.conversation_repository.get_messages(conversation_id)

        return conversation, messages

    def delete(self, conversation_id: int, user_id: int) -> None:
        deleted = self.conversation_repository.delete(conversation_id, user_id)

        if not deleted:
            raise ConversationNotFoundError(
                f"Conversation with id {conversation_id} not found"
            )
