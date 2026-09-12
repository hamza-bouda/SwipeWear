"""Push notification sender for legacy Expo and native Flutter tokens.

Sends notifications via the Expo Push API:
https://docs.expo.dev/push-notifications/sending-notifications/

Batches up to 100 messages per HTTP call (Expo limit).
Returns per-message status so callers can log failures.
"""
from __future__ import annotations

import json
import logging
import os
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any

import requests

_LOG = logging.getLogger("swipewear.notifications.push_sender")

EXPO_PUSH_URL = "https://exp.host/--/api/v2/push/send"
_MAX_BATCH = 100


@dataclass
class PushMessage:
    to: str
    title: str
    body: str
    data: dict[str, Any]
    sound: str = "default"
    badge: int = 1


@dataclass
class PushReceipt:
    token: str
    status: str
    message: str | None = None


def send_batch(messages: list[PushMessage]) -> list[PushReceipt]:
    """Send Expo and native FCM messages, preserving input order.

    Existing Expo tokens remain supported during the migration. Flutter uses
    Firebase tokens; those are sent through FCM HTTP v1 when a Firebase
    service-account credential is configured. The adapter is deliberately
    isolated so the alert queue and its Premium/free scheduling do not change.
    """
    if not messages:
        return []

    receipts_by_token: dict[str, PushReceipt] = {}
    expo = [m for m in messages if m.to.startswith("ExponentPushToken[")]
    native = [m for m in messages if not m.to.startswith("ExponentPushToken[")]
    receipts_by_token.update({receipt.token: receipt for receipt in _send_expo_batch(expo)})
    receipts_by_token.update({receipt.token: receipt for receipt in _send_fcm_batch(native)})
    return [receipts_by_token[m.to] for m in messages]


def _send_expo_batch(messages: list[PushMessage]) -> list[PushReceipt]:
    if not messages:
        return []

    payload = [
        {
            "to": m.to,
            "title": m.title,
            "body": m.body,
            "data": m.data,
            "sound": m.sound,
            "badge": m.badge,
        }
        for m in messages
    ]
    body = json.dumps(payload).encode()
    req = urllib.request.Request(
        EXPO_PUSH_URL,
        data=body,
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Accept-Encoding": "gzip, deflate",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            result = json.loads(resp.read().decode())
    except Exception:
        _LOG.error("Expo push API call failed", exc_info=True)
        return [PushReceipt(token=m.to, status="error", message="network error") for m in messages]

    receipts: list[PushReceipt] = []
    for msg, item in zip(messages, result.get("data", [])):
        status = item.get("status", "error")
        receipts.append(PushReceipt(
            token=msg.to,
            status=status,
            message=item.get("message"),
        ))
        if status != "ok":
            _LOG.warning("Push failed for token %s: %s", msg.to, item.get("message"))
    return receipts


def _firebase_service_account() -> dict[str, Any] | None:
    """Read the Firebase service account from the deployment secret store.

    FCM HTTP v1 needs a short-lived OAuth token, not the deprecated server key.
    The JSON is deliberately read only from the environment so no credential
    file or private key can enter the repository image.
    """
    raw = os.getenv("FIREBASE_SERVICE_ACCOUNT_JSON", "").strip()
    if not raw:
        return None
    try:
        account = json.loads(raw)
    except json.JSONDecodeError:
        _LOG.error("FIREBASE_SERVICE_ACCOUNT_JSON is not valid JSON")
        return None
    if not isinstance(account, dict):
        _LOG.error("FIREBASE_SERVICE_ACCOUNT_JSON must be a JSON object")
        return None
    if not account.get("client_email") or not account.get("private_key"):
        _LOG.error("Firebase service account is missing client_email/private_key")
        return None
    return account


def _send_fcm_batch(messages: list[PushMessage]) -> list[PushReceipt]:
    if not messages:
        return []
    account = _firebase_service_account()
    if account is not None:
        return _send_fcm_v1_batch(messages, account)

    # Keep a compatibility path for an already deployed legacy setup. New
    # deployments should use the HTTP v1 path above because FCM server keys
    # are no longer the scalable/native integration.
    server_key = os.getenv("FCM_SERVER_KEY", "").strip()
    if not server_key:
        _LOG.error(
            "Native push token received but Firebase HTTP v1 is not configured"
        )
        return [
            PushReceipt(token=m.to, status="error", message="FCM not configured")
            for m in messages
        ]

    return _send_fcm_legacy_batch(messages, server_key)


def _send_fcm_v1_batch(
    messages: list[PushMessage],
    account: dict[str, Any],
) -> list[PushReceipt]:
    """Send native messages through Firebase Cloud Messaging HTTP v1.

    HTTP v1 accepts one registration token per request. The dispatcher already
    bounds a flush to 500 queue rows, and this small loop keeps each receipt
    associated with its exact token and message instead of applying the first
    message's body to every device in a batch.
    """
    configured_project = os.getenv("FCM_PROJECT_ID", "").strip()
    account_project = account.get("project_id")
    project_id = configured_project or (
        str(account_project).strip() if account_project else ""
    )
    if not project_id:
        _LOG.error("Firebase service account has no project_id and FCM_PROJECT_ID is empty")
        return [
            PushReceipt(token=m.to, status="error", message="FCM project missing")
            for m in messages
        ]

    try:
        from google.auth.transport.requests import Request
        from google.oauth2 import service_account

        credentials = service_account.Credentials.from_service_account_info(
            account,
            scopes=["https://www.googleapis.com/auth/firebase.messaging"],
        )
        credentials.refresh(Request())
        access_token = credentials.token
    except Exception:  # noqa: BLE001 - one bad credential must not kill the worker
        _LOG.error("Could not obtain a Firebase HTTP v1 access token", exc_info=True)
        return [
            PushReceipt(token=m.to, status="error", message="FCM authentication error")
            for m in messages
        ]

    endpoint = f"https://fcm.googleapis.com/v1/projects/{project_id}/messages:send"
    receipts: list[PushReceipt] = []
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }
    for message in messages:
        payload = {
            "message": {
                "token": message.to,
                "notification": {
                    "title": message.title,
                    "body": message.body,
                },
                "data": {key: str(value) for key, value in message.data.items()},
                "android": {"notification": {"sound": message.sound}},
                "apns": {"payload": {"aps": {"sound": message.sound}}},
            }
        }
        try:
            response = requests.post(endpoint, headers=headers, json=payload, timeout=10)
            if response.ok:
                receipts.append(PushReceipt(token=message.to, status="ok"))
            else:
                _LOG.warning(
                    "FCM HTTP v1 rejected token %s: %s",
                    message.to,
                    response.text[:300],
                )
                receipts.append(
                    PushReceipt(
                        token=message.to,
                        status="error",
                        message=f"HTTP {response.status_code}",
                    )
                )
        except requests.RequestException:
            _LOG.error("FCM HTTP v1 request failed for token %s", message.to, exc_info=True)
            receipts.append(
                PushReceipt(token=message.to, status="error", message="network error")
            )
    return receipts


def _send_fcm_legacy_batch(
    messages: list[PushMessage],
    server_key: str,
) -> list[PushReceipt]:
    """Compatibility sender for installations not yet migrated to HTTP v1."""

    payload = {
        "registration_ids": [m.to for m in messages],
        "notification": {
            "title": messages[0].title,
            "body": messages[0].body,
            "sound": messages[0].sound,
        },
        "data": messages[0].data,
    }
    request = urllib.request.Request(
        "https://fcm.googleapis.com/fcm/send",
        data=json.dumps(payload).encode(),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"key={server_key}",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            result = json.loads(response.read().decode())
    except (OSError, ValueError, urllib.error.URLError):
        _LOG.error("FCM push API call failed", exc_info=True)
        return [PushReceipt(token=m.to, status="error", message="network error") for m in messages]

    results = result.get("results", [])
    receipts = []
    for index, message in enumerate(messages):
        item = results[index] if index < len(results) else {}
        status = "ok" if "message_id" in item else "error"
        receipts.append(PushReceipt(token=message.to, status=status, message=item.get("error")))
    return receipts
