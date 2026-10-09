from secondbrain.services.password_service import (
    hash_password,
    verify_password,
)


def test_password_is_hashed():
    password = "my-secret-password"

    hashed_password = hash_password(password)

    assert hashed_password != password


def test_correct_password_is_verified():
    password = "my-secret-password"

    hashed_password = hash_password(password)

    assert verify_password(password, hashed_password) is True


def test_wrong_password_is_rejected():
    password = "my-secret-password"

    hashed_password = hash_password(password)

    assert verify_password("wrong-password", hashed_password) is False


def test_same_password_produces_different_hashes():
    password = "my-secret-password"

    hash_one = hash_password(password)
    hash_two = hash_password(password)

    assert hash_one != hash_two