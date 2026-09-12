"""Server-side enrichment for mobile interaction events."""
from __future__ import annotations

from decimal import Decimal
from unittest.mock import MagicMock

from api.routers.events import _load_product_signals


def _connection(row):
    cursor = MagicMock()
    cursor.fetchone.return_value = row
    cursor.__enter__ = lambda self: self
    cursor.__exit__ = MagicMock(return_value=False)
    connection = MagicMock()
    connection.cursor.return_value = cursor
    return connection


def test_loads_embedding_brand_and_price_for_mobile_swipes() -> None:
    signals = _load_product_signals(
        _connection(("[0.1, 0.2]", "Carhartt", Decimal("89.50"))),
        "product-1",
    )

    assert signals["product_embedding"] == [0.1, 0.2]
    assert signals["brand"] == "Carhartt"
    assert signals["product_price_eur"] == 89.5


def test_missing_embedding_keeps_metadata_available() -> None:
    signals = _load_product_signals(
        _connection((None, "Nike", Decimal("65.00"))),
        "product-2",
    )

    assert signals["product_embedding"] is None
    assert signals["brand"] == "Nike"
    assert signals["product_price_eur"] == 65.0
