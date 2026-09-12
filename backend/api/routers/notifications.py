from __future__ import annotations

import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, model_validator

from api.auth import get_current_user_id
from api.db import get_conn, put_conn
from notifications.notification_store import (
    get_notification_preference,
    mark_notification_opened,
    register_device_token,
    set_notification_preference,
)

_LOG = logging.getLogger("swipewear.api.notifications")

router = APIRouter(prefix="/notifications", tags=["notifications"])


class DeviceTokenRequest(BaseModel):
    # `expo_token` stays accepted for existing installations. Flutter sends a
    # native FCM token through `device_token`.
    expo_token: str | None = None
    device_token: str | None = None
    platform: str = "unknown"

    @model_validator(mode="after")
    def token_is_present(self):
        if not self.expo_token and not self.device_token:
            raise ValueError("A device token is required")
        return self


class DeviceTokenResponse(BaseModel):
    registered: bool = True


class NotificationPreferenceRequest(BaseModel):
    preference: str  # instant | daily_digest | disabled


class NotificationPreferenceResponse(BaseModel):
    preference: str


class OpenedRequest(BaseModel):
    queue_id: str


@router.post("/register", response_model=DeviceTokenResponse, status_code=201)
def register_token(
    body: DeviceTokenRequest,
    user_id: UUID = Depends(get_current_user_id),
):
    token = body.expo_token or body.device_token
    if body.expo_token and not body.expo_token.startswith("ExponentPushToken["):
        raise HTTPException(status_code=400, detail="Invalid Expo push token format")
    if body.device_token and len(body.device_token) < 20:
        raise HTTPException(status_code=400, detail="Invalid device token format")
    conn = None
    try:
        conn = get_conn()
        register_device_token(conn, user_id, token, body.platform)
        return DeviceTokenResponse()
    except HTTPException:
        raise
    except Exception:
        _LOG.exception("Failed to register device token for user %s", user_id)
        raise HTTPException(status_code=500, detail="Failed to register token")
    finally:
        if conn is not None:
            put_conn(conn)


_VALID_PREFS = {"instant", "daily_digest", "disabled"}


@router.get("/preferences", response_model=NotificationPreferenceResponse)
def get_prefs(user_id: UUID = Depends(get_current_user_id)):
    conn = None
    try:
        conn = get_conn()
        pref = get_notification_preference(conn, user_id)
        return NotificationPreferenceResponse(preference=pref)
    finally:
        if conn is not None:
            put_conn(conn)


@router.patch("/preferences", response_model=NotificationPreferenceResponse)
def update_prefs(
    body: NotificationPreferenceRequest,
    user_id: UUID = Depends(get_current_user_id),
):
    if body.preference not in _VALID_PREFS:
        allowed = ", ".join(sorted(_VALID_PREFS))
        raise HTTPException(status_code=422, detail=f"Must be one of: {allowed}")
    conn = None
    try:
        conn = get_conn()
        set_notification_preference(conn, user_id, body.preference)
        return NotificationPreferenceResponse(preference=body.preference)
    except HTTPException:
        raise
    except Exception:
        _LOG.exception("Failed to update notification preference for user %s", user_id)
        raise HTTPException(status_code=500, detail="Failed to update preference")
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
        mark_notification_opened(conn, body.queue_id, user_id)
    except Exception:
        _LOG.warning("Failed to mark notification opened: %s", body.queue_id)
    finally:
        if conn is not None:
            put_conn(conn)
