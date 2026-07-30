"""Verification of Supabase-issued access tokens.

Accounts are no longer ours to hold. Supabase owns the credentials, the OAuth
handshakes with Google and Apple, the password resets and the email
confirmations; this module only answers one question — is this bearer token
genuinely signed by our Supabase project, and for whom.

The `sub` claim is a UUID, and it is used directly as our `users.user_id`.
Keeping a second identifier and a mapping table would create two ways to name
the same person, and therefore a way for them to disagree.

KAN-90
"""
from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from uuid import UUID

import jwt
from jwt import PyJWKClient

from api.errors import error_response

_LOG = logging.getLogger("swipewear.api.supabase_auth")

# Every Supabase user token carries this audience. Tokens minted for other
# audiences (service role, anon key) must not authenticate a person.
_AUDIENCE = "authenticated"
_JWKS_CACHE_SECONDS = 600
_ASYMMETRIC_ALGORITHMS = ["RS256", "ES256"]


def supabase_url() -> str:
    return (os.getenv("SUPABASE_URL") or "").strip().rstrip("/")


def _jwt_secret() -> str:
    """Legacy shared HS256 secret, for projects not yet on signing keys."""
    return (os.getenv("SUPABASE_JWT_SECRET") or "").strip()


def service_role_key() -> str:
    """Admin key. Only ever used server-side, never handed to a client."""
    return (os.getenv("SUPABASE_SERVICE_ROLE_KEY") or "").strip()


def is_configured() -> bool:
    return bool(supabase_url())


def issuer() -> str:
    return f"{supabase_url()}/auth/v1"


_jwks_client: PyJWKClient | None = None


def _client() -> PyJWKClient:
    global _jwks_client
    if _jwks_client is None:
        _jwks_client = PyJWKClient(
            f"{issuer()}/.well-known/jwks.json",
            cache_keys=True,
            lifespan=_JWKS_CACHE_SECONDS,
        )
    return _jwks_client


def reset_cache() -> None:
    """Drop the cached JWKS client. Used by tests; harmless in production."""
    global _jwks_client
    _jwks_client = None


@dataclass(frozen=True)
class SupabaseClaims:
    user_id: UUID
    email: str | None
    provider: str


def looks_like_supabase_token(token: str) -> bool:
    """Whether this token claims to come from our Supabase project.

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


def verify(token: str) -> SupabaseClaims:
    """Verify signature, expiry, issuer and audience, or raise 401."""
    try:
        algorithm = (jwt.get_unverified_header(token) or {}).get("alg")
    except jwt.PyJWTError:
        error_response(401, "INVALID_TOKEN", "Malformed token.")

    try:
        # The key source is chosen by algorithm, and each branch passes an
        # explicit allowlist. There is no path where a public key is accepted
        # as an HMAC secret, which is the algorithm-confusion attack this
        # shape is usually vulnerable to.
        if algorithm == "HS256":
            secret = _jwt_secret()
            if not secret:
                error_response(
                    401, "INVALID_TOKEN",
                    "This project does not accept shared-secret tokens.",
                )
            payload = jwt.decode(
                token, secret, algorithms=["HS256"],
                audience=_AUDIENCE, issuer=issuer(),
            )
        else:
            signing_key = _client().get_signing_key_from_jwt(token)
            payload = jwt.decode(
                token, signing_key.key, algorithms=_ASYMMETRIC_ALGORITHMS,
                audience=_AUDIENCE, issuer=issuer(),
            )
    except jwt.ExpiredSignatureError:
        error_response(401, "TOKEN_EXPIRED", "Session expired. Sign in again.")
    except jwt.PyJWTError as exc:
        # The reason stays in the log rather than the response: telling a
        # caller which check failed helps them craft the next attempt.
        _LOG.warning("Rejected a Supabase token: %s", exc)
        error_response(401, "INVALID_TOKEN", "Invalid authentication token.")

    try:
        user_id = UUID(str(payload["sub"]))
    except (KeyError, ValueError):
        error_response(401, "INVALID_TOKEN", "Token missing valid 'sub' claim.")

    email = payload.get("email") or None
    provider = str(
        (payload.get("app_metadata") or {}).get("provider") or "unknown"
    )
    return SupabaseClaims(user_id=user_id, email=email, provider=provider)
