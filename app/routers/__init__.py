from fastapi import APIRouter, Depends, status

from app.schemas import ErrorResponse, HealthResponse

router = APIRouter(tags=["Salud"])


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Health check",
    description="Verifica que el micro de métricas está vivo. No requiere autenticación.",
    responses={
        status.HTTP_200_OK: {"description": "Servicio disponible.", "model": HealthResponse},
    },
)
def health() -> HealthResponse:
    return HealthResponse(status="ok", service="global-invoice-metrics")
