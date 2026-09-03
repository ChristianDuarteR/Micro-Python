from fastapi.testclient import TestClient

from tests.conftest import make_token, seed_store


def test_metrics_requires_token(app):
    client = TestClient(app)
    response = client.get("/api/v1/metrics/by-type")
    assert response.status_code == 401


def test_operador_cannot_read_metrics(app, settings):
    client = TestClient(app)
    token = make_token(settings, "ROLE_OPERADOR")
    response = client.get(
        "/api/v1/metrics/by-type",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 403


def test_auditor_reads_cached_metrics(app, settings, store):
    seed_store(store)
    client = TestClient(app)
    token = make_token(settings, "ROLE_AUDITOR")
    response = client.get(
        "/api/v1/metrics/by-type",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["invoice_count"] == 2
    assert body["grand_total"] == "169.00"


def test_expired_token_is_rejected(app, settings):
    client = TestClient(app)
    token = make_token(settings, "ROLE_AUDITOR", expired=True)
    response = client.get(
        "/api/v1/metrics/by-type",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 401
