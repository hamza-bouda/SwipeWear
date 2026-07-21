"""Recall@10 comparison and activation gate for optional segmentation."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Mapping

import numpy as np


@dataclass(frozen=True)
class RecallComparison:
    """Before/after retrieval measurement with a strict positive-gain gate."""

    baseline: float
    segmented: float
    gain: float
    activated: bool
    k: int = 10

    def to_dict(self) -> dict[str, float | bool | int]:
        return asdict(self)


def recall_at_k(
    query_vectors: Mapping[str, np.ndarray],
    catalogue_vectors: Mapping[str, np.ndarray],
    relevant_products: Mapping[str, set[str]],
    *,
    k: int = 10,
) -> float:
    """Return macro-average recall for cosine-ranked catalogue vectors."""
    if k <= 0:
        raise ValueError("k must be positive")
    if not query_vectors:
        raise ValueError("at least one query is required")
    if not catalogue_vectors:
        raise ValueError("at least one catalogue vector is required")

    catalogue = {
        product_id: _normalized(vector)
        for product_id, vector in catalogue_vectors.items()
    }
    recalls: list[float] = []
    for query_id, query_vector in query_vectors.items():
        relevant = relevant_products.get(query_id)
        if not relevant:
            raise ValueError(f"query {query_id!r} has no relevant products")
        query = _normalized(query_vector)
        ranking = sorted(
            catalogue,
            key=lambda product_id: (
                -float(np.dot(query, catalogue[product_id])),
                product_id,
            ),
        )
        retrieved = set(ranking[:k])
        recalls.append(len(retrieved & relevant) / len(relevant))
    return float(np.mean(recalls))


def compare_recall_at_10(
    query_vectors: Mapping[str, np.ndarray],
    baseline_vectors: Mapping[str, np.ndarray],
    segmented_vectors: Mapping[str, np.ndarray],
    relevant_products: Mapping[str, set[str]],
) -> RecallComparison:
    """Compare baseline and segmented retrieval and activate only on gain > 0."""
    baseline = recall_at_k(
        query_vectors,
        baseline_vectors,
        relevant_products,
        k=10,
    )
    segmented = recall_at_k(
        query_vectors,
        segmented_vectors,
        relevant_products,
        k=10,
    )
    gain = segmented - baseline
    return RecallComparison(
        baseline=round(baseline, 6),
        segmented=round(segmented, 6),
        gain=round(gain, 6),
        activated=gain > 0.0,
    )


def _normalized(vector: np.ndarray) -> np.ndarray:
    result = np.asarray(vector, dtype=np.float32)
    if result.ndim != 1 or result.size == 0:
        raise ValueError("vectors must be non-empty and one-dimensional")
    if not np.isfinite(result).all():
        raise ValueError("vectors must contain only finite values")
    norm = float(np.linalg.norm(result))
    if norm == 0.0:
        raise ValueError("vectors must have non-zero norm")
    return result / norm
