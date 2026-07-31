import json
from pathlib import Path

import pytest

from contracts.product import ProductCondition, ProductRecord, ProductSource
from contracts.profile import UserPreferenceProfile
from evaluation.interfaces import EvaluationReport, _passes_hard_constraints, run_golden_scenario

FIXTURES = Path(__file__).parent.parent / "fixtures"


# ── Fixture loading ────────────────────────────────────────────────────────────

class TestFixtureLoading:
    def test_golden_user_loads_and_validates(self):
        data = json.loads((FIXTURES / "golden_user.json").read_text(encoding="utf-8"))
        profile = UserPreferenceProfile.model_validate(data)
        assert profile.hard_constraints.max_price_eur == 120.0
        assert "M" in profile.hard_constraints.sizes
        assert "42" in profile.hard_constraints.sizes
        assert "fair" in profile.hard_constraints.excluded_conditions

    def test_golden_catalogue_has_50_products(self):
        data = json.loads((FIXTURES / "golden_catalogue.json").read_text(encoding="utf-8"))
        products = [ProductRecord.model_validate(p) for p in data]
        assert len(products) == 50

    def test_golden_catalogue_covers_5_categories(self):
        data = json.loads((FIXTURES / "golden_catalogue.json").read_text(encoding="utf-8"))
        categories = {p["category"] for p in data}
        assert categories == {"sneakers", "vestes", "jeans", "tee-shirts", "accessoires"}

    def test_golden_catalogue_has_3_conditions(self):
        data = json.loads((FIXTURES / "golden_catalogue.json").read_text(encoding="utf-8"))
        conditions = {p["condition"] for p in data}
        assert {"new", "like_new", "good", "fair"}.issuperset(conditions)
        assert len(conditions) >= 3

    def test_golden_catalogue_has_2_sources(self):
        data = json.loads((FIXTURES / "golden_catalogue.json").read_text(encoding="utf-8"))
        sources = {p["source"] for p in data}
        assert sources == {"ebay", "awin"}

    def test_golden_expected_has_10_entries(self):
        data = json.loads((FIXTURES / "golden_expected.json").read_text(encoding="utf-8"))
        assert len(data["top10"]) == 10

    def test_golden_expected_ids_are_in_catalogue(self):
        cat = json.loads((FIXTURES / "golden_catalogue.json").read_text(encoding="utf-8"))
        catalogue_ids = {p["id"] for p in cat}
        exp = json.loads((FIXTURES / "golden_expected.json").read_text(encoding="utf-8"))
        for entry in exp["top10"]:
            assert entry["product_id"] in catalogue_ids

    def test_style_vectors_are_512_dim(self):
        data = json.loads((FIXTURES / "golden_user.json").read_text(encoding="utf-8"))
        profile = UserPreferenceProfile.model_validate(data)
        assert len(profile.vectors.positive) == 512
        assert len(profile.vectors.negative) == 512


# ── Hard constraint filter ─────────────────────────────────────────────────────

def _make_product(**overrides) -> ProductRecord:
    defaults = {
        "id": "test-001",
        "source": ProductSource.ebay,
        "source_record_id": "src-001",
        "title": "Test product",
        "price": 50.0,
        "condition": ProductCondition.good,
        "category": "sneakers",
        "image_urls": ["https://img.test.com/1.jpg"],
        "size_raw": "M",
        "size_eu": "M",
    }
    return ProductRecord(**{**defaults, **overrides})


def _make_profile(**hc_overrides) -> UserPreferenceProfile:
    from contracts.profile import HardConstraints
    defaults = {"sizes": ["M", "42"], "max_price_eur": 120.0, "excluded_conditions": ["fair"]}
    defaults.update(hc_overrides)
    hc = HardConstraints(**defaults)
    profile = UserPreferenceProfile()
    profile.hard_constraints = hc
    return profile


class TestHardConstraintFilter:
    def test_product_within_budget_passes(self):
        p = _make_product(price=100.0)
        assert _passes_hard_constraints(p, _make_profile()) is True

    def test_product_over_budget_fails(self):
        p = _make_product(price=121.0)
        assert _passes_hard_constraints(p, _make_profile()) is False

    def test_fair_condition_fails(self):
        p = _make_product(condition=ProductCondition.fair)
        assert _passes_hard_constraints(p, _make_profile()) is False

    def test_good_condition_passes(self):
        p = _make_product(condition=ProductCondition.good)
        assert _passes_hard_constraints(p, _make_profile()) is True

    def test_wrong_size_fails(self):
        p = _make_product(size_raw="XL", size_eu="XL")
        assert _passes_hard_constraints(p, _make_profile()) is False

    def test_correct_size_passes(self):
        p = _make_product(size_raw="M", size_eu="M")
        assert _passes_hard_constraints(p, _make_profile()) is True

    def test_no_size_product_passes_size_filter(self):
        p = _make_product(size_raw=None, size_eu=None)
        assert _passes_hard_constraints(p, _make_profile()) is True

    def test_empty_sizes_constraint_passes_all(self):
        p = _make_product(size_raw="XL", size_eu="XL")
        profile = _make_profile(sizes=[])
        assert _passes_hard_constraints(p, profile) is True


# ── Golden scenario ────────────────────────────────────────────────────────────

class TestGoldenScenario:
    def test_run_golden_scenario_returns_report(self):
        report = run_golden_scenario()
        assert isinstance(report, EvaluationReport)

    def test_golden_scenario_passes(self):
        report = run_golden_scenario()
        assert report.passed is True, (
            "Golden scenario FAILED — fix the code, never modify the fixtures."
        )

    def test_golden_metrics_present(self):
        report = run_golden_scenario()
        assert report.metrics["catalogue_size"] == 50.0
        assert report.metrics["passing_after_filter"] == 29.0
        assert report.metrics["top10_match"] == 1.0
