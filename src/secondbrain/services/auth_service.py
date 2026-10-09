from datetime import datetime

from secondbrain.exceptions import UserAlreadyExistsError, InvalidCredentialsError
from secondbrain.models.user import User
from secondbrain.repositories.user_repository import UserRepository
from secondbrain.services.jwt_service import create_access_token
from secondbrain.services.password_service import hash_password, verify_password


class AuthService:

    def __init__(self, user_repository: UserRepository):
        self.user_repository = user_repository

    def register(self, email: str, password: str) -> User:
        existing_user = self.user_repository.get_by_email(email)

        if existing_user is not None:
            raise UserAlreadyExistsError(
                "A user with this email already exists."
            )

        user = User(
            id=None,
            email=email,
            password_hash=hash_password(password),
            created_at=datetime.now(),
        )

        return self.user_repository.save(user)

    def login(self, email: str, password: str) -> str:
        user = self.user_repository.get_by_email(email)

        if user is None:
            raise InvalidCredentialsError("Invalid email or password.")

        if not verify_password(password, user.password_hash):
            raise InvalidCredentialsError("Invalid email or password.")

        return create_access_token(user.id)