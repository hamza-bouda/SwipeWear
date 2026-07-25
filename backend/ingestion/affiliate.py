"""Affiliate URL builder — transforms raw product URLs into tracked affiliate links.

Each source has its own URL format. Credentials are read from environment
variables (never hardcoded — CLAUDE.md §6, §8).

Supported sources:
    ebay — eBay Partner Network (EPN) query-param format
    awin — Awin deep link with publisher ID
    cj   — CJ Affiliate deep link with publisher ID
"""
from __future__ import annotations

import logging
import os
from enum import Enum
from urllib.parse import quote, urlencode

from contracts.product import ProductRecord, ProductSource

_LOG = logging.getLogger("swipewear.ingestion.affiliate")


class ClickContext(str, Enum):
    feed = "feed"
    ladder = "ladder"
    detail = "detail"


_TRUTHY = {"1", "true", "yes", "on"}


def _affiliate_enabled() -> bool:
    """Whether outgoing links should be wrapped for affiliate tracking.

    Off by default: the credentials being present in the environment is not the
    same as the programme being live, and a deep link built against a
    programme that has not approved the account yet is a broken link for the
    user. Set AFFILIATE_LINKS_ENABLED=true once each network is confirmed.
    """
    return os.environ.get("AFFILIATE_LINKS_ENABLED", "").strip().lower() in _TRUTHY


def _get_env(key: str) -> str | None:
    return os.environ.get(key)


def _build_ebay_epn_url(
    product: ProductRecord,
    context: ClickContext,
) -> str:
    mkrid = _get_env("EPN_PROGRAM_ID")
    campaign_id = _get_env("EPN_CAMPAIGN_ID")

    if not mkrid or not campaign_id:
        _LOG.warning("EPN credentials missing, returning raw URL for %s", product.id)
        return product.affiliate_url or ""

    listing_url = product.affiliate_url or ""
    custom_id = f"sw-{context.value}-{product.id}"

    params = {
        "mkcid": "1",
        "mkrid": mkrid,
        "siteid": "0",
        "campid": campaign_id,
        "customid": custom_id,
        "toolid": "10001",
        "mkevt": "1",
    }
    return f"{listing_url}?{urlencode(params)}" if listing_url else ""


def _build_awin_deep_link(
    product: ProductRecord,
    context: ClickContext,
) -> str:
    publisher_id = _get_env("AWIN_PUBLISHER_ID")

    if not publisher_id:
        _LOG.warning("AWIN_PUBLISHER_ID missing, returning raw URL for %s", product.id)
        return product.affiliate_url or ""

    destination = product.affiliate_url or ""
    custom_id = f"sw-{context.value}-{product.id}"

    params = {
        "awinmid": "",
        "awinaffid": publisher_id,
        "clickref": custom_id,
        "ued": destination,
    }
    return f"https://www.awin1.com/cread.php?{urlencode(params)}"


def _build_cj_deep_link(
    product: ProductRecord,
    context: ClickContext,
) -> str:
    publisher_id = _get_env("CJ_PUBLISHER_ID")

    if not publisher_id:
        _LOG.warning("CJ_PUBLISHER_ID missing, returning raw URL for %s", product.id)
        return product.affiliate_url or ""

    destination = product.affiliate_url or ""
    custom_id = f"sw-{context.value}-{product.id}"

    return (
        f"https://www.anrdoezrs.net/links/{publisher_id}/type/dlg/"
        f"sid/{custom_id}/{quote(destination, safe='')}"
    )


_BUILDERS = {
    ProductSource.ebay: _build_ebay_epn_url,
    ProductSource.awin: _build_awin_deep_link,
    ProductSource.cj: _build_cj_deep_link,
}


def build_affiliate_url(
    product: ProductRecord,
    context: ClickContext = ClickContext.ladder,
) -> str:
    if not _affiliate_enabled():
        return product.affiliate_url or ""

    builder = _BUILDERS.get(product.source)
    if builder is None:
        _LOG.info(
            "No affiliate program for source %s, returning raw URL",
            product.source.value,
        )
        return product.affiliate_url or ""

    return builder(product, context)


def is_monetized(product: ProductRecord) -> bool:
    if not _affiliate_enabled():
        return False
    if product.source == ProductSource.ebay:
        return bool(_get_env("EPN_PROGRAM_ID") and _get_env("EPN_CAMPAIGN_ID"))
    if product.source == ProductSource.awin:
        return bool(_get_env("AWIN_PUBLISHER_ID"))
    if product.source == ProductSource.cj:
        return bool(_get_env("CJ_PUBLISHER_ID"))
    return False
