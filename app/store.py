from decimal import Decimal
from threading import Lock

from app.schemas import InvoiceType, MetricsSnapshot, TypeMetric

ZERO = Decimal("0.00")


class MetricsStore:
    def __init__(self) -> None:
        self._lock = Lock()
        self._reset_unlocked()

    def _reset_unlocked(self) -> None:
        self._totals: dict[InvoiceType, Decimal] = {t: ZERO for t in InvoiceType}
        self._counts: dict[InvoiceType, int] = {t: 0 for t in InvoiceType}

    def snapshot(self) -> MetricsSnapshot:
        with self._lock:
            by_type = [
                TypeMetric(
                    invoice_type=invoice_type,
                    total=self._totals[invoice_type].quantize(Decimal("0.01")),
                    count=self._counts[invoice_type],
                )
                for invoice_type in InvoiceType
            ]
            grand_total = sum(self._totals.values(), ZERO).quantize(Decimal("0.01"))
            invoice_count = sum(self._counts.values())
        return MetricsSnapshot(
            by_type=by_type,
            grand_total=grand_total,
            invoice_count=invoice_count,
        )

    def apply_invoice(self, invoice_type: InvoiceType, total: Decimal) -> MetricsSnapshot:
        with self._lock:
            self._totals[invoice_type] += total
            self._counts[invoice_type] += 1
        return self.snapshot()

    def replace(self, rows: list[TypeMetric]) -> MetricsSnapshot:
        with self._lock:
            self._reset_unlocked()
            for row in rows:
                self._totals[row.invoice_type] = row.total
                self._counts[row.invoice_type] = row.count
        return self.snapshot()
