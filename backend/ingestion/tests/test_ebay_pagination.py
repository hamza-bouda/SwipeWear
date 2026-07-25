"""Tests for eBay paging and image-resolution handling — KAN-87.

Without paging the connector could only ever return the first 200 hits of a
query, which capped the whole catalogue; and it passed eBay's s-l225 thumbnails
straight to FashionSigLIP, whose 224 px input they do not even fill.
"""
from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock

import pytest

from ingestion.sources.ebay import (
    MAX_OFFSET,
    EbaySource,
    _upgrade_image_url,
)

_FAKE_TOKEN_RESP = {"access_token": "test-token-abc", "expires_in": 7200}


def _make_session(search_payload: dict[str, Any]) -> MagicMock:
    session = MagicMock()

    token_resp = MagicMock()
    token_resp.raise_for_status.return_value = None
    token_resp.json.return_value = _FAKE_TOKEN_RESP

    search_resp = MagicMock()
    search_resp.status_code = 200
    search_resp.raise_for_status.return_value = None
    search_resp.json.return_value = search_payload
    search_resp.headers = {}

    session.post.return_value = token_resp
    session.get.return_value = search_resp
    return session


def _make_source(session: MagicMock) -> EbaySource:
    return EbaySource(
        client_id="fake-id",
        client_secret="fake-secret",
        env="sandbox",
        session=session,
    )


def _sent_params(session: MagicMock) -> dict[str, Any]:
    return session.get.call_args.kwargs["params"]


class TestOffsetPaging:
    def test_offset_is_forwarded_to_the_api(self):
        session = _make_session({"itemSummaries": []})
        _make_source(session).fetch("sneakers", {"limit": 200, "offset": 400})
        assert _sent_params(session)["offset"] == 400

    def test_offset_is_omitted_when_zero(self):
        """eBay treats a missing offset as 0; sending it adds noise."""
        session = _make_session({"itemSummaries": []})
        _make_source(session).fetch("sneakers", {"limit": 200})
        assert "offset" not in _sent_params(session)

    def test_limit_is_capped_at_the_api_maximum(self):
        session = _make_session({"itemSummaries": []})
        _make_source(session).fetch("sneakers", {"limit": 5_000})
        assert _sent_params(session)["limit"] == 200

    def test_paging_past_the_cap_raises_before_calling_the_api(self):
        """Past 10 000 eBay errors out; a bulk run must fail loudly, not
        silently record an empty page and mark the query exhausted."""
        session = _make_session({"itemSummaries": []})
        with pytest.raises(ValueError, match="10000"):
            _make_source(session).fetch(
                "sneakers", {"limit": 200, "offset": MAX_OFFSET},
            )
        session.get.assert_not_called()


class TestImageResolution:
    @pytest.mark.parametrize("variant", ["s-l225", "s-l64", "s-l1600"])
    def test_any_variant_is_rewritten_to_the_configured_size(self, variant):
        url = f"https://i.ebayimg.com/images/g/abc/{variant}.jpg"
        assert _upgrade_image_url(url).endswith("/s-l500.jpg")

    def test_non_ebay_urls_are_left_alone(self):
        url = "https://example.com/photo.jpg"
        assert _upgrade_image_url(url) == url

    def test_fetch_returns_upgraded_image_urls(self):
        session = _make_session({"itemSummaries": [{
            "itemId": "v1|1|0",
            "title": "Nike Air Max",
            "price": {"value": "50.00", "currency": "EUR"},
            "condition": "USED",
            "image": {"imageUrl": "https://i.ebayimg.com/images/g/a/s-l225.jpg"},
            "itemWebUrl": "https://www.ebay.fr/itm/1",
        }]})
        items = _make_source(session).fetch("nike")
        assert items[0]["image_urls"] == [
            "https://i.ebayimg.com/images/g/a/s-l500.jpg"
        ]
