from __future__ import annotations

import numpy as np
import pytest

from evaluation.segmentation_recall import (
    compare_recall_at_10,
    recall_at_k,
)


def _vector(index: int, dimensions: int = 12) -> np.ndarray:
    result = np.zeros(dimensions, dtype=np.float32)
    result[index] = 1.0
    return result


def test_recall_at_10_counts_relevant_products_in_top_ten() -> None:
    catalogue = {f"p{index}": _vector(index) for index in range(12)}
    query = {"outerwear": _vector(11)}
    relevant = {"outerwear": {"p9", "p11"}}

    recall = recall_at_k(query, catalogue, relevant, k=10)

    assert recall == 0.5


def test_positive_recall_gain_activates_segmentation() -> None:
    query = {"outerwear": _vector(11)}
    baseline = {f"p{index}": _vector(index) for index in range(12)}
    segmented = dict(baseline)
    segmented["p9"] = _vector(11)
    relevant = {"outerwear": {"p9"}}

    comparison = compare_recall_at_10(
        query,
        baseline,
        segmented,
        relevant,
    )

    assert comparison.baseline == 0.0
    assert comparison.segmented == 1.0
    assert comparison.gain == 1.0
    assert comparison.activated is True


def test_equal_or_worse_recall_keeps_segmentation_disabled() -> None:
    query = {"outerwear": _vector(0)}
    vectors = {f"p{index}": _vector(index) for index in range(12)}
    relevant = {"outerwear": {"p0"}}

    comparison = compare_recall_at_10(query, vectors, vectors, relevant)

    assert comparison.gain == 0.0
    assert comparison.activated is False


@pytest.mark.parametrize(
    "vector",
    [
        np.zeros(3, dtype=np.float32),
        np.array([1.0, np.nan, 0.0], dtype=np.float32),
        np.zeros((2, 2), dtype=np.float32),
    ],
)
def test_invalid_vectors_are_rejected(vector: np.ndarray) -> None:
    with pytest.raises(ValueError):
        recall_at_k(
            {"query": vector},
            {"product": _vector(0)},
            {"query": {"product"}},
        )
