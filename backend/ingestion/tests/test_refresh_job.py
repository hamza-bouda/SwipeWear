"""Tests for ingestion.refresh_job — run_refresh(store, fresh_records) -> JobResult."""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, call

import pytest

from contracts.product import ProductCondition, ProductRecord, ProductSource
from ingestion.refresh_job import JobResult, _REMOVE_AFTER, run_refresh

# ── Helpers ───────────────────────────────────────────────────────────────────

_IMG = ["https://img.example.com/a.jpg"]
_NOW = datetime(2026, 7, 20, 12, 0, 0, tzinfo=timezone.utc)


def _rec(
    record_id: str = "ebay-001",
    source: ProductSource = ProductSource.ebay,
    brand: str | None = "Nike",
    model: str | None = "Air Force 1",
    size_eu: str | None = "42",
    price: float = 80.0,
    available: bool = True,
) -> ProductRecord:
    return ProductRecord(
        id=record_id,
        source=source,
        source_record_id=record_id.split("-", 1)[-1],
        title="Nike Air Force 1",
        brand=brand,
        model=model,
        size_eu=size_eu,
        condition=ProductCondition.good,
        price=price,
        currency="EUR",
        category="sneakers",
        image_urls=_IMG,
        available=available,
    )


def _store(unavailable_since: list[ProductRecord] | None = None) -> MagicMock:
    store = MagicMock()
    store.get_unavailable_since.return_value = unavailable_since or []
    return store


# ── JobResult counts ──────────────────────────────────────────────────────────

class TestJobResultCounts:
    def test_no_duplicates_no_removal_counts(self) -> None:
        recs = [_rec("ebay-001", brand="Nike"), _rec("ebay-002", brand="Adidas")]
        result = run_refresh(_store(), recs, now=_NOW)
        assert result.updated == 2
        assert result.deduplicated == 0
        assert result.removed == 0

    def test_one_duplicate_counted(self) -> None:
        ebay = _rec("ebay-001", price=100.0)
        awin = _rec("awin-001", source=ProductSource.awin, price=80.0)
        result = run_refresh(_store(), [ebay, awin], now=_NOW)
        assert result.updated == 1
        assert result.deduplicated == 1

    def test_removed_count_matches_store_return(self) -> None:
        old_recs = [_rec("ebay-old", available=False)]
        result = run_refresh(_store(old_recs), [_rec("ebay-001")], now=_NOW)
        assert result.removed == 1

    def test_empty_records_all_counts_zero(self) -> None:
        result = run_refresh(_store(), [], now=_NOW)
        assert result.updated == 0
        assert result.deduplicated == 0
        assert result.removed == 0


# ── Store interactions ────────────────────────────────────────────────────────

class TestStoreInteractions:
    def test_upsert_all_called_with_all_records(self) -> None:
        store = _store()
        recs = [_rec("ebay-001"), _rec("ebay-002", brand="Adidas")]
        run_refresh(store, recs, now=_NOW)
        store.upsert_all.assert_called_once()
        upserted = store.upsert_all.call_args.args[0]
        assert len(upserted) == 2

    def test_mark_unavailable_called_for_duplicate(self) -> None:
        store = _store()
        ebay = _rec("ebay-001", price=100.0)
        awin = _rec("awin-001", source=ProductSource.awin, price=80.0)
        run_refresh(store, [ebay, awin], now=_NOW)
        store.mark_unavailable.assert_called_once_with("ebay-001")

    def test_mark_unavailable_not_called_when_no_duplicates(self) -> None:
        store = _store()
        run_refresh(store, [_rec("ebay-001")], now=_NOW)
        store.mark_unavailable.assert_not_called()

    def test_remove_from_index_called_for_old_unavailable(self) -> None:
        store = _store(unavailable_since=[_rec("ebay-old", available=False)])
        run_refresh(store, [_rec("ebay-001")], now=_NOW)
        store.remove_from_index.assert_called_once_with("ebay-old")

    def test_get_unavailable_since_called_with_7day_cutoff(self) -> None:
        store = _store()
        run_refresh(store, [], now=_NOW)
        expected_cutoff = _NOW - _REMOVE_AFTER
        store.get_unavailable_since.assert_called_once_with(expected_cutoff)

    def test_remove_not_called_when_no_old_unavailable(self) -> None:
        store = _store(unavailable_since=[])
        run_refresh(store, [_rec("ebay-001")], now=_NOW)
        store.remove_from_index.assert_not_called()


# ── Log output ────────────────────────────────────────────────────────────────

class TestLogging:
    def test_info_log_emitted(self, caplog) -> None:
        with caplog.at_level(logging.INFO, logger="swipewear.ingestion.refresh"):
            run_refresh(_store(), [_rec("ebay-001")], now=_NOW)
        assert any("Refresh job complete" in r.message for r in caplog.records)

    def test_log_contains_updated_count(self, caplog) -> None:
        with caplog.at_level(logging.INFO, logger="swipewear.ingestion.refresh"):
            run_refresh(_store(), [_rec("ebay-001")], now=_NOW)
        assert any("updated=1" in r.message for r in caplog.records)

    def test_log_contains_deduplicated_count(self, caplog) -> None:
        with caplog.at_level(logging.INFO, logger="swipewear.ingestion.refresh"):
            ebay = _rec("ebay-001", price=100.0)
            awin = _rec("awin-001", source=ProductSource.awin, price=80.0)
            run_refresh(_store(), [ebay, awin], now=_NOW)
        assert any("deduplicated=1" in r.message for r in caplog.records)

    def test_log_contains_removed_count(self, caplog) -> None:
        old = [_rec("ebay-old", available=False)]
        with caplog.at_level(logging.INFO, logger="swipewear.ingestion.refresh"):
            run_refresh(_store(old), [], now=_NOW)
        assert any("removed=1" in r.message for r in caplog.records)


# ── now default ───────────────────────────────────────────────────────────────

class TestNowDefault:
    def test_now_defaults_to_utc(self) -> None:
        store = _store()
        run_refresh(store, [])
        cutoff = store.get_unavailable_since.call_args.args[0]
        assert cutoff.tzinfo is not None
