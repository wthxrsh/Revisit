import uuid

import pytest

pytestmark = pytest.mark.integration


def _email() -> str:
    return f"user-{uuid.uuid4().hex}@example.com"


def test_register_returns_created_user(client):
    email = _email()

    response = client.post(
        "/auth/register", json={"email": email, "password": "password123"}
    )

    assert response.status_code == 201
    body = response.json()
    assert body["email"] == email
    assert body["id"] > 0
    assert "password" not in body


def test_register_rejects_duplicate_email(client):
    email = _email()
    payload = {"email": email, "password": "password123"}

    assert client.post("/auth/register", json=payload).status_code == 201
    duplicate = client.post("/auth/register", json=payload)

    assert duplicate.status_code == 409
    assert duplicate.json()["error"] == "conflict"


def test_register_rejects_short_password(client):
    response = client.post(
        "/auth/register", json={"email": _email(), "password": "short"}
    )

    assert response.status_code == 422


def test_register_rejects_invalid_email(client):
    response = client.post(
        "/auth/register", json={"email": "not-an-email", "password": "password123"}
    )

    assert response.status_code == 422


def test_login_returns_token(client):
    email = _email()
    client.post(
        "/auth/register", json={"email": email, "password": "password123"}
    )

    response = client.post(
        "/auth/login", json={"email": email, "password": "password123"}
    )

    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"]


def test_login_email_is_case_insensitive(client):
    email = _email()
    client.post(
        "/auth/register", json={"email": email, "password": "password123"}
    )

    response = client.post(
        "/auth/login",
        json={"email": email.upper(), "password": "password123"},
    )

    assert response.status_code == 200


def test_login_with_wrong_password_fails(client):
    email = _email()
    client.post(
        "/auth/register", json={"email": email, "password": "password123"}
    )

    response = client.post(
        "/auth/login", json={"email": email, "password": "wrong-password"}
    )

    assert response.status_code == 401


def test_login_with_unknown_user_fails(client):
    response = client.post(
        "/auth/login", json={"email": _email(), "password": "password123"}
    )

    assert response.status_code == 401


def test_protected_route_requires_token(client):
    response = client.get("/notes")

    assert response.status_code == 401


def test_protected_route_rejects_garbage_token(client):
    response = client.get(
        "/notes", headers={"Authorization": "Bearer not-a-real-token"}
    )

    assert response.status_code == 401


def test_only_password_hash_is_stored(client, db_session):
    from sqlalchemy import text

    email = _email()
    client.post(
        "/auth/register", json={"email": email, "password": "password123"}
    )

    stored = db_session.execute(
        text("SELECT password_hash FROM users WHERE email = :email"),
        {"email": email},
    ).scalar()

    assert stored is not None
    assert stored != "password123"
    assert stored.startswith("$")
