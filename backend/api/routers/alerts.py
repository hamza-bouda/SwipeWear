from __future__ import annotations

import json
import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException

from alerts.alert_store import (
    count_active_alerts,
    create_alert,
    delete_alert,
    get_alert,
    list_alerts,
    set_alert_status,
    update_alert_constraints,
)
from api.auth import get_current_user_id
from api.db import get_conn, put_conn
from billing.subscription_store import is_user_premium
from contracts.alerts import FREE_ALERT_LIMIT, Alert, AlertConstraints, AlertStatus, AlertType
from notifications.notification_store import count_missed_deals

_LOG = logging.getLogger("swipewear.api.alerts")

router = APIRouter(prefix="/alerts", tags=["alerts"])


from pydantic import BaseModel, Field


class AlertCreateRequest(BaseModel):
    alert_type: AlertType
    label: str
    reference_product_id: str | None = None
    reference_embedding: list[float] | None = None
    constraints: AlertConstraints = Field(default_factory=AlertConstraints)


class AlertPatchRequest(BaseModel):
    status: AlertStatus | None = None
    constraints: AlertConstraints | None = None


class AlertResponse(BaseModel):
    alert_id: UUID
    alert_type: AlertType
    label: str
    status: AlertStatus
    constraints: AlertConstraints
    reference_product_id: str | None = None


class AlertsListResponse(BaseModel):
    alerts: list[AlertResponse]
    active_count: int
    free_limit: int = FREE_ALERT_LIMIT
    missed_deals_count: int = 0


def _to_response(alert: Alert) -> AlertResponse:
    return AlertResponse(
        alert_id=alert.alert_id,
        alert_type=alert.alert_type,
        label=alert.label,
        status=alert.status,
        constraints=alert.constraints,
        reference_product_id=alert.reference_product_id,
    )


@router.post("", response_model=AlertResponse, status_code=201)
def create_alert_endpoint(
    body: AlertCreateRequest,
    user_id: UUID = Depends(get_current_user_id),
):
    conn = None
    try:
        conn = get_conn()
        active = count_active_alerts(conn, user_id)
        if active >= FREE_ALERT_LIMIT and not is_user_premium(conn, user_id):
            raise HTTPException(
                status_code=403,
                detail=f"Free tier limited to {FREE_ALERT_LIMIT} active alerts. Upgrade to Premium for unlimited alerts.",
            )
        alert = Alert(
            user_id=user_id,
            alert_type=body.alert_type,
            label=body.label,
            reference_product_id=body.reference_product_id,
            reference_embedding=body.reference_embedding,
            constraints=body.constraints,
        )
        create_alert(conn, alert)
        return _to_response(alert)
    except HTTPException:
        raise
    except Exception:
        _LOG.exception("Failed to create alert for user %s", user_id)
        raise HTTPException(status_code=500, detail="Failed to create alert")
    finally:
        if conn is not None:
            put_conn(conn)


@router.get("", response_model=AlertsListResponse)
def list_alerts_endpoint(user_id: UUID = Depends(get_current_user_id)):
    conn = None
    try:
        conn = get_conn()
        alerts = list_alerts(conn, user_id)
        active_count = sum(1 for a in alerts if a.status == AlertStatus.active)
        missed = count_missed_deals(conn, user_id)
        return AlertsListResponse(
            alerts=[_to_response(a) for a in alerts],
            active_count=active_count,
            missed_deals_count=missed,
        )
    except Exception:
        _LOG.exception("Failed to list alerts for user %s", user_id)
        raise HTTPException(status_code=500, detail="Failed to list alerts")
    finally:
        if conn is not None:
            put_conn(conn)


@router.patch("/{alert_id}", response_model=AlertResponse)
def patch_alert_endpoint(
    alert_id: UUID,
    body: AlertPatchRequest,
    user_id: UUID = Depends(get_current_user_id),
):
    conn = None
    try:
        conn = get_conn()

        if body.status is not None:
            if body.status == AlertStatus.active:
                active = count_active_alerts(conn, user_id)
                current = get_alert(conn, alert_id, user_id)
                if (
                    current
                    and current.status != AlertStatus.active
                    and active >= FREE_ALERT_LIMIT
                    and not is_user_premium(conn, user_id)
                ):
                    raise HTTPException(
                        status_code=403,
                        detail=f"Free tier limited to {FREE_ALERT_LIMIT} active alerts. Upgrade to Premium.",
                    )
            ok = set_alert_status(conn, alert_id, user_id, body.status)
            if not ok:
                raise HTTPException(status_code=404, detail="Alert not found")

        if body.constraints is not None:
            ok = update_alert_constraints(
                conn, alert_id, user_id, json.dumps(body.constraints.model_dump())
            )
            if not ok:
                raise HTTPException(status_code=404, detail="Alert not found")

        alert = get_alert(conn, alert_id, user_id)
        if alert is None:
            raise HTTPException(status_code=404, detail="Alert not found")
        return _to_response(alert)
    except HTTPException:
        raise
    except Exception:
        _LOG.exception("Failed to patch alert %s", alert_id)
        raise HTTPException(status_code=500, detail="Failed to update alert")
    finally:
        if conn is not None:
            put_conn(conn)


@router.delete("/{alert_id}", status_code=204)
def delete_alert_endpoint(
    alert_id: UUID,
    user_id: UUID = Depends(get_current_user_id),
):
    conn = None
    try:
        conn = get_conn()
        deleted = delete_alert(conn, alert_id, user_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Alert not found")
    except HTTPException:
        raise
    except Exception:
        _LOG.exception("Failed to delete alert %s", alert_id)
        raise HTTPException(status_code=500, detail="Failed to delete alert")
    finally:
        if conn is not None:
            put_conn(conn)
