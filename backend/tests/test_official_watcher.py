from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from scripts.watch_official_sources import _active_alert_queries, _build_sources


def test_official_watcher_rejects_vinted_source() -> None:
    with pytest.raises(ValueError, match="Vinted is isolated"):
        _build_sources(["vinted"])


def test_active_alert_queries_keep_max_price_filter() -> None:
    conn = MagicMock()
    conn.cursor.return_value.__enter__.return_value.fetchall.return_value = [
        ("vintage jacket", {"max_price_eur": 90, "sizes": ["M"]}),
        ("sneakers", "{\"sizes\": [\"42\"]}"),
    ]

    assert _active_alert_queries(conn) == [
        ("vintage jacket", {"limit": 20, "max_price": 90}),
        ("sneakers", {"limit": 20}),
    ]


def test_build_sources_uses_only_configured_official_connectors() -> None:
    with patch("scripts.watch_official_sources.EbaySource") as ebay:
        assert list(_build_sources(["ebay"])) == ["ebay"]
        ebay.assert_called_once_with()
