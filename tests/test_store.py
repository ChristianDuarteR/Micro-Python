from decimal import Decimal

from app.schemas import InvoiceType, TypeMetric
from app.store import MetricsStore


def test_snapshot_starts_at_zero():
    store = MetricsStore()
    snap = store.snapshot()
    assert snap.grand_total == Decimal("0.00")
    assert snap.invoice_count == 0
    assert len(snap.by_type) == 3


def test_apply_invoice_increments_type():
    store = MetricsStore()
    store.apply_invoice(InvoiceType.NACIONAL, Decimal("119.00"))
    snap = store.apply_invoice(InvoiceType.NACIONAL, Decimal("119.00"))
    nacional = next(item for item in snap.by_type if item.invoice_type == InvoiceType.NACIONAL)
    assert nacional.count == 2
    assert nacional.total == Decimal("238.00")
    assert snap.grand_total == Decimal("238.00")


def test_replace_overwrites_cache():
    store = MetricsStore()
    store.apply_invoice(InvoiceType.EXPORTACION, Decimal("10.00"))
    snap = store.replace(
        [TypeMetric(invoice_type=InvoiceType.GUBERNAMENTAL, total=Decimal("95.00"), count=1)]
    )
    exportacion = next(item for item in snap.by_type if item.invoice_type == InvoiceType.EXPORTACION)
    gubernamental = next(
        item for item in snap.by_type if item.invoice_type == InvoiceType.GUBERNAMENTAL
    )
    assert exportacion.count == 0
    assert gubernamental.total == Decimal("95.00")
    assert snap.invoice_count == 1
