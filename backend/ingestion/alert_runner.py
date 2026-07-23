"""Ingestion-time alert matching job (KAN-70).

Called after each new product is inserted into the catalogue.
Evaluates the product against all active specific_item alerts using DINOv2
and logs matches with their scores for audit and future recalibration.

Design constraints:
- Runs in the ingestion job, NOT per user-request.
- DINOv2 model is shared (singleton) with vision/instance_matcher.py.
- Does not fire push notifications — that is KAN-71.
- A missing reference_dinov2_embedding on an alert silently skips it.
"""
from __future__ import annotations

import logging
from typing import Any
from uuid import UUID

from alerts.alert_store import fetch_active_specific_item_alerts
from vision.instance_matcher import MatchResult, MatchTier, match

_LOG = logging.getLogger("swipewear.ingestion.alert_runner")


class AlertMatch:
    """A confirmed alert match (exact or similar) for a new product."""

    __slots__ = ("alert_id", "user_id", "result")

    def __init__(self, alert_id: UUID, user_id: UUID, result: MatchResult) -> None:
        self.alert_id = alert_id
        self.user_id = user_id
        self.result = result


def evaluate_product_against_alerts(
    conn: Any,
    product_image_bytes: bytes,
    product_fashion_embedding: list[float] | None = None,
) -> list[AlertMatch]:
    """Check a newly-ingested product against all active specific_item alerts.

    Args:
        conn: psycopg2 DB connection.
        product_image_bytes: raw image bytes of the new product.
        product_fashion_embedding: FashionSigLIP embedding of the new product
            (pre-computed during ingestion; avoids double-encoding).

    Returns:
        List of AlertMatch where tier is "exact" or "similar".
        Empty list if DINOv2 model is unavailable or no alerts exist.
    """
    rows = fetch_active_specific_item_alerts(conn)
    if not rows:
        return []

    matches: list[AlertMatch] = []
    for (alert_id, user_id, dinov2_emb, fashion_emb) in rows:
        if dinov2_emb is None:
            _LOG.debug("Alert %s has no DINOv2 reference — skipped", alert_id)
            continue

        try:
            result = match(
                reference_dinov2_embedding=list(dinov2_emb),
                candidate_image=product_image_bytes,
                reference_fashion_embedding=list(fashion_emb) if fashion_emb is not None else None,
                candidate_fashion_embedding=product_fashion_embedding,
            )
        except Exception:
            _LOG.warning(
                "DINOv2 match() failed for alert %s — skipping", alert_id, exc_info=True
            )
            continue

        _LOG.info(
            "Alert %s | user %s | tier=%s dinov2=%.4f%s",
            alert_id,
            user_id,
            result.tier,
            result.dinov2_score,
            f" fashion={result.fashion_score:.4f}" if result.fashion_score is not None else "",
        )

        if result.tier != MatchTier.no_match:
            matches.append(AlertMatch(
                alert_id=UUID(str(alert_id)),
                user_id=UUID(str(user_id)),
                result=result,
            ))

    return matches
