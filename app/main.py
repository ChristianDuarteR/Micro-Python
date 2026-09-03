import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Query, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi

from app.config import Settings, get_settings
from app.realtime import ConnectionHub
from app.repository import InvoiceMetricsRepository
from app.routers import events, metrics
from app.routers import router as health_router
from app.security import AUDITOR_ROLE, decode_token, extract_roles
from app.store import MetricsStore

logger = logging.getLogger(__name__)


def create_app(
    settings: Settings | None = None,
    store: MetricsStore | None = None,
    hub: ConnectionHub | None = None,
    repository: InvoiceMetricsRepository | None = None,
    load_on_startup: bool = True,
) -> FastAPI:
    settings = settings or get_settings()
    store = store or MetricsStore()
    hub = hub or ConnectionHub()
    repository = repository or InvoiceMetricsRepository(settings)

    @asynccontextmanager
    async def lifespan(_: FastAPI):
        if load_on_startup:
            try:
                store.replace(repository.fetch_aggregates())
                logger.info("Métricas cargadas desde PostgreSQL")
            except Exception:
                logger.exception("No se pudo hidratar el caché; se inicia en ceros")
        yield

    application = FastAPI(
        title="Global-Invoice Metrics",
        description=(
            "Microservicio Python de **métricas e inteligencia de negocio** (RF-04).\n\n"
            "## Autenticación\n"
            "Usa el botón **Authorize** de Swagger:\n"
            "- **BearerJWT**: JWT del micro Java. Claim `role` = `ROLE_AUDITOR` o `ROLE_OPERADOR`.\n"
            "- **InternalKey**: header `X-Internal-Key` para el evento interno Java → Python.\n\n"
            "## WebSocket (tiempo real)\n"
            "`WS /ws/metrics?token=<JWT>` — solo `ROLE_AUDITOR`. Al conectar envía el snapshot; "
            "cada `POST /internal/events/invoice-created` emite `{ event: metrics_updated, data: ... }`.\n\n"
            "Swagger UI no prueba WebSockets; usa Angular o un cliente WS."
        ),
        version="1.0.0",
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        openapi_tags=[
            {"name": "Salud", "description": "Liveness del servicio."},
            {
                "name": "Métricas (Dashboard)",
                "description": "Agregación por tipo de factura. Solo ROLE_AUDITOR.",
            },
            {
                "name": "Eventos internos (Java)",
                "description": "Notificación de altas para actualizar caché y WebSocket.",
            },
            {
                "name": "Tiempo real",
                "description": "WebSocket del Dashboard. No ejecutable desde Swagger UI.",
            },
        ],
        servers=[
            {"url": "http://localhost:5000", "description": "Local / Docker"},
        ],
        contact={"name": "Global-Invoice", "url": "http://localhost:5000/docs"},
    )
    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=settings.cors_origins.strip() != "*",
        allow_methods=["*"],
        allow_headers=["*"],
    )

    application.dependency_overrides[get_settings] = lambda: settings
    application.dependency_overrides[metrics.get_store] = lambda: store
    application.dependency_overrides[events.get_store] = lambda: store
    application.dependency_overrides[events.get_hub] = lambda: hub

    application.include_router(health_router)
    application.include_router(metrics.router)
    application.include_router(events.router)

    @application.websocket("/ws/metrics")
    async def metrics_ws(
        websocket: WebSocket,
        token: str = Query(
            default="",
            description="JWT del auditor (mismo token que Authorization Bearer). Rol ROLE_AUDITOR.",
        ),
    ):
        if not token:
            await websocket.close(code=4401)
            return
        try:
            payload = decode_token(token, settings)
        except Exception:
            await websocket.close(code=4401)
            return
        if AUDITOR_ROLE not in extract_roles(payload, settings):
            await websocket.close(code=4403)
            return

        await hub.connect(websocket)
        await websocket.send_json(
            {"event": "metrics_updated", "data": store.snapshot().model_dump(mode="json")}
        )
        try:
            while True:
                await websocket.receive_text()
        except WebSocketDisconnect:
            hub.disconnect(websocket)

    def custom_openapi():
        if application.openapi_schema:
            return application.openapi_schema
        schema = get_openapi(
            title=application.title,
            version=application.version,
            description=application.description,
            routes=application.routes,
            tags=application.openapi_tags,
            servers=application.servers,
        )
        schema["paths"]["/ws/metrics"] = {
            "get": {
                "tags": ["Tiempo real"],
                "summary": "WebSocket de métricas (RF-04)",
                "description": (
                    "Conexión `ws://localhost:5000/ws/metrics?token=<JWT>`.\n\n"
                    "Solo **ROLE_AUDITOR**. Al conectar envía `{ event: metrics_updated, data }` "
                    "y vuelve a emitir el mismo mensaje cuando Java notifica un alta.\n\n"
                    "Swagger UI no abre WebSockets; este path queda documentado para el contrato."
                ),
                "operationId": "metrics_websocket",
                "parameters": [
                    {
                        "name": "token",
                        "in": "query",
                        "required": True,
                        "schema": {"type": "string"},
                        "description": "JWT con claim role = ROLE_AUDITOR.",
                    }
                ],
                "responses": {
                    "101": {
                        "description": "Upgrade a WebSocket. Primer frame: snapshot de métricas."
                    }
                },
            }
        }
        application.openapi_schema = schema
        return schema

    application.openapi = custom_openapi

    application.state.store = store
    application.state.hub = hub
    application.state.settings = settings
    return application


app = create_app()
