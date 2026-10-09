from datetime import datetime, timedelta, timezone

import jwt
import pytest

from secondbrain.config import settings
from secondbrain.services.jwt_service import (
    create_access_token,
    decode_access_token,
)


def test_token_round_trip():
    token = create_access_token(123)

    assert decode_access_token(token) == 123


def test_tampered_token_is_rejected():
    token = create_access_token(123)
    tampered = token[:-2] + ("aa" if not token.endswith("aa") else "bb")

    with pytest.raises(jwt.PyJWTError):
        decode_access_token(tampered)


def test_expired_token_is_rejected():
    expired = jwt.encode(
        {
            "sub": "1",
            "exp": datetime.now(timezone.utc) - timedelta(minutes=1),
        },
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )

    with pytest.raises(jwt.ExpiredSignatureError):
        decode_access_token(expired)


def test_token_signed_with_wrong_key_is_rejected():
    forged = jwt.encode(
        {
            "sub": "1",
            "exp": datetime.now(timezone.utc) + timedelta(minutes=5),
        },
        "definitely-not-the-real-secret-1234567890",
        algorithm=settings.jwt_algorithm,
    )

    with pytest.raises(jwt.InvalidSignatureError):
        decode_access_token(forged)


def test_missing_subject_is_rejected():
    token = jwt.encode(
        {"exp": datetime.now(timezone.utc) + timedelta(minutes=5)},
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )

    with pytest.raises(jwt.PyJWTError):
        decode_access_token(token)
