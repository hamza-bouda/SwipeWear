#!/usr/bin/env python3
"""Golden scenario runner — v0 deterministic price-sort baseline.

Loads fixed fixtures, applies hard constraints, ranks by price ascending,
and compares against the pre-computed expected top-10.

Exit code: 0 = PASS, 1 = FAIL.
Run: python evaluation/run_golden.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from contracts.product import ProductRecord  # noqa: E402
from contracts.profile import UserPreferenceProfile  # noqa: E402

FIXTURES = Path(__file__).parent / "fixtures"


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


def _baseline_score(product: ProductRecord, max_price: float) -> float:
    return round(1.0 - product.price / max_price, 4)


def run_golden() -> bool:
    profile = UserPreferenceProfile.model_validate(
        json.loads((FIXTURES / "golden_user.json").read_text(encoding="utf-8"))
    )
    products = [
        ProductRecord.model_validate(p)
        for p in json.loads(
            (FIXTURES / "golden_catalogue.json").read_text(encoding="utf-8")
        )
    ]
    expected_data = json.loads(
        (FIXTURES / "golden_expected.json").read_text(encoding="utf-8")
    )
    expected_ids = [e["product_id"] for e in expected_data["top10"]]

    passing = [p for p in products if _passes_hard_constraints(p, profile)]
    ranked = sorted(passing, key=lambda p: p.price)
    top10 = [p.id for p in ranked[:10]]

    if top10 == expected_ids:
        print("PASS — golden scenario OK")
        return True

    print("FAIL — golden scenario regression detected")
    print(f"  Expected: {expected_ids}")
    print(f"  Got:      {top10}")
    diff = set(expected_ids) ^ set(top10)
    if diff:
        print(f"  Diff IDs: {sorted(diff)}")
    return False


if __name__ == "__main__":
    sys.exit(0 if run_golden() else 1)
