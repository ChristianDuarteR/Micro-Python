from decimal import Decimal
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class InvoiceType(str, Enum):
    NACIONAL = "NACIONAL"
    EXPORTACION = "EXPORTACION"
    GUBERNAMENTAL = "GUBERNAMENTAL"


class TypeMetric(BaseModel):
    invoice_type: InvoiceType = Field(description="Tipo de factura (RF-01).")
    total: Decimal = Field(decimal_places=2, description="Suma de totales de ese tipo.", examples=["119.00"])
    count: int = Field(default=0, ge=0, description="Cantidad de facturas de ese tipo.")


class MetricsSnapshot(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "by_type": [
                    {"invoice_type": "NACIONAL", "total": "119.00", "count": 1},
                    {"invoice_type": "EXPORTACION", "total": "0.00", "count": 0},
                    {"invoice_type": "GUBERNAMENTAL", "total": "0.00", "count": 0},
                ],
                "grand_total": "119.00",
                "invoice_count": 1,
            }
        }
    )

    by_type: list[TypeMetric] = Field(description="Agregados por cada tipo de factura.")
    grand_total: Decimal = Field(decimal_places=2, description="Total facturado (todos los tipos).")
    invoice_count: int = Field(default=0, ge=0, description="Número total de facturas.")


class InvoiceCreatedEvent(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {"invoice_type": "NACIONAL", "total": "119.00"}
        }
    )

    invoice_type: InvoiceType = Field(description="Tipo de la factura recién persistida en Java.")
    total: Decimal = Field(gt=0, decimal_places=2, description="Total de la factura (no el subtotal).")


class MetricsMessage(BaseModel):
    event: str = Field(default="metrics_updated", description="Nombre del evento WebSocket.")
    data: MetricsSnapshot


class HealthResponse(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={"example": {"status": "ok", "service": "global-invoice-metrics"}}
    )

    status: str
    service: str


class ErrorResponse(BaseModel):
    detail: str = Field(examples=["Se requiere Bearer token"])
