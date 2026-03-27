"""Expo Push Notification sender (KAN-71).

Sends notifications via the Expo Push API:
https://docs.expo.dev/push-notifications/sending-notifications/

Batches up to 100 messages per HTTP call (Expo limit).
Returns per-message status so callers can log failures.
"""
from __future__ import annotations

import json
import logging
import urllib.request
from dataclasses import dataclass
from typing import Any

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
    """Send up to 100 push messages. Returns one receipt per message."""
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
