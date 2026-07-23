from __future__ import annotations

import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from api.auth import get_current_user_id
from api.db import get_conn, put_conn
from notifications.notification_store import mark_notification_opened, register_device_token

_LOG = logging.getLogger("swipewear.api.notifications")

router = APIRouter(prefix="/notifications", tags=["notifications"])


class DeviceTokenRequest(BaseModel):
    expo_token: str
    platform: str = "unknown"


class DeviceTokenResponse(BaseModel):
    registered: bool = True


class OpenedRequest(BaseModel):
    queue_id: str


@router.post("/register", response_model=DeviceTokenResponse, status_code=201)
def register_token(
    body: DeviceTokenRequest,
    user_id: UUID = Depends(get_current_user_id),
):
    if not body.expo_token.startswith("ExponentPushToken["):
        raise HTTPException(status_code=400, detail="Invalid Expo push token format")
    conn = None
    try:
        conn = get_conn()
        register_device_token(conn, user_id, body.expo_token, body.platform)
        return DeviceTokenResponse()
    except HTTPException:
        raise
    except Exception:
        _LOG.exception("Failed to register device token for user %s", user_id)
        raise HTTPException(status_code=500, detail="Failed to register token")
    finally:
        if conn is not None:
            put_conn(conn)


@router.post("/opened", status_code=204)
def notification_opened(
    body: OpenedRequest,
    user_id: UUID = Depends(get_current_user_id),
):
    conn = None
    try:
        conn = get_conn()
        mark_notification_opened(conn, body.queue_id)
    except Exception:
        _LOG.warning("Failed to mark notification opened: %s", body.queue_id)
    finally:
        if conn is not None:
            put_conn(conn)
