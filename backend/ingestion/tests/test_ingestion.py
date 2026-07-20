"""Tests for ingestion.interfaces.Source and ingestion.sources.ebay.EbaySource."""
from __future__ import annotations

import json
from typing import Any
from unittest.mock import MagicMock, call, patch

import pytest

from ingestion.interfaces import Source
from ingestion.sources.ebay import EbaySource, _CONDITION_MAP, _DAILY_LIMIT


# ── Fixtures ──────────────────────────────────────────────────────────────────

_FAKE_TOKEN_RESP = {
    "access_token": "test-token-abc",
    "expires_in": 7200,
}

_FAKE_ITEM = {
    "itemId": "v1|123456|0",
    "title": "Nike Air Max 90 Taille 42",
    "price": {"value": "89.99", "currency": "EUR"},
    "condition": "USED",
    "thumbnailImages": [{"imageUrl": "https://i.ebayimg.com/img1.jpg"}],
    "itemWebUrl": "https://www.ebay.fr/itm/123456",
}

_FAKE_SEARCH_RESP = {"itemSummaries": [_FAKE_ITEM]}


def _make_session(
    token_payload: dict[str, Any] = _FAKE_TOKEN_RESP,
    search_payload: dict[str, Any] = _FAKE_SEARCH_RESP,
    search_status: int = 200,
) -> MagicMock:
    """Build a mock requests.Session."""
    session = MagicMock()

    token_resp = MagicMock()
    token_resp.raise_for_status.return_value = None
    token_resp.json.return_value = token_payload

    search_resp = MagicMock()
    search_resp.status_code = search_status
    search_resp.raise_for_status.return_value = None
    search_resp.json.return_value = search_payload
    search_resp.headers = {}

    session.post.return_value = token_resp
    session.get.return_value = search_resp
    return session


def _make_source(session: MagicMock | None = None) -> EbaySource:
    return EbaySource(
        client_id="fake-id",
        client_secret="fake-secret",
        env="sandbox",
        session=session or _make_session(),
    )


# ── Source Protocol ───────────────────────────────────────────────────────────

class TestSourceProtocol:
    def test_source_is_a_protocol(self):
        import typing
        assert getattr(Source, "__protocol_attrs__", None) is not None or (
            hasattr(Source, "fetch")
        )

    def test_ebay_source_structurally_satisfies_source(self):
        src = _make_source()
        assert hasattr(src, "fetch")
        assert callable(src.fetch)

    def test_source_fetch_signature_matches(self):
        import inspect
        sig = inspect.signature(Source.fetch)
        params = list(sig.parameters)
        assert "query" in params
        assert "filters" in params


# ── EbaySource.fetch ──────────────────────────────────────────────────────────

class TestEbaySourceFetch:
    def test_fetch_returns_list(self):
        src = _make_source()
        result = src.fetch("nike air max")
        assert isinstance(result, list)

    def test_fetch_returns_non_empty_list(self):
        src = _make_source()
        result = src.fetch("nike air max")
        assert len(result) == 1

    def test_fetch_result_contains_required_fields(self):
        src = _make_source()
        item = src.fetch("nike air max")[0]
        required = {"item_id", "title", "price", "currency", "condition",
                    "image_urls", "listing_url", "source"}
        assert required <= item.keys()

    def test_fetch_maps_item_id(self):
        src = _make_source()
        item = src.fetch("nike")[0]
        assert item["item_id"] == "v1|123456|0"

    def test_fetch_maps_title(self):
        src = _make_source()
        item = src.fetch("nike")[0]
        assert item["title"] == "Nike Air Max 90 Taille 42"

    def test_fetch_maps_price_as_float(self):
        src = _make_source()
        item = src.fetch("nike")[0]
        assert item["price"] == 89.99
        assert isinstance(item["price"], float)

    def test_fetch_maps_currency(self):
        src = _make_source()
        item = src.fetch("nike")[0]
        assert item["currency"] == "EUR"

    def test_fetch_maps_condition(self):
        src = _make_source()
        item = src.fetch("nike")[0]
        assert item["condition"] == "good"

    def test_fetch_maps_image_urls(self):
        src = _make_source()
        item = src.fetch("nike")[0]
        assert item["image_urls"] == ["https://i.ebayimg.com/img1.jpg"]

    def test_fetch_maps_listing_url(self):
        src = _make_source()
        item = src.fetch("nike")[0]
        assert item["listing_url"] == "https://www.ebay.fr/itm/123456"

    def test_fetch_maps_source_name(self):
        src = _make_source()
        item = src.fetch("nike")[0]
        assert item["source"] == "ebay"

    def test_fetch_empty_result_on_no_items(self):
        session = _make_session(search_payload={"itemSummaries": []})
        src = _make_source(session)
        assert src.fetch("zzz-no-match") == []

    def test_fetch_result_has_no_items_key_missing(self):
        session = _make_session(search_payload={})
        src = _make_source(session)
        assert src.fetch("zzz") == []


# ── Condition mapping ─────────────────────────────────────────────────────────

class TestConditionMapping:
    @pytest.mark.parametrize("ebay_cond,expected", [
        ("NEW", "new"),
        ("LIKE_NEW", "like_new"),
        ("VERY_GOOD", "like_new"),
        ("GOOD", "good"),
        ("USED", "good"),
        ("ACCEPTABLE", "fair"),
        ("FOR_PARTS_OR_NOT_WORKING", "fair"),
        ("UNKNOWN_CONDITION", "fair"),
    ])
    def test_condition_map(self, ebay_cond: str, expected: str):
        item = {**_FAKE_ITEM, "condition": ebay_cond}
        session = _make_session(search_payload={"itemSummaries": [item]})
        src = _make_source(session)
        result = src.fetch("test")[0]
        assert result["condition"] == expected


# ── Image fallback ────────────────────────────────────────────────────────────

class TestImageFallback:
    def test_uses_image_field_when_no_thumbnail(self):
        item = {
            **_FAKE_ITEM,
            "thumbnailImages": None,
            "image": {"imageUrl": "https://img.fallback.com/x.jpg"},
        }
        session = _make_session(search_payload={"itemSummaries": [item]})
        result = _make_source(session).fetch("test")[0]
        assert result["image_urls"] == ["https://img.fallback.com/x.jpg"]

    def test_empty_list_when_no_images(self):
        item = {k: v for k, v in _FAKE_ITEM.items()
                if k not in ("thumbnailImages", "image")}
        session = _make_session(search_payload={"itemSummaries": [item]})
        result = _make_source(session).fetch("test")[0]
        assert result["image_urls"] == []


# ── Rate limiting & 429 handling ──────────────────────────────────────────────

class TestRateLimiting:
    def test_429_retried_and_succeeds(self):
        session = MagicMock()

        token_resp = MagicMock()
        token_resp.raise_for_status.return_value = None
        token_resp.json.return_value = _FAKE_TOKEN_RESP
        session.post.return_value = token_resp

        resp_429 = MagicMock()
        resp_429.status_code = 429
        resp_429.headers = {"Retry-After": "0"}

        resp_200 = MagicMock()
        resp_200.status_code = 200
        resp_200.raise_for_status.return_value = None
        resp_200.json.return_value = _FAKE_SEARCH_RESP

        session.get.side_effect = [resp_429, resp_200]

        with patch("ingestion.sources.ebay.time.sleep"):
            result = _make_source(session).fetch("nike")

        assert len(result) == 1
        assert session.get.call_count == 2

    def test_429_all_retries_exhausted_raises(self):
        session = MagicMock()

        token_resp = MagicMock()
        token_resp.raise_for_status.return_value = None
        token_resp.json.return_value = _FAKE_TOKEN_RESP
        session.post.return_value = token_resp

        resp_429 = MagicMock()
        resp_429.status_code = 429
        resp_429.headers = {"Retry-After": "0"}
        session.get.return_value = resp_429

        with patch("ingestion.sources.ebay.time.sleep"):
            with pytest.raises(RuntimeError, match="429"):
                _make_source(session).fetch("nike")

    def test_daily_limit_warning_logged(self, caplog):
        import logging
        src = _make_source()
        src._daily_calls = _DAILY_LIMIT - 1

        with caplog.at_level(logging.WARNING, logger="swipewear.ingestion.ebay"):
            src.fetch("nike")

        assert any("daily call limit" in r.message for r in caplog.records)


# ── Invalid env ───────────────────────────────────────────────────────────────

class TestInvalidConfig:
    def test_invalid_env_raises_value_error(self):
        with pytest.raises(ValueError, match="EBAY_ENV"):
            EbaySource(
                client_id="x", client_secret="y", env="staging"
            )
