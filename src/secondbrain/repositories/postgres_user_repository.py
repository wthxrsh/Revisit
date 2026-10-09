from sqlalchemy import select
from sqlalchemy.orm import Session

from secondbrain.database.user_models import UserModel
from secondbrain.models.user import User
from secondbrain.repositories.user_repository import UserRepository


class PostgresUserRepository(UserRepository):

    def __init__(self, session: Session):
        self.session = session

    def save(self, user: User) -> User:
        user_model = UserModel(
            email=user.email,
            password_hash=user.password_hash,
            created_at=user.created_at,
        )

        self.session.add(user_model)
        self.session.commit()
        self.session.refresh(user_model)

        return self._to_domain(user_model)

    def get_by_id(self, user_id: int) -> User | None:
        user_model = self.session.get(UserModel, user_id)

        if user_model is None:
            return None

        return self._to_domain(user_model)

    def get_by_email(self, email: str) -> User | None:
        statement = select(UserModel).where(UserModel.email == email)

        user_model = self.session.execute(statement).scalar_one_or_none()

        if user_model is None:
            return None

        return self._to_domain(user_model)

    @staticmethod
    def _to_domain(user_model: UserModel) -> User:
        return User(
            id=user_model.id,
            email=user_model.email,
            password_hash=user_model.password_hash,
            created_at=user_model.created_at,
        )