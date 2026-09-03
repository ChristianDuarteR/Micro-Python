from decimal import Decimal
from unittest.mock import MagicMock

from sqlalchemy.exc import SQLAlchemyError

from app.config import Settings
from app.repository import InvoiceMetricsRepository
from app.schemas import InvoiceType


def test_fetch_aggregates_maps_rows():
    settings = Settings()
    engine = MagicMock()
    conn = MagicMock()
    engine.connect.return_value.__enter__.return_value = conn
    conn.execute.return_value.mappings.return_value.all.return_value = [
        {"invoice_type": "nacional", "total": Decimal("10.00"), "count": 2},
        {"invoice_type": "desconocido", "total": Decimal("1.00"), "count": 1},
    ]
    repo = InvoiceMetricsRepository(settings, engine=engine)
    rows = repo.fetch_aggregates()
    assert len(rows) == 1
    assert rows[0].invoice_type == InvoiceType.NACIONAL
    assert rows[0].count == 2


def test_fetch_aggregates_returns_empty_on_db_error():
    settings = Settings()
    engine = MagicMock()
    engine.connect.side_effect = SQLAlchemyError("down")
    repo = InvoiceMetricsRepository(settings, engine=engine)
    assert repo.fetch_aggregates() == []
