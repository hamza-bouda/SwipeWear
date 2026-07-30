"""Verification of Firebase-issued ID tokens.

Firebase owns credentials, the Google handshake and phone verification. This
module answers one question: is this bearer token genuinely signed by Google
for our project, and for whom.

**Firebase user ids are not UUIDs.** `sub` is a 28-character opaque string,
while `user_id` is a UUID in ten database columns and in four models under
`contracts/` — a zone that may not be modified without both lanes agreeing
(CLAUDE.md §4, §8). Rather than migrate all of that, the local id is derived
from the Firebase uid with UUIDv5: deterministic, so the same person always
resolves to the same row, and namespaced by project so two Firebase projects
can never collide. The original uid is stored alongside, because deleting the
account upstream needs it.

KAN-91
"""
from __future__ import annotations

import logging
import os
import uuid
from dataclasses import dataclass
from uuid import UUID

import jwt
from jwt import PyJWKClient

from api.errors import error_response

_LOG = logging.getLogger("swipewear.api.firebase_auth")

# Google publishes the public halves of the Firebase signing keys here, in
# JWKS form. (The x509 endpoint carries the same keys as PEM certificates;
# this one plugs straight into PyJWT.)
_JWKS_URL = (
    "https://www.googleapis.com/service_accounts/v1/jwk/"
    "securetoken@system.gserviceaccount.com"
)
_JWKS_CACHE_SECONDS = 3600
_ALGORITHMS = ["RS256"]


def project_id() -> str:
    return (os.getenv("FIREBASE_PROJECT_ID") or "").strip()


def is_configured() -> bool:
    return bool(project_id())


def issuer() -> str:
    return f"https://securetoken.google.com/{project_id()}"


_jwks_client: PyJWKClient | None = None


def _client() -> PyJWKClient:
    global _jwks_client
    if _jwks_client is None:
        _jwks_client = PyJWKClient(
            _JWKS_URL, cache_keys=True, lifespan=_JWKS_CACHE_SECONDS,
        )
    return _jwks_client


def reset_cache() -> None:
    """Drop the cached signing keys. Used by tests; harmless in production."""
    global _jwks_client
    _jwks_client = None


def local_user_id(firebase_uid: str) -> UUID:
    """Stable UUID for a Firebase uid, scoped to this project.

    Deterministic on purpose: it is recomputed on every request rather than
    stored and looked up, so there is no mapping table to fall out of sync.
    """
    return uuid.uuid5(uuid.NAMESPACE_URL, f"{issuer()}/{firebase_uid}")


@dataclass(frozen=True)
class FirebaseClaims:
    user_id: UUID
    firebase_uid: str
    email: str | None
    phone_number: str | None
    provider: str


def looks_like_firebase_token(token: str) -> bool:
    """Whether this token claims to come from our Firebase project.

    Read without verifying, and used only to route the token to the right
    verifier — never to trust anything in it. A forged `iss` buys an attacker
    nothing but a signature check it cannot pass.
    """
    if not is_configured():
        return False
    try:
        unverified = jwt.decode(token, options={"verify_signature": False})
    except jwt.PyJWTError:
        return False
    return unverified.get("iss") == issuer()


def verify(token: str) -> FirebaseClaims:
    """Verify signature, expiry, issuer and audience, or raise 401."""
    try:
        signing_key = _client().get_signing_key_from_jwt(token)
        payload = jwt.decode(
            token,
            signing_key.key,
            # Only RS256 is ever accepted. Allowing HS256 here would let a
            # token re-signed with the public key as an HMAC secret pass, and
            # that key is public by definition.
            algorithms=_ALGORITHMS,
            audience=project_id(),
            issuer=issuer(),
        )
    except jwt.ExpiredSignatureError:
        error_response(401, "TOKEN_EXPIRED", "Session expirée. Reconnecte-toi.")
    except jwt.PyJWTError as exc:
        # The reason stays in the log rather than the response: telling a
        # caller which check failed helps them craft the next attempt.
        _LOG.warning("Rejected a Firebase token: %s", exc)
        error_response(401, "INVALID_TOKEN", "Jeton d'authentification invalide.")

    firebase_uid = str(payload.get("sub") or "").strip()
    if not firebase_uid:
        error_response(401, "INVALID_TOKEN", "Token missing valid 'sub' claim.")

    firebase_claims = payload.get("firebase") or {}
    return FirebaseClaims(
        user_id=local_user_id(firebase_uid),
        firebase_uid=firebase_uid,
        email=payload.get("email") or None,
        phone_number=payload.get("phone_number") or None,
        # password | google.com | phone — what the person actually used.
        provider=str(firebase_claims.get("sign_in_provider") or "unknown"),
    )
