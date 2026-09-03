from fastapi.testclient import TestClient


def test_health(app):
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["service"] == "global-invoice-metrics"
