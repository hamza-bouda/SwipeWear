from __future__ import annotations

import hashlib
import hmac
import json
import time
from uuid import UUID

from fastapi import Header

from api.config import require_secret
from api.errors import error_response

# .env has always called this JWT_SECRET while this module read JWT_SECRET_KEY,
# so the configured value was never loaded and every token was signed with the
# development literal below — which is public in this repository, and lets
# anyone forge a token for any user. JWT_SECRET_KEY stays accepted so an
# existing deployment that did set it keeps working.
SECRET_KEY = require_secret(
    "JWT_SECRET",
    "JWT_SECRET_KEY",
    dev_default="swipewear-dev-secret-change-in-prod",
)
TOKEN_TTL_SECONDS = 86400 * 30


def _b64url_encode(data: bytes) -> str:
    import base64
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def _b64url_decode(s: str) -> bytes:
    import base64
    padding = 4 - len(s) % 4
    return base64.urlsafe_b64decode(s + "=" * padding)


def create_token(user_id: UUID) -> str:
    header = _b64url_encode(json.dumps({"alg": "HS256", "typ": "JWT"}).encode())
    payload = _b64url_encode(json.dumps({
        "sub": str(user_id),
        "iat": int(time.time()),
        "exp": int(time.time()) + TOKEN_TTL_SECONDS,
    }).encode())
    signing_input = f"{header}.{payload}"
    signature = _b64url_encode(
        hmac.new(SECRET_KEY.encode(), signing_input.encode(), hashlib.sha256).digest()
    )
    return f"{header}.{payload}.{signature}"


def _decode_token(token: str) -> dict:
    parts = token.split(".")
    if len(parts) != 3:
        error_response(401, "INVALID_TOKEN", "Malformed token.")

    header_b64, payload_b64, signature_b64 = parts
    signing_input = f"{header_b64}.{payload_b64}"
    expected_sig = hmac.new(
        SECRET_KEY.encode(), signing_input.encode(), hashlib.sha256
    ).digest()
    actual_sig = _b64url_decode(signature_b64)
    if not hmac.compare_digest(expected_sig, actual_sig):
        error_response(401, "INVALID_TOKEN", "Invalid signature.")

    payload = json.loads(_b64url_decode(payload_b64))
    if payload.get("exp", 0) < time.time():
        error_response(401, "TOKEN_EXPIRED", "Token has expired.")
    return payload


def get_current_user_id(authorization: str = Header(...)) -> UUID:
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        error_response(401, "INVALID_AUTH", "Expected 'Bearer <token>' header.")
    payload = _decode_token(token)
    try:
        return UUID(payload["sub"])
    except (KeyError, ValueError):
        error_response(401, "INVALID_TOKEN", "Token missing valid 'sub' claim.")
        raise  # unreachable, keeps type checker happy
