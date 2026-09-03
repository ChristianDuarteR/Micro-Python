import logging

from fastapi import APIRouter, Depends, status

from app.realtime import ConnectionHub
from app.schemas import ErrorResponse, InvoiceCreatedEvent, MetricsSnapshot
from app.security import require_internal_key
from app.store import MetricsStore

router = APIRouter(prefix="/internal/events", tags=["Eventos internos (Java)"])
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def get_store() -> MetricsStore:
    raise RuntimeError("Store no inicializado")


def get_hub() -> ConnectionHub:
    raise RuntimeError("Hub no inicializado")


@router.post(
    "/invoice-created",
    response_model=MetricsSnapshot,
    summary="Notificar alta de factura",
    description=(
        "Lo llama el micro **Java** justo después de persistir una factura.\n\n"
        "Incrementa el caché y hace broadcast por WebSocket `/ws/metrics` para que "
        "el Dashboard de Angular se actualice sin recargar ni volver a consultar la BD.\n\n"
        "Autenticación: header `X-Internal-Key` (mismo valor que `INTERNAL_API_KEY`)."
    ),
    responses={
        status.HTTP_200_OK: {
            "description": "Caché actualizado y clientes WS notificados.",
            "model": MetricsSnapshot,
        },
        status.HTTP_401_UNAUTHORIZED: {
            "description": "X-Internal-Key ausente o incorrecta.",
            "model": ErrorResponse,
        },
        status.HTTP_422_UNPROCESSABLE_CONTENT: {
            "description": "Tipo de factura desconocido o total inválido.",
        },
    },
)
async def invoice_created(
    event: InvoiceCreatedEvent,
    _: None = Depends(require_internal_key),
    store: MetricsStore = Depends(get_store),
    hub: ConnectionHub = Depends(get_hub),
) -> MetricsSnapshot:
    logger.info("Evento de factura recibido. invoice_type=%s total=%s", event.invoice_type, event.total)
    snapshot = store.apply_invoice(event.invoice_type, event.total)
    await hub.broadcast(snapshot)
    logger.info("Métricas actualizadas y evento emitido por WebSocket. invoice_count=%s", snapshot.invoice_count)
    return snapshot
