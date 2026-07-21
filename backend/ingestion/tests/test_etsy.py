"""Tests for the Etsy Open API v3 connector."""
from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from ingestion.sources.etsy import EtsySource


def _fake_listing(
    listing_id: int = 123456,
    title: str = "Vintage Levi's 501 Jeans",
    amount: int = 4500,
    currency: str = "USD",
    is_vintage: bool = True,
) -> dict:
    return {
        "listing_id": listing_id,
        "title": title,
        "price": {"amount": amount, "divisor": 100, "currency_code": currency},
        "is_vintage": is_vintage,
        "when_made": "1990s" if is_vintage else "2024",
        "tags": ["vintage", "denim", "jeans"],
        "taxonomy_path": ["Clothing", "Pants & Capris", "Jeans"],
        "images": [
            {"url_fullxfull": "https://i.etsystatic.com/full1.jpg", "url_570xN": ""},
            {"url_fullxfull": "https://i.etsystatic.com/full2.jpg", "url_570xN": ""},
        ],
        "shop": {"shop_name": "VintageFinds"},
    }


def _mock_session(results: list[dict]) -> MagicMock:
    session = MagicMock()
    resp = MagicMock()
    resp.status_code = 200
    resp.json.return_value = {"results": results}
    resp.raise_for_status = MagicMock()
    session.get.return_value = resp
    return session


class TestEtsySource:
    def test_fetch_returns_mapped_items(self):
        listing = _fake_listing()
        session = _mock_session([listing])
        source = EtsySource(api_key="test-key", session=session)

        items = source.fetch("vintage jeans")

        assert len(items) == 1
        item = items[0]
        assert item["item_id"] == "123456"
        assert item["title"] == "Vintage Levi's 501 Jeans"
        assert item["price"] == 45.0
        assert item["currency"] == "USD"
        assert item["source"] == "etsy"
        assert item["condition"] == "good"
        assert len(item["image_urls"]) == 2

    def test_vintage_item_has_good_condition(self):
        listing = _fake_listing(is_vintage=True)
        session = _mock_session([listing])
        source = EtsySource(api_key="test-key", session=session)

        items = source.fetch("vintage")
        assert items[0]["condition"] == "good"

    def test_non_vintage_recent_has_like_new_condition(self):
        listing = _fake_listing(is_vintage=False)
        listing["when_made"] = "2024"
        session = _mock_session([listing])
        source = EtsySource(api_key="test-key", session=session)

        items = source.fetch("new jeans")
        assert items[0]["condition"] == "like_new"

    def test_listing_url_format(self):
        listing = _fake_listing(listing_id=999)
        session = _mock_session([listing])
        source = EtsySource(api_key="test-key", session=session)

        items = source.fetch("test")
        assert items[0]["listing_url"] == "https://www.etsy.com/listing/999"

    def test_empty_results(self):
        session = _mock_session([])
        source = EtsySource(api_key="test-key", session=session)

        items = source.fetch("nonexistent")
        assert items == []

    def test_price_calculation_with_divisor(self):
        listing = _fake_listing(amount=12999, currency="EUR")
        session = _mock_session([listing])
        source = EtsySource(api_key="test-key", session=session)

        items = source.fetch("test")
        assert items[0]["price"] == 129.99
        assert items[0]["currency"] == "EUR"

    def test_brand_from_shop_name(self):
        listing = _fake_listing()
        session = _mock_session([listing])
        source = EtsySource(api_key="test-key", session=session)

        items = source.fetch("test")
        assert items[0]["brand"] == "VintageFinds"

    def test_category_from_taxonomy_path(self):
        listing = _fake_listing()
        session = _mock_session([listing])
        source = EtsySource(api_key="test-key", session=session)

        items = source.fetch("test")
        assert items[0]["category"] == "Jeans"

    def test_retry_on_429(self):
        session = MagicMock()
        resp_429 = MagicMock()
        resp_429.status_code = 429
        resp_429.headers = {"Retry-After": "0"}
        resp_ok = MagicMock()
        resp_ok.status_code = 200
        resp_ok.json.return_value = {"results": [_fake_listing()]}
        resp_ok.raise_for_status = MagicMock()
        session.get.side_effect = [resp_429, resp_ok]

        source = EtsySource(api_key="test-key", session=session)
        items = source.fetch("test")
        assert len(items) == 1
        assert session.get.call_count == 2

    def test_api_key_in_session_headers(self):
        session = _mock_session([])
        EtsySource(api_key="my-key", session=session)
        session.headers.update.assert_called_with({
            "x-api-key": "my-key",
            "Accept": "application/json",
        })
