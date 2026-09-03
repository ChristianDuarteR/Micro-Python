from fastapi.testclient import TestClient

from tests.conftest import make_token, seed_store


def test_ws_rejects_missing_token(app):
    client = TestClient(app)
    try:
        with client.websocket_connect("/ws/metrics"):
            pass
        assert False, "debía cerrar"
    except Exception:
        pass


def test_ws_auditor_receives_snapshot_and_event(app, settings, store):
    seed_store(store)
    token = make_token(settings, "ROLE_AUDITOR")
    client = TestClient(app)

    with client.websocket_connect(f"/ws/metrics?token={token}") as ws:
        first = ws.receive_json()
        assert first["event"] == "metrics_updated"
        assert first["data"]["invoice_count"] == 2

        response = client.post(
            "/internal/events/invoice-created",
            json={"invoice_type": "NACIONAL", "total": "119.00"},
            headers={"X-Internal-Key": settings.internal_api_key},
        )
        assert response.status_code == 200
        update = ws.receive_json()
        assert update["data"]["invoice_count"] == 3
        assert update["data"]["grand_total"] == "288.00"


def test_ws_operador_is_rejected(app, settings):
    token = make_token(settings, "ROLE_OPERADOR")
    client = TestClient(app)
    try:
        with client.websocket_connect(f"/ws/metrics?token={token}"):
            pass
        assert False, "el operador no debe conectar"
    except Exception:
        pass
