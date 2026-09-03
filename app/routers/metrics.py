from fastapi import APIRouter, Depends, status

from app.schemas import ErrorResponse, MetricsSnapshot
from app.security import require_auditor
from app.store import MetricsStore

router = APIRouter(prefix="/api/v1/metrics", tags=["Métricas (Dashboard)"])


def get_store() -> MetricsStore:
    raise RuntimeError("Store no inicializado")


@router.get(
    "/by-type",
    response_model=MetricsSnapshot,
    summary="Total facturado por tipo de factura",
    description=(
        "Devuelve el snapshot en caché (RF-04): `SUM(total)` y `COUNT(*)` por "
        "`NACIONAL`, `EXPORTACION` y `GUBERNAMENTAL`.\n\n"
        "No consulta PostgreSQL en cada petición. Requiere JWT con rol **ROLE_AUDITOR**. "
        "ROLE_OPERADOR recibe 403."
    ),
    responses={
        status.HTTP_200_OK: {"description": "Snapshot de métricas.", "model": MetricsSnapshot},
        status.HTTP_401_UNAUTHORIZED: {
            "description": "Sin Bearer token o JWT inválido/expirado.",
            "model": ErrorResponse,
        },
        status.HTTP_403_FORBIDDEN: {
            "description": "El token no tiene rol ROLE_AUDITOR.",
            "model": ErrorResponse,
        },
    },
)
def metrics_by_type(
    _: dict = Depends(require_auditor),
    store: MetricsStore = Depends(get_store),
) -> MetricsSnapshot:
    return store.snapshot()
