from pathlib import Path

import pytest

pytestmark = pytest.mark.integration

FIXTURES = Path(__file__).parent.parent / "fixtures"


@pytest.fixture
def uploaded_document(client, registered_user):
    content = (FIXTURES / "sample.pdf").read_bytes()
    response = client.post(
        "/documents",
        files={"file": ("sample.pdf", content, "application/pdf")},
        headers=registered_user["headers"],
    )
    assert response.status_code == 201, response.text
    assert response.json()["status"] == "completed"
    return response.json()


def test_chat_is_grounded_in_documents(client, registered_user, uploaded_document):
    response = client.post(
        "/chat",
        json={"question": "What is retrieval augmented generation?"},
        headers=registered_user["headers"],
    )

    assert response.status_code == 200
    body = response.json()
    assert body["grounded"] is True
    assert body["citations"]
    citation = body["citations"][0]
    assert citation["filename"] == "sample.pdf"
    assert citation["document_id"] == uploaded_document["id"]
    assert citation["snippet"]


def test_chat_refuses_without_relevant_context(client, registered_user, uploaded_document):
    response = client.post(
        "/chat",
        json={"question": "How do I bake sourdough bread?"},
        headers=registered_user["headers"],
    )

    assert response.status_code == 200
    body = response.json()
    assert body["grounded"] is False
    assert body["citations"] == []
    assert "could not find" in body["answer"].lower()


def test_chat_with_no_documents_does_not_answer(client, registered_user):
    response = client.post(
        "/chat",
        json={"question": "What is retrieval augmented generation?"},
        headers=registered_user["headers"],
    )

    assert response.status_code == 200
    body = response.json()
    assert body["grounded"] is False
    assert body["citations"] == []


def test_chat_is_isolated_between_users(
    client, registered_user, second_user, uploaded_document
):
    response = client.post(
        "/chat",
        json={"question": "What is retrieval augmented generation?"},
        headers=second_user["headers"],
    )

    assert response.status_code == 200
    body = response.json()
    assert body["grounded"] is False
    assert body["citations"] == []


def test_chat_requires_auth(client):
    response = client.post("/chat", json={"question": "hello"})

    assert response.status_code == 401


def test_chat_rejects_empty_question(client, registered_user):
    response = client.post(
        "/chat", json={"question": ""}, headers=registered_user["headers"]
    )

    assert response.status_code == 422


def test_conversation_is_persisted(client, registered_user, uploaded_document):
    first = client.post(
        "/chat",
        json={"question": "What is retrieval augmented generation?"},
        headers=registered_user["headers"],
    ).json()

    conversation_id = first["conversation_id"]

    detail = client.get(
        f"/conversations/{conversation_id}",
        headers=registered_user["headers"],
    )

    assert detail.status_code == 200
    messages = detail.json()["messages"]
    assert len(messages) == 2
    assert messages[0]["role"] == "user"
    assert messages[1]["role"] == "assistant"


def test_follow_up_uses_existing_conversation(
    client, registered_user, uploaded_document
):
    first = client.post(
        "/chat",
        json={"question": "What is retrieval augmented generation?"},
        headers=registered_user["headers"],
    ).json()

    second = client.post(
        "/chat",
        json={
            "question": "What does chunking do?",
            "conversation_id": first["conversation_id"],
        },
        headers=registered_user["headers"],
    ).json()

    assert second["conversation_id"] == first["conversation_id"]

    detail = client.get(
        f"/conversations/{first['conversation_id']}",
        headers=registered_user["headers"],
    ).json()
    assert len(detail["messages"]) == 4


def test_cannot_read_other_users_conversation(
    client, registered_user, second_user, uploaded_document
):
    created = client.post(
        "/chat",
        json={"question": "What is retrieval augmented generation?"},
        headers=registered_user["headers"],
    ).json()

    response = client.get(
        f"/conversations/{created['conversation_id']}",
        headers=second_user["headers"],
    )

    assert response.status_code == 404


def test_list_and_delete_conversations(client, registered_user, uploaded_document):
    created = client.post(
        "/chat",
        json={"question": "What is retrieval augmented generation?"},
        headers=registered_user["headers"],
    ).json()

    listing = client.get("/conversations", headers=registered_user["headers"])
    assert listing.status_code == 200
    assert created["conversation_id"] in [
        conversation["id"] for conversation in listing.json()
    ]

    deleted = client.delete(
        f"/conversations/{created['conversation_id']}",
        headers=registered_user["headers"],
    )
    assert deleted.status_code == 200

    assert (
        client.get(
            f"/conversations/{created['conversation_id']}",
            headers=registered_user["headers"],
        ).status_code
        == 404
    )
