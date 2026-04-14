"""CRUD operations for the `alerts` table (KAN-69)."""
from __future__ import annotations

import json
import logging
from typing import Any
from uuid import UUID

from contracts.alerts import FREE_ALERT_LIMIT, Alert, AlertStatus, AlertType

_LOG = logging.getLogger("swipewear.alerts.store")


def count_active_alerts(conn: Any, user_id: UUID) -> int:
    with conn.cursor() as cur:
        cur.execute(
            "SELECT COUNT(*) FROM alerts WHERE user_id = %s AND status = 'active'",
            (str(user_id),),
        )
        return cur.fetchone()[0]


def create_alert(conn: Any, alert: Alert) -> Alert:
    with conn.cursor() as cur:
        embedding_json = json.dumps(alert.reference_embedding) if alert.reference_embedding else None
        constraints_json = json.dumps(alert.constraints.model_dump())
        cur.execute(
            """
            INSERT INTO alerts
                (alert_id, user_id, alert_type, label, reference_embedding,
                 reference_product_id, constraints, status, created_at, schema_version)
            VALUES (%s, %s, %s, %s, %s::jsonb, %s, %s::jsonb, %s, %s, %s)
            """,
            (
                str(alert.alert_id),
                str(alert.user_id),
                alert.alert_type.value,
                alert.label,
                embedding_json,
                alert.reference_product_id,
                constraints_json,
                alert.status.value,
                alert.created_at,
                alert.schema_version,
            ),
        )
    conn.commit()
    return alert


def list_alerts(conn: Any, user_id: UUID) -> list[Alert]:
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT alert_id, user_id, alert_type, label, reference_embedding,
                   reference_product_id, constraints, status, created_at, schema_version
            FROM alerts WHERE user_id = %s ORDER BY created_at DESC
            """,
            (str(user_id),),
        )
        rows = cur.fetchall()
    return [_row_to_alert(r) for r in rows]


def get_alert(conn: Any, alert_id: UUID, user_id: UUID) -> Alert | None:
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT alert_id, user_id, alert_type, label, reference_embedding,
                   reference_product_id, constraints, status, created_at, schema_version
            FROM alerts WHERE alert_id = %s AND user_id = %s
            """,
            (str(alert_id), str(user_id)),
        )
        row = cur.fetchone()
    return _row_to_alert(row) if row else None


def set_alert_status(conn: Any, alert_id: UUID, user_id: UUID, status: AlertStatus) -> bool:
    with conn.cursor() as cur:
        cur.execute(
            "UPDATE alerts SET status = %s WHERE alert_id = %s AND user_id = %s",
            (status.value, str(alert_id), str(user_id)),
        )
        updated = cur.rowcount
    conn.commit()
    return updated > 0


def delete_alert(conn: Any, alert_id: UUID, user_id: UUID) -> bool:
    with conn.cursor() as cur:
        cur.execute(
            "DELETE FROM alerts WHERE alert_id = %s AND user_id = %s",
            (str(alert_id), str(user_id)),
        )
        deleted = cur.rowcount
    conn.commit()
    return deleted > 0


def update_alert_constraints(conn: Any, alert_id: UUID, user_id: UUID, constraints_json: str) -> bool:
    with conn.cursor() as cur:
        cur.execute(
            "UPDATE alerts SET constraints = %s::jsonb WHERE alert_id = %s AND user_id = %s",
            (constraints_json, str(alert_id), str(user_id)),
        )
        updated = cur.rowcount
    conn.commit()
    return updated > 0


def _row_to_alert(row: tuple) -> Alert:
    (
        alert_id, user_id, alert_type, label, reference_embedding,
        reference_product_id, constraints, status, created_at, schema_version,
    ) = row
    return Alert(
        alert_id=alert_id,
        user_id=user_id,
        alert_type=AlertType(alert_type),
        label=label,
        reference_embedding=reference_embedding if reference_embedding is None else list(reference_embedding),
        reference_product_id=reference_product_id,
        constraints=constraints if isinstance(constraints, dict) else json.loads(constraints),
        status=AlertStatus(status),
        created_at=created_at,
        schema_version=schema_version,
    )
