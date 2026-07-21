from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

from contracts.product import ProductRecord
from contracts.profile import UserPreferenceProfile
from evaluation.reporting import write_report

FIXTURES_DIR = Path(__file__).parent / "fixtures"


@dataclass
class EvaluationReport:
    passed: bool
    metrics: dict[str, float] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)
    fixture_hash: str = ""


def _passes_hard_constraints(product: ProductRecord, profile: UserPreferenceProfile) -> bool:
    hc = profile.hard_constraints
    if hc.max_price_eur is not None and product.price > hc.max_price_eur:
        return False
    if product.condition.value in hc.excluded_conditions:
        return False
    if hc.sizes:
        product_sizes: set[str] = set()
        if product.size_raw:
            product_sizes.add(product.size_raw)
        if product.size_eu:
            product_sizes.add(product.size_eu)
        if product_sizes and not product_sizes.intersection(set(hc.sizes)):
            return False
    return True


def run_golden_scenario(write_report_file: bool = False) -> EvaluationReport:
    """Execute the golden scenario on fixed fixtures. Never modify fixtures to make this pass."""
    profile = UserPreferenceProfile.model_validate(
        json.loads((FIXTURES_DIR / "golden_user.json").read_text(encoding="utf-8"))
    )
    products = [
        ProductRecord.model_validate(p)
        for p in json.loads(
            (FIXTURES_DIR / "golden_catalogue.json").read_text(encoding="utf-8")
        )
    ]
    expected_data = json.loads(
        (FIXTURES_DIR / "golden_expected.json").read_text(encoding="utf-8")
    )
    expected_ids = [e["product_id"] for e in expected_data["top10"]]

    passing = [p for p in products if _passes_hard_constraints(p, profile)]
    ranked = sorted(passing, key=lambda p: p.price)
    top10 = [p.id for p in ranked[:10]]

    passed = top10 == expected_ids
    report = EvaluationReport(
        passed=passed,
        metrics={
            "catalogue_size": float(len(products)),
            "passing_after_filter": float(len(passing)),
            "top10_match": 1.0 if passed else 0.0,
        },
    )
    if write_report_file:
        write_report("golden", report)
    return report
