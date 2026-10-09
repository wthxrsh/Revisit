from sqlalchemy import select
from sqlalchemy.orm import Session

from secondbrain.database.conversation_models import (
    ConversationModel,
    MessageModel,
)
from secondbrain.models.conversation import Conversation, Message
from secondbrain.repositories.conversation_repository import (
    ConversationRepository,
)


class PostgresConversationRepository(ConversationRepository):

    def __init__(self, session: Session):
        self.session = session

    def create(self, conversation: Conversation) -> Conversation:
        model = ConversationModel(
            user_id=conversation.user_id,
            title=conversation.title,
            created_at=conversation.created_at,
        )

        self.session.add(model)
        self.session.commit()
        self.session.refresh(model)

        return self._to_domain(model)

    def get_by_id(
        self, conversation_id: int, user_id: int
    ) -> Conversation | None:
        statement = select(ConversationModel).where(
            ConversationModel.id == conversation_id,
            ConversationModel.user_id == user_id,
        )

        model = self.session.scalar(statement)

        return self._to_domain(model) if model else None

    def get_all(
        self,
        user_id: int,
        limit: int = 20,
        offset: int = 0,
    ) -> list[Conversation]:
        statement = (
            select(ConversationModel)
            .where(ConversationModel.user_id == user_id)
            .order_by(
                ConversationModel.created_at.desc(),
                ConversationModel.id.desc(),
            )
            .limit(limit)
            .offset(offset)
        )

        models = self.session.scalars(statement).all()

        return [self._to_domain(model) for model in models]

    def delete(self, conversation_id: int, user_id: int) -> bool:
        statement = select(ConversationModel).where(
            ConversationModel.id == conversation_id,
            ConversationModel.user_id == user_id,
        )

        model = self.session.scalar(statement)

        if model is None:
            return False

        self.session.delete(model)
        self.session.commit()

        return True

    def add_message(
        self, conversation_id: int, message: Message
    ) -> Message:
        model = MessageModel(
            conversation_id=conversation_id,
            role=message.role,
            content=message.content,
            citations=message.citations,
            created_at=message.created_at,
        )

        self.session.add(model)
        self.session.commit()
        self.session.refresh(model)

        return self._to_message_domain(model)

    def get_messages(self, conversation_id: int) -> list[Message]:
        statement = (
            select(MessageModel)
            .where(MessageModel.conversation_id == conversation_id)
            .order_by(MessageModel.id)
        )

        models = self.session.scalars(statement).all()

        return [self._to_message_domain(model) for model in models]

    @staticmethod
    def _to_domain(model: ConversationModel) -> Conversation:
        return Conversation(
            id=model.id,
            user_id=model.user_id,
            title=model.title,
            created_at=model.created_at,
        )

    @staticmethod
    def _to_message_domain(model: MessageModel) -> Message:
        return Message(
            id=model.id,
            conversation_id=model.conversation_id,
            role=model.role,
            content=model.content,
            citations=model.citations,
            created_at=model.created_at,
        )
