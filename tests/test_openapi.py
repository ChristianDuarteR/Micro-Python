from fastapi.testclient import TestClient


def test_swagger_ui_and_openapi(app):
    client = TestClient(app)
    docs = client.get("/docs")
    redoc = client.get("/redoc")
    spec = client.get("/openapi.json")

    assert docs.status_code == 200
    assert redoc.status_code == 200
    assert spec.status_code == 200

    body = spec.json()
    paths = body["paths"]
    assert "/health" in paths
    assert "/api/v1/metrics/by-type" in paths
    assert "/internal/events/invoice-created" in paths
    assert "/ws/metrics" in paths

    schemes = body["components"]["securitySchemes"]
    assert "BearerJWT" in schemes
    assert "InternalKey" in schemes
    assert body["info"]["title"] == "Global-Invoice Metrics"
