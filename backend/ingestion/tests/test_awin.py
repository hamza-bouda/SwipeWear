"""Tests for ingestion.sources.awin.AwinSource."""
from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock

import pytest

from ingestion.interfaces import Source
from ingestion.normalizer import normalize
from ingestion.sources.awin import AwinSource

# ── Fixtures ──────────────────────────────────────────────────────────────────

_PUBLISHER_ID = "99999"
_API_TOKEN = "test-awin-token"

_FAKE_ITEM: dict[str, Any] = {
    "product_id": "PROD-001",
    "merchant_id": "12345",
    "merchant_product_id": "MP-001",
    "product_name": "Nike Air Force 1 Blanc",
    "search_price": "89.99",
    "currency": "EUR",
    "brand_name": "Nike",
    "aw_image_url": "https://static.awin.com/img1.jpg",
    "aw_deep_link": (
        "https://www.awin1.com/cread.php"
        f"?awinaffid={_PUBLISHER_ID}&awinmid=12345&p=https%3A%2F%2Fexample.com%2Fprod"
    ),
    "category_name": "Chaussures",
    "merchant_name": "ExampleShop",
}

_FAKE_RESPONSE: dict[str, Any] = {"data": [_FAKE_ITEM]}


def _make_session(payload: dict[str, Any] = _FAKE_RESPONSE, status: int = 200) -> MagicMock:
    session = MagicMock()
    resp = MagicMock()
    resp.status_code = status
    resp.raise_for_status.return_value = None
    resp.json.return_value = payload
    session.get.return_value = resp
    return session


def _make_source(session: MagicMock | None = None) -> AwinSource:
    return AwinSource(
        api_token=_API_TOKEN,
        publisher_id=_PUBLISHER_ID,
        session=session or _make_session(),
    )


# ── Source Protocol ───────────────────────────────────────────────────────────

class TestSourceProtocol:
    def test_awin_source_satisfies_source_protocol(self) -> None:
        source: Source = _make_source()
        assert hasattr(source, "fetch")

    def test_fetch_returns_list(self) -> None:
        result = _make_source().fetch("baskets")
        assert isinstance(result, list)


# ── fetch() — champs mappés ───────────────────────────────────────────────────

class TestFetch:
    def test_item_id_built_from_merchant_and_product(self) -> None:
        result = _make_source().fetch("baskets")
        assert result[0]["item_id"] == "12345-PROD-001"

    def test_title_mapped(self) -> None:
        result = _make_source().fetch("baskets")
        assert result[0]["title"] == "Nike Air Force 1 Blanc"

    def test_price_mapped_as_float(self) -> None:
        result = _make_source().fetch("baskets")
        assert result[0]["price"] == 89.99

    def test_currency_mapped(self) -> None:
        result = _make_source().fetch("baskets")
        assert result[0]["currency"] == "EUR"

    def test_condition_always_new(self) -> None:
        result = _make_source().fetch("baskets")
        assert result[0]["condition"] == "new"

    def test_image_urls_mapped(self) -> None:
        result = _make_source().fetch("baskets")
        assert result[0]["image_urls"] == ["https://static.awin.com/img1.jpg"]

    def test_affiliate_url_from_aw_deep_link(self) -> None:
        result = _make_source().fetch("baskets")
        assert "awin1.com" in result[0]["listing_url"]
        assert _PUBLISHER_ID in result[0]["listing_url"]

    def test_source_field_is_awin(self) -> None:
        result = _make_source().fetch("baskets")
        assert result[0]["source"] == "awin"

    def test_brand_mapped(self) -> None:
        result = _make_source().fetch("baskets")
        assert result[0]["brand"] == "Nike"

    def test_category_mapped(self) -> None:
        result = _make_source().fetch("baskets")
        assert result[0]["category"] == "Chaussures"

    def test_empty_response_returns_empty_list(self) -> None:
        result = _make_source(session=_make_session({"data": []})).fetch("nothing")
        assert result == []


# ── Cas limites de _map_item ──────────────────────────────────────────────────

class TestMapItem:
    def test_price_with_comma_decimal_separator(self) -> None:
        item = {**_FAKE_ITEM, "search_price": "49,99"}
        result = AwinSource._map_item(item)
        assert result["price"] == 49.99

    def test_price_as_integer_string(self) -> None:
        result = AwinSource._map_item({**_FAKE_ITEM, "search_price": "50"})
        assert result["price"] == 50.0

    def test_missing_image_gives_empty_list(self) -> None:
        result = AwinSource._map_item({**_FAKE_ITEM, "aw_image_url": ""})
        assert result["image_urls"] == []

    def test_missing_brand_gives_none(self) -> None:
        result = AwinSource._map_item({**_FAKE_ITEM, "brand_name": ""})
        assert result["brand"] is None

    def test_currency_uppercased(self) -> None:
        result = AwinSource._map_item({**_FAKE_ITEM, "currency": "eur"})
        assert result["currency"] == "EUR"

    def test_item_id_fallback_to_product_id_only_when_no_merchant(self) -> None:
        item = {**_FAKE_ITEM, "merchant_id": None}
        result = AwinSource._map_item(item)
        assert result["item_id"] == "PROD-001"

    def test_merchant_product_id_used_as_fallback(self) -> None:
        item = {**_FAKE_ITEM, "product_id": None}
        result = AwinSource._map_item(item)
        assert "MP-001" in result["item_id"]


# ── Paramètres de requête ─────────────────────────────────────────────────────

class TestRequestParams:
    def test_keyword_sent_as_param(self) -> None:
        session = _make_session()
        _make_source(session).fetch("jean slim")
        call_kwargs = session.get.call_args
        assert call_kwargs.kwargs["params"]["keyword"] == "jean slim"

    def test_publisher_id_in_url(self) -> None:
        session = _make_session()
        _make_source(session).fetch("veste")
        url = session.get.call_args.args[0]
        assert _PUBLISHER_ID in url

    def test_default_limit_100(self) -> None:
        session = _make_session()
        _make_source(session).fetch("veste")
        assert session.get.call_args.kwargs["params"]["limit"] == 100

    def test_custom_limit_passed(self) -> None:
        session = _make_session()
        _make_source(session).fetch("veste", {"limit": 25})
        assert session.get.call_args.kwargs["params"]["limit"] == 25

    def test_limit_capped_at_1000(self) -> None:
        session = _make_session()
        _make_source(session).fetch("veste", {"limit": 9999})
        assert session.get.call_args.kwargs["params"]["limit"] == 1000

    def test_advertiser_id_filter(self) -> None:
        session = _make_session()
        _make_source(session).fetch("veste", {"advertiser_id": "777"})
        assert session.get.call_args.kwargs["params"]["advertiser_id"] == "777"

    def test_auth_header_set(self) -> None:
        session = _make_session()
        AwinSource(api_token=_API_TOKEN, publisher_id=_PUBLISHER_ID, session=session)
        session.headers.update.assert_called_with({
            "Authorization": f"Bearer {_API_TOKEN}",
            "Accept": "application/json",
        })

    def test_http_error_propagates(self) -> None:
        session = _make_session(status=401)
        resp = session.get.return_value
        resp.raise_for_status.side_effect = Exception("401 Unauthorized")
        with pytest.raises(Exception, match="401"):
            _make_source(session).fetch("veste")


# ── Critère d'acceptation principal : ProductRecord neuf avec affiliate_url ───

class TestNormalizeIntegration:
    def test_awin_item_normalizes_to_productrecord_condition_new_with_affiliate_url(
        self,
    ) -> None:
        from contracts.product import ProductCondition

        raw = _make_source().fetch("baskets")[0]
        record = normalize("awin", raw)

        assert record.condition == ProductCondition.new
        assert record.affiliate_url is not None
        assert "awin1.com" in record.affiliate_url

    def test_awin_item_normalizes_source_field(self) -> None:
        from contracts.product import ProductSource

        raw = _make_source().fetch("baskets")[0]
        record = normalize("awin", raw)
        assert record.source == ProductSource.awin

    def test_awin_item_normalizes_brand(self) -> None:
        raw = _make_source().fetch("baskets")[0]
        record = normalize("awin", raw)
        assert record.brand == "Nike"
