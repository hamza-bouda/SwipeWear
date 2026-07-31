"""Tests for ingestion.enricher — TitleEnricher.enrich(record) -> ProductRecord."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

import ingestion.enricher as _mod
from contracts.product import ProductCondition, ProductRecord, ProductSource
from ingestion.enricher import TitleEnricher

# ── Helpers ───────────────────────────────────────────────────────────────────

_IMG = ["https://img.example.com/a.jpg"]


def _record(**kwargs) -> ProductRecord:
    defaults: dict = dict(
        id="ebay-test001",
        source=ProductSource.ebay,
        source_record_id="test001",
        title="Veste Carhartt Detroit taille M très bon état marron",
        price=45.0,
        currency="EUR",
        condition=ProductCondition.good,
        category="vestes",
        image_urls=_IMG,
    )
    defaults.update(kwargs)
    return ProductRecord(**defaults)


def _mock_model(entities: list[dict]) -> MagicMock:
    m = MagicMock()
    m.predict_entities.return_value = entities
    return m


# ── 5 titres Vinted — marque extraite sur les 5 ───────────────────────────────

_VINTED_TITLES = [
    ("Veste Carhartt Detroit taille M très bon état marron", "Carhartt"),
    ("Nike Air Force 1 Blanc Taille 42 Neuf", "Nike"),
    ("Jean Levi's 501 W32 L32 bleu délavé", "Levi's"),
    ("Adidas Gazelle taille 38 Rose occasion", "Adidas"),
    ("T-shirt Tommy Hilfiger bleu marine XL", "Tommy Hilfiger"),
]


class TestBrandExtraction:
    @patch("ingestion.enricher._get_model")
    def test_brand_extracted_for_5_vinted_titles(self, mock_get: MagicMock) -> None:
        brand_map = {title: brand for title, brand in _VINTED_TITLES}

        def predict(title: str, labels: list[str], threshold: float = 0.5) -> list[dict]:
            return [{"label": "marque", "text": brand_map[title], "score": 0.95}]

        mock_model = MagicMock()
        mock_model.predict_entities.side_effect = predict
        mock_get.return_value = mock_model

        enricher = TitleEnricher()
        for title, expected_brand in _VINTED_TITLES:
            rec = _record(title=title, brand=None)
            enriched = enricher.enrich(rec)
            assert enriched.brand == expected_brand, f"Brand not extracted for: {title!r}"


# ── Singleton — modèle chargé une seule fois ──────────────────────────────────

class TestSingleton:
    def test_model_returned_without_reload_when_already_set(self) -> None:
        original = _mod._model
        try:
            sentinel = MagicMock()
            _mod._model = sentinel
            result = _mod._get_model()
            assert result is sentinel
        finally:
            _mod._model = original


# ── Fusion des champs ─────────────────────────────────────────────────────────

class TestFieldMerge:
    @patch("ingestion.enricher._get_model")
    def test_enriched_attrs_populated(self, mock_get: MagicMock) -> None:
        mock_get.return_value = _mock_model([
            {"label": "marque", "text": "Carhartt", "score": 0.95},
            {"label": "taille", "text": "M", "score": 0.90},
            {"label": "couleur", "text": "marron", "score": 0.85},
        ])
        enriched = TitleEnricher().enrich(_record())
        assert enriched.enriched_attrs == {"marque": "Carhartt", "taille": "M", "couleur": "marron"}

    @patch("ingestion.enricher._get_model")
    def test_empty_entities_enriched_attrs_is_empty(self, mock_get: MagicMock) -> None:
        mock_get.return_value = _mock_model([])
        enriched = TitleEnricher().enrich(_record())
        assert enriched.enriched_attrs == {}

    @patch("ingestion.enricher._get_model")
    def test_brand_set_when_record_has_none(self, mock_get: MagicMock) -> None:
        mock_get.return_value = _mock_model([{"label": "marque", "text": "Nike", "score": 0.9}])
        enriched = TitleEnricher().enrich(_record(brand=None))
        assert enriched.brand == "Nike"

    @patch("ingestion.enricher._get_model")
    def test_existing_brand_not_overwritten(self, mock_get: MagicMock) -> None:
        mock_get.return_value = _mock_model([{"label": "marque", "text": "Nike", "score": 0.9}])
        enriched = TitleEnricher().enrich(_record(brand="Adidas"))
        assert enriched.brand == "Adidas"

    @patch("ingestion.enricher._get_model")
    def test_model_field_set_when_record_has_none(self, mock_get: MagicMock) -> None:
        mock_get.return_value = _mock_model([{"label": "modèle", "text": "501", "score": 0.9}])
        enriched = TitleEnricher().enrich(_record(model=None))
        assert enriched.model == "501"

    @patch("ingestion.enricher._get_model")
    def test_existing_model_field_not_overwritten(self, mock_get: MagicMock) -> None:
        mock_get.return_value = _mock_model([{"label": "modèle", "text": "502", "score": 0.9}])
        enriched = TitleEnricher().enrich(_record(model="501"))
        assert enriched.model == "501"

    @patch("ingestion.enricher._get_model")
    def test_size_eu_set_when_record_has_none(self, mock_get: MagicMock) -> None:
        mock_get.return_value = _mock_model([{"label": "taille", "text": "M", "score": 0.9}])
        enriched = TitleEnricher().enrich(_record(size_eu=None))
        assert enriched.size_eu == "M"

    @patch("ingestion.enricher._get_model")
    def test_size_eu_with_eu_prefix(self, mock_get: MagicMock) -> None:
        mock_get.return_value = _mock_model([{"label": "taille", "text": "EU 42", "score": 0.9}])
        enriched = TitleEnricher().enrich(_record(size_eu=None))
        assert enriched.size_eu == "42"

    @patch("ingestion.enricher._get_model")
    def test_existing_size_eu_not_overwritten(self, mock_get: MagicMock) -> None:
        mock_get.return_value = _mock_model([{"label": "taille", "text": "L", "score": 0.9}])
        enriched = TitleEnricher().enrich(_record(size_eu="42"))
        assert enriched.size_eu == "42"

    @patch("ingestion.enricher._get_model")
    def test_duplicate_label_keeps_first_occurrence(self, mock_get: MagicMock) -> None:
        mock_get.return_value = _mock_model([
            {"label": "marque", "text": "Nike", "score": 0.9},
            {"label": "marque", "text": "Adidas", "score": 0.8},
        ])
        enriched = TitleEnricher().enrich(_record(brand=None))
        assert enriched.enriched_attrs["marque"] == "Nike"
        assert enriched.brand == "Nike"

    @patch("ingestion.enricher._get_model")
    def test_original_record_not_mutated(self, mock_get: MagicMock) -> None:
        mock_get.return_value = _mock_model([{"label": "marque", "text": "Nike", "score": 0.9}])
        rec = _record(brand=None)
        enriched = TitleEnricher().enrich(rec)
        assert rec.brand is None
        assert enriched.brand == "Nike"


# ── Fallback ──────────────────────────────────────────────────────────────────

class TestFallback:
    @patch("ingestion.enricher._get_model")
    def test_fallback_on_model_load_failure(self, mock_get: MagicMock) -> None:
        mock_get.side_effect = RuntimeError("GLiNER not available")
        rec = _record()
        result = TitleEnricher().enrich(rec)
        assert result is rec

    @patch("ingestion.enricher._get_model")
    def test_fallback_on_inference_failure(self, mock_get: MagicMock) -> None:
        m = MagicMock()
        m.predict_entities.side_effect = Exception("CUDA OOM")
        mock_get.return_value = m
        rec = _record()
        result = TitleEnricher().enrich(rec)
        assert result is rec

    @patch("ingestion.enricher._get_model")
    def test_fallback_preserves_all_original_fields(self, mock_get: MagicMock) -> None:
        mock_get.side_effect = RuntimeError("no model")
        rec = _record(brand="Levi's", size_eu="32", model="501")
        result = TitleEnricher().enrich(rec)
        assert result.brand == "Levi's"
        assert result.size_eu == "32"
        assert result.model == "501"
