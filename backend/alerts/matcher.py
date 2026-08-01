"""Batch alert matcher -- periodic pgvector scan (F11).

Complements ingestion/alert_runner.py (which matches one product at
ingestion time using DINOv2) by scanning ALL recent products against
ALL active alerts using the FashionSigLIP embeddings already indexed
in pgvector.

Run via: python scripts/run_alert_matcher.py (cron every 1h)
"""
from __future__ import annotations

import json
import logging
from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import UUID

from billing.subscription_store import is_user_premium
from notifications.dispatcher import enqueue_match_notification

_LOG = logging.getLogger("swipewear.alerts.matcher")

SIMILARITY_THRESHOLD = 0.90

_MATCH_QUERY = """\
SELECT p.id, p.title, p.price, p.condition, p.size_eu,
       p.image_urls, p.available,
       1 - (e.embedding <=> %(ref_embedding)s::vector) AS similarity
FROM products AS p
JOIN product_embeddings AS e ON e.product_id = p.id
WHERE p.available = true
  AND p.created_at >= %(since)s
  AND NOT EXISTS (
      SELECT 1 FROM notification_queue AS nq
      WHERE nq.alert_id = %(alert_id)s AND nq.product_id = p.id
  )
ORDER BY e.embedding <=> %(ref_embedding)s::vector
LIMIT %(k)s"""

_CONDITION_RANK = {"new": 3, "very_good": 2, "good": 1, "fair": 0}


def _to_pgvector_literal(vector: list[float]) -> str:
    return "[" + ",".join(str(float(v)) for v in vector) + "]"


def _fetch_active_alerts_with_embeddings(conn: Any) -> list[dict]:
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT alert_id, user_id, alert_type, reference_embedding,
                   constraints, reference_product_id
            FROM alerts
            WHERE status = 'active' AND reference_embedding IS NOT NULL
            """
        )
        rows = cur.fetchall()

    alerts = []
    for alert_id, user_id, alert_type, ref_emb, constraints_raw, ref_product_id in rows:
        constraints = (
            constraints_raw
            if isinstance(constraints_raw, dict)
            else json.loads(constraints_raw)
        )
        alerts.append({
            "alert_id": UUID(str(alert_id)),
            "user_id": UUID(str(user_id)),
            "alert_type": alert_type,
            "reference_embedding": list(ref_emb),
            "constraints": constraints,
            "reference_product_id": ref_product_id,
        })
    return alerts


def _passes_constraints(
    price: float | None,
    size_eu: str | None,
    condition: str | None,
    constraints: dict,
) -> bool:
    max_price = constraints.get("max_price_eur")
    if max_price is not None and price is not None:
        if float(price) > float(max_price):
            return False

    sizes = constraints.get("sizes", [])
    if sizes and size_eu is not None:
        if size_eu not in sizes:
            return False

    min_condition = constraints.get("min_condition")
    if min_condition and condition:
        if _CONDITION_RANK.get(condition, -1) < _CONDITION_RANK.get(min_condition, -1):
            return False

    return True


def run_batch_matching(
    conn: Any,
    window_hours: int = 2,
    max_candidates_per_alert: int = 50,
) -> int:
    """Scan recent products against all active alerts.

    Returns the total number of notifications enqueued.
    """
    since = datetime.now(timezone.utc) - timedelta(hours=window_hours)
    alerts = _fetch_active_alerts_with_embeddings(conn)

    if not alerts:
        _LOG.info("No active alerts with embeddings.")
        return 0

    _LOG.info(
        "Matching %d alert(s) against products since %s",
        len(alerts), since.isoformat(),
    )

    total_enqueued = 0
    premium_cache: dict[UUID, bool] = {}

    for alert in alerts:
        ref_vector = _to_pgvector_literal(alert["reference_embedding"])

        with conn.cursor() as cur:
            cur.execute(
                _MATCH_QUERY,
                {
                    "ref_embedding": ref_vector,
                    "since": since,
                    "alert_id": str(alert["alert_id"]),
                    "k": max_candidates_per_alert,
                },
            )
            rows = cur.fetchall()

        for row in rows:
            product_id, title, price, condition, size_eu, image_urls, _, similarity = row

            if similarity < SIMILARITY_THRESHOLD:
                break

            if not _passes_constraints(
                float(price) if price else None,
                size_eu, condition, alert["constraints"],
            ):
                continue

            if alert["reference_product_id"] and product_id == alert["reference_product_id"]:
                continue

            uid = alert["user_id"]
            if uid not in premium_cache:
                premium_cache[uid] = is_user_premium(conn, uid)

            queue_id = enqueue_match_notification(
                conn=conn,
                user_id=uid,
                alert_id=alert["alert_id"],
                product_id=product_id,
                match_tier="similar",
                product_price=float(price) if price else None,
                product_image=image_urls[0] if image_urls else None,
                is_premium=premium_cache[uid],
            )

            if queue_id is not None:
                total_enqueued += 1
                _LOG.info(
                    "Match: alert=%s product=%s sim=%.4f price=%s",
                    alert["alert_id"], product_id, similarity,
                    price,
                )

    _LOG.info("Batch matching done: %d notification(s) enqueued.", total_enqueued)
    return total_enqueued
