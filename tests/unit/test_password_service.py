from secondbrain.services.password_service import (
    hash_password,
    verify_password,
)


def test_password_is_hashed():
    password = "my-secret-password"

    hashed = hash_password(password)

    assert hashed != password


def test_correct_password_is_verified():
    hashed = hash_password("my-secret-password")

    assert verify_password("my-secret-password", hashed) is True


def test_wrong_password_is_rejected():
    hashed = hash_password("my-secret-password")

    assert verify_password("wrong-password", hashed) is False


def test_same_password_produces_different_hashes():
    assert hash_password("my-secret-password") != hash_password(
        "my-secret-password"
    )
