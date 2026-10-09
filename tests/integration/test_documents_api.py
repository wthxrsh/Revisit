from pathlib import Path

import pytest

pytestmark = pytest.mark.integration

FIXTURES = Path(__file__).parent.parent / "fixtures"
VALID_PDF = b"%PDF-1.4\n1 0 obj\n<<>>\nendobj\n%%EOF"


def _upload(client, headers, filename, content, content_type="application/pdf"):
    return client.post(
        "/documents",
        files={"file": (filename, content, content_type)},
        headers=headers,
    )


def test_upload_and_process_pdf(client, registered_user):
    content = (FIXTURES / "sample.pdf").read_bytes()

    response = _upload(client, registered_user["headers"], "sample.pdf", content)

    assert response.status_code == 201
    body = response.json()
    assert body["original_filename"] == "sample.pdf"
    assert body["status"] == "completed"
    assert body["page_count"] == 2
    assert body["file_size"] == len(content)


def test_upload_requires_auth(client):
    response = client.post(
        "/documents", files={"file": ("a.pdf", VALID_PDF, "application/pdf")}
    )

    assert response.status_code == 401


def test_upload_rejects_non_pdf(client, registered_user):
    response = _upload(
        client, registered_user["headers"], "notes.txt", b"just text"
    )

    assert response.status_code == 415


def test_upload_fails_on_empty_pdf(client, registered_user):
    content = (FIXTURES / "empty.pdf").read_bytes()

    response = _upload(
        client, registered_user["headers"], "empty.pdf", content
    )

    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "failed"
    assert body["error_message"]


def test_upload_fails_on_encrypted_pdf(client, registered_user):
    content = (FIXTURES / "encrypted.pdf").read_bytes()

    response = _upload(
        client, registered_user["headers"], "encrypted.pdf", content
    )

    assert response.status_code == 201
    assert response.json()["status"] == "failed"


def test_upload_too_large(client, registered_user, monkeypatch, tmp_path):
    from secondbrain.api import dependencies
    from secondbrain.storage.file_storage import LocalFileStorage

    monkeypatch.setattr(
        dependencies,
        "get_file_storage",
        lambda: LocalFileStorage(tmp_path, max_size_bytes=10),
    )

    response = _upload(
        client, registered_user["headers"], "big.pdf", VALID_PDF
    )

    assert response.status_code == 413


def test_filename_is_sanitized(client, registered_user, tmp_path):
    content = (FIXTURES / "sample.pdf").read_bytes()

    response = _upload(
        client,
        registered_user["headers"],
        "../../etc/passwd.pdf",
        content,
    )

    assert response.status_code == 201
    assert response.json()["original_filename"] == "passwd.pdf"


def test_list_and_get_documents(client, registered_user):
    content = (FIXTURES / "sample.pdf").read_bytes()
    created = _upload(
        client, registered_user["headers"], "sample.pdf", content
    ).json()

    listing = client.get("/documents", headers=registered_user["headers"])
    assert listing.status_code == 200
    assert [doc["id"] for doc in listing.json()] == [created["id"]]

    fetched = client.get(
        f"/documents/{created['id']}", headers=registered_user["headers"]
    )
    assert fetched.status_code == 200
    assert fetched.json()["id"] == created["id"]


def test_documents_are_isolated_between_users(
    client, registered_user, second_user
):
    content = (FIXTURES / "sample.pdf").read_bytes()
    created = _upload(
        client, registered_user["headers"], "sample.pdf", content
    ).json()

    listing = client.get("/documents", headers=second_user["headers"])
    assert listing.json() == []

    fetched = client.get(
        f"/documents/{created['id']}", headers=second_user["headers"]
    )
    assert fetched.status_code == 404


def test_delete_document(client, registered_user):
    content = (FIXTURES / "sample.pdf").read_bytes()
    created = _upload(
        client, registered_user["headers"], "sample.pdf", content
    ).json()

    response = client.delete(
        f"/documents/{created['id']}", headers=registered_user["headers"]
    )
    assert response.status_code == 200

    assert (
        client.get(
            f"/documents/{created['id']}", headers=registered_user["headers"]
        ).status_code
        == 404
    )


def test_cannot_delete_other_users_document(
    client, registered_user, second_user
):
    content = (FIXTURES / "sample.pdf").read_bytes()
    created = _upload(
        client, registered_user["headers"], "sample.pdf", content
    ).json()

    response = client.delete(
        f"/documents/{created['id']}", headers=second_user["headers"]
    )

    assert response.status_code == 404
