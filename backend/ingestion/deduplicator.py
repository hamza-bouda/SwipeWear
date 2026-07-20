"""Cross-source deduplication of ProductRecord lists.

Fingerprint: (brand, model, size_eu, condition).
On collision: keep cheapest, mark others available=False.
Products with no brand AND no model are treated as unique (no fingerprint match)
to avoid false deduplication of unidentified items.
"""
from __future__ import annotations

from contracts.product import ProductRecord


def _fingerprint(record: ProductRecord) -> tuple:
    brand = (record.brand or "").lower().strip()
    model = (record.model or "").lower().strip()
    if not brand and not model:
        # Cannot reliably identify this product — keep it unique
        return ("__unique__", record.id)
    return (brand, model, record.size_eu or "", record.condition.value)


def deduplicate(records: list[ProductRecord]) -> list[ProductRecord]:
    """Group records by fingerprint; keep cheapest per group, mark rest unavailable.

    Returns a new list — original records are never mutated.
    Order within each group: cheapest first (available=True), rest available=False.
    """
    groups: dict[tuple, list[ProductRecord]] = {}
    for rec in records:
        fp = _fingerprint(rec)
        groups.setdefault(fp, []).append(rec)

    result: list[ProductRecord] = []
    for fp, group in groups.items():
        if len(group) == 1:
            result.append(group[0])
        else:
            by_price = sorted(group, key=lambda r: r.price)
            result.append(by_price[0])
            for dup in by_price[1:]:
                result.append(dup.model_copy(update={"available": False}))
    return result
