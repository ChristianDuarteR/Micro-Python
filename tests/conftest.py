from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest
from jose import jwt

from app.config import Settings
from app.main import create_app
from app.realtime import ConnectionHub
from app.schemas import InvoiceType, TypeMetric
from app.store import MetricsStore


class FakeRepository:
    def __init__(self, rows: list[TypeMetric] | None = None) -> None:
        self.rows = rows or []

    def fetch_aggregates(self) -> list[TypeMetric]:
        return self.rows


@pytest.fixture
def settings() -> Settings:
    return Settings(
        jwt_secret="test-secret",
        internal_api_key="test-internal",
        cors_origins="http://localhost:4200",
    )


@pytest.fixture
def store() -> MetricsStore:
    return MetricsStore()


@pytest.fixture
def hub() -> ConnectionHub:
    return ConnectionHub()


@pytest.fixture
def app(settings, store, hub):
    return create_app(
        settings=settings,
        store=store,
        hub=hub,
        repository=FakeRepository(),
        load_on_startup=False,
    )


def make_token(settings: Settings, role: str, expired: bool = False) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": "tester",
        "role": role,
        "exp": now - timedelta(hours=1) if expired else now + timedelta(hours=1),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def seed_store(store: MetricsStore) -> None:
    store.replace(
        [
            TypeMetric(invoice_type=InvoiceType.NACIONAL, total=Decimal("119.00"), count=1),
            TypeMetric(invoice_type=InvoiceType.EXPORTACION, total=Decimal("50.00"), count=1),
        ]
    )
