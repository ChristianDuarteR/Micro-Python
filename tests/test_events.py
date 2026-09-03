from fastapi.testclient import TestClient

from tests.conftest import make_token


def test_event_requires_internal_key(app):
    client = TestClient(app)
    response = client.post(
        "/internal/events/invoice-created",
        json={"invoice_type": "NACIONAL", "total": "119.00"},
    )
    assert response.status_code == 401


def test_event_updates_cache(app, settings):
    client = TestClient(app)
    response = client.post(
        "/internal/events/invoice-created",
        json={"invoice_type": "EXPORTACION", "total": "200.50"},
        headers={"X-Internal-Key": settings.internal_api_key},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["grand_total"] == "200.50"
    assert body["invoice_count"] == 1

    token = make_token(settings, "ROLE_AUDITOR")
    metrics = client.get(
        "/api/v1/metrics/by-type",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert metrics.json()["grand_total"] == "200.50"


def test_event_rejects_unknown_type(app, settings):
    client = TestClient(app)
    response = client.post(
        "/internal/events/invoice-created",
        json={"invoice_type": "OTRO", "total": "10.00"},
        headers={"X-Internal-Key": settings.internal_api_key},
    )
    assert response.status_code == 422
