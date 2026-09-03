from fastapi.testclient import TestClient

from app.main import create_app
from app.schemas import InvoiceType, TypeMetric
from tests.conftest import FakeRepository


def test_startup_hydrates_cache_from_repository(settings, store, hub):
    repo = FakeRepository(
        [TypeMetric(invoice_type=InvoiceType.NACIONAL, total=50, count=1)]
    )
    app = create_app(
        settings=settings,
        store=store,
        hub=hub,
        repository=repo,
        load_on_startup=True,
    )
    with TestClient(app):
        assert store.snapshot().invoice_count == 1
