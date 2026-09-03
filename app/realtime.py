import logging

from fastapi import WebSocket

from app.schemas import MetricsMessage, MetricsSnapshot


class ConnectionHub:
    def __init__(self) -> None:
        self._clients: set[WebSocket] = set()
        self._logger = logging.getLogger(__name__)
        self._logger.setLevel(logging.INFO)

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        self._clients.add(websocket)

    def disconnect(self, websocket: WebSocket) -> None:
        self._clients.discard(websocket)

    async def broadcast(self, snapshot: MetricsSnapshot) -> None:
        message = MetricsMessage(data=snapshot).model_dump(mode="json")
        stale: list[WebSocket] = []
        self._logger.info("Broadcast de métricas a %s clientes WebSocket", len(self._clients))
        for client in list(self._clients):
            try:
                await client.send_json(message)
            except Exception:
                stale.append(client)
        for client in stale:
            self.disconnect(client)
