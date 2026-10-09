import pytest

pytestmark = pytest.mark.integration


def test_health_endpoint(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_readiness_endpoint(client):
    response = client.get("/ready")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ready"
    assert body["checks"]["database"] == "ok"


def test_unknown_route_returns_error_envelope(client):
    response = client.get("/does-not-exist")

    assert response.status_code == 404
    assert response.json()["error"] == "http_error"
