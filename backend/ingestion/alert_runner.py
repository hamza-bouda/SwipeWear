"""Ingestion-time alert matching job (KAN-70 / KAN-74).

Called after each new product is inserted into the catalogue.
Evaluates the product against all active specific_item alerts using DINOv2
and dispatches push notifications via the notification queue (KAN-74).

Design constraints:
- Runs in the ingestion job, NOT per user-request.
- DINOv2 model is shared (singleton) with vision/instance_matcher.py.
- Push dispatch: is_premium looked up per user via billing.subscription_store.
- A missing reference_dinov2_embedding on an alert silently skips it.
"""
from __future__ import annotations

import logging
from typing import Any
from uuid import UUID

from alerts.alert_store import fetch_active_specific_item_alerts
from billing.subscription_store import is_user_premium
from notifications.dispatcher import enqueue_match_notification
from vision.interfaces import MatchResult, MatchTier, match

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


def dispatch_alert_matches(
    conn: Any,
    product_id: str,
    matches: list[AlertMatch],
    product_price: float | None = None,
    product_image: str | None = None,
) -> int:
    """Enqueue push notifications for each AlertMatch (KAN-74).

    Looks up premium status per user so premium users get instant delivery
    and free-tier users get the 30-minute delay.

    Returns the number of notifications enqueued (None returns from
    enqueue_match_notification — suppressed prefs — are not counted).
    """
    enqueued = 0
    for m in matches:
        premium = is_user_premium(conn, m.user_id)
        queue_id = enqueue_match_notification(
            conn=conn,
            user_id=m.user_id,
            alert_id=m.alert_id,
            product_id=product_id,
            match_tier=m.result.tier.value,
            product_price=product_price,
            product_image=product_image,
            is_premium=premium,
        )
        if queue_id is not None:
            enqueued += 1
            _LOG.info(
                "Dispatched notification queue_id=%s user=%s alert=%s tier=%s premium=%s",
                queue_id, m.user_id, m.alert_id, m.result.tier.value, premium,
            )
    return enqueued
