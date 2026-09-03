from decimal import Decimal

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError

from app.config import Settings
from app.schemas import InvoiceType, TypeMetric

_ALLOWED_IDENTIFIERS = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_")


def _safe_ident(value: str) -> str:
    if not value or any(ch not in _ALLOWED_IDENTIFIERS for ch in value):
        raise ValueError(f"Identificador SQL inválido: {value}")
    return value


class InvoiceMetricsRepository:
    def __init__(self, settings: Settings, engine: Engine | None = None) -> None:
        self._settings = settings
        self._engine = engine or create_engine(settings.database_url, pool_pre_ping=True)

    def fetch_aggregates(self) -> list[TypeMetric]:
        table = _safe_ident(self._settings.invoice_table)
        type_col = _safe_ident(self._settings.invoice_type_column)
        total_col = _safe_ident(self._settings.invoice_total_column)
        sql = text(
            f"""
            SELECT {type_col} AS invoice_type,
                   COALESCE(SUM({total_col}), 0) AS total,
                   COUNT(*) AS count
            FROM {table}
            GROUP BY {type_col}
            """
        )
        try:
            with self._engine.connect() as conn:
                rows = conn.execute(sql).mappings().all()
        except SQLAlchemyError:
            return []

        metrics: list[TypeMetric] = []
        for row in rows:
            raw_type = str(row["invoice_type"]).upper()
            try:
                invoice_type = InvoiceType(raw_type)
            except ValueError:
                continue
            metrics.append(
                TypeMetric(
                    invoice_type=invoice_type,
                    total=Decimal(str(row["total"])),
                    count=int(row["count"]),
                )
            )
        return metrics
