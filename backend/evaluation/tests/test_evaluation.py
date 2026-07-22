import json
from pathlib import Path

import pytest

from contracts.product import ProductCondition, ProductRecord, ProductSource
from contracts.profile import UserPreferenceProfile
from evaluation.eval_ranking import (
    RankingEvalReport,
    compute_ndcg,
    evaluate_ranking,
)
from evaluation.eval_retrieval import (
    RECALL_100_THRESHOLD,
    RetrievalEvalReport,
    compute_recall_at_k,
    evaluate_retrieval,
)
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

    def test_style_vectors_are_768_dim(self):
        data = json.loads((FIXTURES / "golden_user.json").read_text(encoding="utf-8"))
        profile = UserPreferenceProfile.model_validate(data)
        assert len(profile.vectors.positive) == 768
        assert len(profile.vectors.negative) == 768


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


# -- Retrieval evaluation -- Recall@K (KAN-40) --------------------------------

class TestComputeRecallAtK:
    def test_perfect_recall(self) -> None:
        expected = ["a", "b", "c"]
        retrieved = ["a", "b", "c", "d", "e"]
        assert compute_recall_at_k(retrieved, expected, k=5) == 1.0

    def test_partial_recall(self) -> None:
        expected = ["a", "b", "c", "d"]
        retrieved = ["a", "b", "x", "y", "z"]
        assert compute_recall_at_k(retrieved, expected, k=5) == 0.5

    def test_zero_recall(self) -> None:
        expected = ["a", "b"]
        retrieved = ["x", "y", "z"]
        assert compute_recall_at_k(retrieved, expected, k=3) == 0.0

    def test_k_limits_retrieved(self) -> None:
        expected = ["a", "b"]
        retrieved = ["x", "y", "a", "b"]
        assert compute_recall_at_k(retrieved, expected, k=2) == 0.0
        assert compute_recall_at_k(retrieved, expected, k=4) == 1.0

    def test_empty_expected_returns_1(self) -> None:
        assert compute_recall_at_k(["a", "b"], [], k=10) == 1.0

    def test_empty_retrieved_returns_0(self) -> None:
        assert compute_recall_at_k([], ["a", "b"], k=10) == 0.0


class TestEvaluateRetrieval:
    def test_returns_report_with_all_k_values(self) -> None:
        retrieved = [f"p{i}" for i in range(100)]
        expected = [f"p{i}" for i in range(10)]
        report = evaluate_retrieval(retrieved, expected, write_report=False)
        assert isinstance(report, RetrievalEvalReport)
        assert 10 in report.recall_at
        assert 20 in report.recall_at
        assert 50 in report.recall_at
        assert 100 in report.recall_at

    def test_passed_when_recall_100_above_threshold(self) -> None:
        retrieved = [f"p{i}" for i in range(100)]
        expected = [f"p{i}" for i in range(10)]
        report = evaluate_retrieval(retrieved, expected, write_report=False)
        assert report.passed is True
        assert report.failure_reason == ""

    def test_fails_when_recall_100_below_threshold(self) -> None:
        retrieved = ["x"] * 100
        expected = [f"p{i}" for i in range(10)]
        report = evaluate_retrieval(retrieved, expected, write_report=False)
        assert report.passed is False
        assert "Recall@100" in report.failure_reason

    def test_counts_populated(self) -> None:
        retrieved = ["a", "b", "c"]
        expected = ["a", "b"]
        report = evaluate_retrieval(retrieved, expected, write_report=False)
        assert report.expected_count == 2
        assert report.retrieved_count == 3

    def test_evaluated_at_is_set(self) -> None:
        report = evaluate_retrieval(["a"], ["a"], write_report=False)
        assert report.evaluated_at != ""

    def test_write_report_creates_json(self, tmp_path) -> None:
        import evaluation.eval_retrieval as mod

        original_dir = mod.REPORTS_DIR
        mod.REPORTS_DIR = tmp_path
        try:
            evaluate_retrieval(["a"], ["a"], write_report=True)
            reports = list(tmp_path.glob("*_retrieval_*.json"))
            assert len(reports) == 1
            data = json.loads(reports[0].read_text(encoding="utf-8"))
            assert "recall_at" in data
            assert data["git_sha"]
            assert data["config"]["ranker_weights"]
            assert (tmp_path / "INDEX.csv").exists()
        finally:
            mod.REPORTS_DIR = original_dir


class TestGoldenRecall:
    def test_recall_at_10_on_golden_catalogue(self) -> None:
        """AC: on golden catalogue of 50 products, Recall@10 is coherent."""
        exp_data = json.loads(
            (FIXTURES / "golden_expected.json").read_text(encoding="utf-8"),
        )
        expected_ids = [e["product_id"] for e in exp_data["top10"]]
        retrieved_ids = expected_ids + [f"filler-{i}" for i in range(40)]
        report = evaluate_retrieval(
            retrieved_ids, expected_ids, write_report=False,
        )
        assert report.recall_at[10] == 1.0
        assert report.recall_at[100] >= RECALL_100_THRESHOLD
        assert report.passed is True


# -- Ranking evaluation -- NDCG@K (KAN-48) ----------------------------------

class TestComputeNdcg:
    def test_perfect_ranking(self) -> None:
        relevance = {"a": 3.0, "b": 2.0, "c": 1.0}
        assert compute_ndcg(["a", "b", "c"], relevance, k=3) == 1.0

    def test_reversed_ranking(self) -> None:
        relevance = {"a": 3.0, "b": 2.0, "c": 1.0}
        score = compute_ndcg(["c", "b", "a"], relevance, k=3)
        assert score < 1.0
        assert score > 0.0

    def test_empty_relevance(self) -> None:
        assert compute_ndcg(["a", "b"], {}, k=3) == 1.0

    def test_unknown_ids_get_zero_relevance(self) -> None:
        relevance = {"a": 3.0}
        score = compute_ndcg(["x", "y", "a"], relevance, k=3)
        assert score < 1.0

    def test_k_limits_ranking(self) -> None:
        relevance = {"a": 3.0, "b": 2.0, "c": 1.0}
        score_k1 = compute_ndcg(["a", "c", "b"], relevance, k=1)
        assert score_k1 == 1.0

    def test_single_item(self) -> None:
        assert compute_ndcg(["a"], {"a": 1.0}, k=1) == 1.0


class TestEvaluateRanking:
    def test_returns_report(self) -> None:
        relevance = {"a": 3.0, "b": 2.0, "c": 1.0}
        baseline = ["a", "b", "c"]
        ranker = ["a", "b", "c"]
        report = evaluate_ranking(baseline, ranker, relevance, write_report=False)
        assert isinstance(report, RankingEvalReport)

    def test_ranker_better_passes(self) -> None:
        relevance = {"a": 3.0, "b": 2.0, "c": 1.0}
        baseline = ["c", "b", "a"]
        ranker = ["a", "b", "c"]
        report = evaluate_ranking(baseline, ranker, relevance, write_report=False)
        assert report.passed is True
        assert report.delta > 0

    def test_ranker_equal_passes(self) -> None:
        relevance = {"a": 3.0, "b": 2.0}
        same = ["a", "b"]
        report = evaluate_ranking(same, same, relevance, write_report=False)
        assert report.passed is True
        assert report.delta == 0.0

    def test_ranker_worse_fails(self) -> None:
        relevance = {"a": 3.0, "b": 2.0, "c": 1.0}
        baseline = ["a", "b", "c"]
        ranker = ["c", "b", "a"]
        report = evaluate_ranking(baseline, ranker, relevance, write_report=False)
        assert report.passed is False
        assert "NDCG" in report.failure_reason

    def test_evaluated_at_set(self) -> None:
        report = evaluate_ranking(["a"], ["a"], {"a": 1.0}, write_report=False)
        assert report.evaluated_at != ""

    def test_write_report_creates_json(self, tmp_path) -> None:
        import evaluation.eval_ranking as mod

        original_dir = mod.REPORTS_DIR
        mod.REPORTS_DIR = tmp_path
        try:
            evaluate_ranking(["a"], ["a"], {"a": 1.0}, write_report=True)
            reports = list(tmp_path.glob("*_ranking_*.json"))
            assert len(reports) == 1
            data = json.loads(reports[0].read_text(encoding="utf-8"))
            assert "ndcg_baseline" in data
            assert "ndcg_ranker" in data
            assert "delta" in data
        finally:
            mod.REPORTS_DIR = original_dir


class TestGoldenRanking:
    def test_ndcg_on_golden_expected(self) -> None:
        exp_data = json.loads(
            (FIXTURES / "golden_expected.json").read_text(encoding="utf-8"),
        )
        relevance = {
            e["product_id"]: e["baseline_score"]
            for e in exp_data["top10"]
        }
        ideal_ids = [e["product_id"] for e in exp_data["top10"]]
        report = evaluate_ranking(
            ideal_ids, ideal_ids, relevance, write_report=False,
        )
        assert report.ndcg_baseline == 1.0
        assert report.ndcg_ranker == 1.0
        assert report.passed is True
