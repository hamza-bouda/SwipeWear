"""Unit tests for alert matching constraints."""

from alerts.matcher import _passes_constraints


def test_like_new_condition_uses_the_product_contract_spelling() -> None:
    assert _passes_constraints(
        40.0,
        "M",
        "like_new",
        {"min_condition": "like_new"},
    )
    assert not _passes_constraints(
        40.0,
        "M",
        "good",
        {"min_condition": "like_new"},
    )


def test_alert_constraints_keep_price_and_size_filters() -> None:
    constraints = {"max_price_eur": 50, "sizes": ["M"]}
    assert _passes_constraints(49.99, "M", "good", constraints)
    assert not _passes_constraints(50.01, "M", "good", constraints)
    assert not _passes_constraints(49.99, "L", "good", constraints)


def test_hard_constraints_reject_unknown_values() -> None:
    constraints = {
        "max_price_eur": 50,
        "sizes": ["M"],
        "min_condition": "good",
    }
    assert not _passes_constraints(None, "M", "good", constraints)
    assert not _passes_constraints(49.99, None, "good", constraints)
    assert not _passes_constraints(49.99, "M", None, constraints)
