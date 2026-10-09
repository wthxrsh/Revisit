import pytest

pytestmark = pytest.mark.integration


def test_create_note(client, registered_user):
    response = client.post(
        "/notes",
        json={"title": "Python", "content": "Learning FastAPI"},
        headers=registered_user["headers"],
    )

    assert response.status_code == 201
    body = response.json()
    assert body["id"] > 0
    assert body["title"] == "Python"
    assert body["content"] == "Learning FastAPI"
    assert body["created_at"]
    assert body["updated_at"]


def test_create_note_requires_auth(client):
    response = client.post("/notes", json={"title": "x", "content": "y"})

    assert response.status_code == 401


def test_create_note_rejects_empty_title(client, registered_user):
    response = client.post(
        "/notes",
        json={"title": "", "content": "y"},
        headers=registered_user["headers"],
    )

    assert response.status_code == 422


def test_create_note_rejects_whitespace_title(client, registered_user):
    response = client.post(
        "/notes",
        json={"title": "   ", "content": "y"},
        headers=registered_user["headers"],
    )

    assert response.status_code == 400
    assert response.json()["error"] == "validation_error"


def test_get_note(client, registered_user):
    created = client.post(
        "/notes",
        json={"title": "Python", "content": "body"},
        headers=registered_user["headers"],
    ).json()

    response = client.get(
        f"/notes/{created['id']}", headers=registered_user["headers"]
    )

    assert response.status_code == 200
    assert response.json()["id"] == created["id"]


def test_get_missing_note_returns_404(client, registered_user):
    response = client.get("/notes/999999", headers=registered_user["headers"])

    assert response.status_code == 404


def test_notes_are_isolated_between_users(client, registered_user, second_user):
    client.post(
        "/notes",
        json={"title": "Mine", "content": "private"},
        headers=registered_user["headers"],
    )

    response = client.get("/notes", headers=second_user["headers"])

    assert response.status_code == 200
    assert response.json() == []


def test_cannot_read_other_users_note(client, registered_user, second_user):
    created = client.post(
        "/notes",
        json={"title": "Mine", "content": "private"},
        headers=registered_user["headers"],
    ).json()

    response = client.get(
        f"/notes/{created['id']}", headers=second_user["headers"]
    )

    assert response.status_code == 404


def test_cannot_update_other_users_note(client, registered_user, second_user):
    created = client.post(
        "/notes",
        json={"title": "Mine", "content": "private"},
        headers=registered_user["headers"],
    ).json()

    response = client.put(
        f"/notes/{created['id']}",
        json={"title": "Hacked", "content": "stolen"},
        headers=second_user["headers"],
    )

    assert response.status_code == 404


def test_cannot_delete_other_users_note(client, registered_user, second_user):
    created = client.post(
        "/notes",
        json={"title": "Mine", "content": "private"},
        headers=registered_user["headers"],
    ).json()

    response = client.delete(
        f"/notes/{created['id']}", headers=second_user["headers"]
    )

    assert response.status_code == 404

    still_there = client.get(
        f"/notes/{created['id']}", headers=registered_user["headers"]
    )
    assert still_there.status_code == 200


def test_update_note(client, registered_user):
    created = client.post(
        "/notes",
        json={"title": "Old", "content": "old body"},
        headers=registered_user["headers"],
    ).json()

    response = client.put(
        f"/notes/{created['id']}",
        json={"title": "New", "content": "new body"},
        headers=registered_user["headers"],
    )

    assert response.status_code == 200
    assert response.json()["title"] == "New"


def test_delete_note(client, registered_user):
    created = client.post(
        "/notes",
        json={"title": "Doomed", "content": "bye"},
        headers=registered_user["headers"],
    ).json()

    response = client.delete(
        f"/notes/{created['id']}", headers=registered_user["headers"]
    )

    assert response.status_code == 200
    assert (
        client.get(
            f"/notes/{created['id']}", headers=registered_user["headers"]
        ).status_code
        == 404
    )


def test_list_notes_search(client, registered_user):
    for title in ("Python", "JavaScript", "Python tricks"):
        client.post(
            "/notes",
            json={"title": title, "content": "body"},
            headers=registered_user["headers"],
        )

    response = client.get(
        "/notes", params={"search": "python"}, headers=registered_user["headers"]
    )

    assert response.status_code == 200
    titles = {note["title"] for note in response.json()}
    assert titles == {"Python", "Python tricks"}
