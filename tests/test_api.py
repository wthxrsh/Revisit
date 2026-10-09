from fastapi.testclient import TestClient

from secondbrain.api.app import app


client = TestClient(app)


def test_health_check():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_create_note():
    response = client.post(
        "/notes",
        json={
            "id": 1,
            "title": "Python",
            "content": "Learning FastAPI",
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["id"] == 1
    assert data["title"] == "Python"
    assert data["content"] == "Learning FastAPI"


def test_get_note():
    response = client.get("/notes/1")

    assert response.status_code == 200
    assert response.json()["title"] == "Python"


def test_missing_note():
    response = client.get("/notes/999")

    assert response.status_code == 404


def test_delete_note():
    response = client.delete("/notes/1")

    assert response.status_code == 200

    response = client.get("/notes/1")

    assert response.status_code == 404