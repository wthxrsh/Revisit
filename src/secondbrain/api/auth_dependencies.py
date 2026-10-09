import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from secondbrain.database.dependencies import get_db
from secondbrain.models.user import User
from secondbrain.repositories.postgres_user_repository import (
    PostgresUserRepository,
)
from secondbrain.services.jwt_service import decode_access_token

bearer_scheme = HTTPBearer(auto_error=False)

_UNAUTHORIZED_HEADERS = {"WWW-Authenticate": "Bearer"}


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers=_UNAUTHORIZED_HEADERS,
        )

    token = credentials.credentials

    try:
        user_id = decode_access_token(token)
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers=_UNAUTHORIZED_HEADERS,
        )

    repository = PostgresUserRepository(db)
    user = repository.get_by_id(user_id)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers=_UNAUTHORIZED_HEADERS,
        )

    return user
