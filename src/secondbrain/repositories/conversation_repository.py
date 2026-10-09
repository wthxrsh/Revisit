from abc import ABC, abstractmethod

from secondbrain.models.conversation import Conversation, Message


class ConversationRepository(ABC):

    @abstractmethod
    def create(self, conversation: Conversation) -> Conversation:
        pass

    @abstractmethod
    def get_by_id(
        self, conversation_id: int, user_id: int
    ) -> Conversation | None:
        pass

    @abstractmethod
    def get_all(
        self,
        user_id: int,
        limit: int = 20,
        offset: int = 0,
    ) -> list[Conversation]:
        pass

    @abstractmethod
    def delete(self, conversation_id: int, user_id: int) -> bool:
        pass

    @abstractmethod
    def add_message(
        self, conversation_id: int, message: Message
    ) -> Message:
        pass

    @abstractmethod
    def get_messages(self, conversation_id: int) -> list[Message]:
        pass
