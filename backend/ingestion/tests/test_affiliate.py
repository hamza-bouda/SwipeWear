"""Tests for affiliate URL builder — KAN-56."""
from __future__ import annotations

import os
from unittest.mock import patch

from contracts.product import ProductCondition, ProductRecord, ProductSource

from ingestion.affiliate import (
    ClickContext,
    build_affiliate_url,
    is_monetized,
)


def _product(
    source: ProductSource = ProductSource.ebay,
    product_id: str = "prod-1",
    affiliate_url: str = "https://www.ebay.com/itm/123456",
) -> ProductRecord:
    return ProductRecord(
        id=product_id,
        source=source,
        source_record_id=f"{source.value}-{product_id}",
        title="Nike Air Force 1",
        price=65.0,
        currency="EUR",
        condition=ProductCondition.good,
        category="sneakers",
        image_urls=["https://example.com/img.jpg"],
        affiliate_url=affiliate_url,
    )


# Affiliate wrapping is opt-in (AFFILIATE_LINKS_ENABLED), so every test that
# exercises a deep-link builder has to turn it on explicitly.
_ON = {"AFFILIATE_LINKS_ENABLED": "true"}

_EPN_ENV = {
    **_ON,
    "EPN_PROGRAM_ID": "5338",
    "EPN_CAMPAIGN_ID": "1234567890",
}

_AWIN_ENV = {
    **_ON,
    "AWIN_PUBLISHER_ID": "999888",
}

_CJ_ENV = {
    **_ON,
    "CJ_PUBLISHER_ID": "7654321",
}


# ── eBay EPN ─────────────────────────────────────────────────────────────────

class TestEbayAffiliateUrl:
    @patch.dict(os.environ, _EPN_ENV)
    def test_contains_mkrid(self) -> None:
        url = build_affiliate_url(_product(), ClickContext.feed)
        assert "mkrid=5338" in url

    @patch.dict(os.environ, _EPN_ENV)
    def test_contains_campaign_id(self) -> None:
        url = build_affiliate_url(_product(), ClickContext.feed)
        assert "campid=1234567890" in url

    @patch.dict(os.environ, _EPN_ENV)
    def test_contains_custom_id_with_context(self) -> None:
        url = build_affiliate_url(_product(), ClickContext.ladder)
        assert "sw-ladder-prod-1" in url

    @patch.dict(os.environ, _EPN_ENV)
    def test_appends_params_to_listing_url(self) -> None:
        url = build_affiliate_url(_product(), ClickContext.detail)
        assert url.startswith("https://www.ebay.com/itm/123456?")

    @patch.dict(os.environ, _EPN_ENV)
    def test_contains_mkevt(self) -> None:
        url = build_affiliate_url(_product(), ClickContext.feed)
        assert "mkevt=1" in url

    @patch.dict(os.environ, _EPN_ENV)
    def test_contains_mkcid(self) -> None:
        url = build_affiliate_url(_product(), ClickContext.feed)
        assert "mkcid=1" in url

    def test_returns_raw_url_without_credentials(self) -> None:
        with patch.dict(os.environ, {}, clear=True):
            url = build_affiliate_url(_product(), ClickContext.feed)
        assert url == "https://www.ebay.com/itm/123456"


# ── Awin ─────────────────────────────────────────────────────────────────────

class TestAwinAffiliateUrl:
    @patch.dict(os.environ, _AWIN_ENV)
    def test_contains_publisher_id(self) -> None:
        url = build_affiliate_url(
            _product(ProductSource.awin, affiliate_url="https://shop.example.com/item/1"),
            ClickContext.ladder,
        )
        assert "999888" in url

    @patch.dict(os.environ, _AWIN_ENV)
    def test_contains_awin_domain(self) -> None:
        url = build_affiliate_url(
            _product(ProductSource.awin),
            ClickContext.feed,
        )
        assert "awin1.com" in url

    @patch.dict(os.environ, _AWIN_ENV)
    def test_contains_custom_id(self) -> None:
        url = build_affiliate_url(
            _product(ProductSource.awin, product_id="awin-42"),
            ClickContext.detail,
        )
        assert "sw-detail-awin-42" in url

    def test_returns_raw_url_without_credentials(self) -> None:
        with patch.dict(os.environ, {}, clear=True):
            p = _product(ProductSource.awin, affiliate_url="https://shop.example.com/x")
            url = build_affiliate_url(p, ClickContext.feed)
        assert url == "https://shop.example.com/x"


# ── CJ ───────────────────────────────────────────────────────────────────────

class TestCjAffiliateUrl:
    @patch.dict(os.environ, _CJ_ENV)
    def test_contains_publisher_id(self) -> None:
        url = build_affiliate_url(
            _product(ProductSource.cj, affiliate_url="https://brand.example.com/p/1"),
            ClickContext.ladder,
        )
        assert "7654321" in url

    @patch.dict(os.environ, _CJ_ENV)
    def test_contains_custom_id(self) -> None:
        url = build_affiliate_url(
            _product(ProductSource.cj, product_id="cj-99"),
            ClickContext.feed,
        )
        assert "sw-feed-cj-99" in url

    def test_returns_raw_url_without_credentials(self) -> None:
        with patch.dict(os.environ, {}, clear=True):
            p = _product(ProductSource.cj, affiliate_url="https://brand.example.com/y")
            url = build_affiliate_url(p, ClickContext.feed)
        assert url == "https://brand.example.com/y"


# ── Click context encoding ──────────────────────────────────────────────────

class TestClickContext:
    @patch.dict(os.environ, _EPN_ENV)
    def test_feed_context(self) -> None:
        url = build_affiliate_url(_product(), ClickContext.feed)
        assert "sw-feed-" in url

    @patch.dict(os.environ, _EPN_ENV)
    def test_ladder_context(self) -> None:
        url = build_affiliate_url(_product(), ClickContext.ladder)
        assert "sw-ladder-" in url

    @patch.dict(os.environ, _EPN_ENV)
    def test_detail_context(self) -> None:
        url = build_affiliate_url(_product(), ClickContext.detail)
        assert "sw-detail-" in url


# ── is_monetized ─────────────────────────────────────────────────────────────

class TestIsMonetized:
    @patch.dict(os.environ, _EPN_ENV)
    def test_ebay_monetized_with_credentials(self) -> None:
        assert is_monetized(_product()) is True

    def test_ebay_not_monetized_without_credentials(self) -> None:
        with patch.dict(os.environ, {}, clear=True):
            assert is_monetized(_product()) is False

    @patch.dict(os.environ, _AWIN_ENV)
    def test_awin_monetized(self) -> None:
        assert is_monetized(_product(ProductSource.awin)) is True

    @patch.dict(os.environ, _CJ_ENV)
    def test_cj_monetized(self) -> None:
        assert is_monetized(_product(ProductSource.cj)) is True


# ── Kill switch ──────────────────────────────────────────────────────────────

class TestAffiliateDisabled:
    """Affiliate wrapping is opt-in.

    Credentials sitting in the environment do not mean the programme has
    approved the account; a deep link built against a pending programme is a
    dead link for the user. Direct seller URLs are the safe default.
    """

    @patch.dict(os.environ, {**_EPN_ENV, "AFFILIATE_LINKS_ENABLED": "false"})
    def test_returns_the_raw_listing_url(self) -> None:
        product = _product(affiliate_url="https://www.ebay.fr/itm/123")
        assert build_affiliate_url(product, ClickContext.feed) == (
            "https://www.ebay.fr/itm/123"
        )

    @patch.dict(os.environ, _EPN_ENV)
    def test_enabled_flag_restores_tracking(self) -> None:
        product = _product(affiliate_url="https://www.ebay.fr/itm/123")
        assert "campid" in build_affiliate_url(product, ClickContext.feed)

    @patch.dict(os.environ, {**_EPN_ENV, "AFFILIATE_LINKS_ENABLED": "false"})
    def test_is_monetized_is_false_when_disabled(self) -> None:
        assert is_monetized(_product()) is False

    def test_disabled_by_default(self) -> None:
        """No AFFILIATE_LINKS_ENABLED set at all must not wrap."""
        env = {k: v for k, v in _EPN_ENV.items() if k != "AFFILIATE_LINKS_ENABLED"}
        with patch.dict(os.environ, env, clear=False):
            os.environ.pop("AFFILIATE_LINKS_ENABLED", None)
            product = _product(affiliate_url="https://www.ebay.fr/itm/123")
            assert build_affiliate_url(product) == "https://www.ebay.fr/itm/123"
