from __future__ import annotations

import os
from uuid import uuid4

import requests
from fastapi import APIRouter, Depends, Header

from api.auth import create_token, get_current_user_id, get_optional_principal
from api.errors import error_response
from api.schemas import (
    AuthUserResponse,
    DeleteAccountResponse,
    LoginRequest,
    GoogleLoginRequest,
    RegisterRequest,
    AnonymousSessionResponse,
)
from api.store import (
    create_user,
    delete_user,
    get_user_by_email,
    migrate_anonymous_profile,
    verify_password,
)

router = APIRouter(prefix="/auth", tags=["auth"])

_GOOGLE_TOKENINFO_URL = "https://oauth2.googleapis.com/tokeninfo"


def _verify_google_identity(id_token: str) -> str:
    """Return the verified Google email address for an OpenID Connect token."""
    client_id = os.getenv("GOOGLE_OAUTH_CLIENT_ID", "").strip()
    if not client_id:
        error_response(
            503,
            "GOOGLE_LOGIN_UNAVAILABLE",
            "Google sign-in is not configured on this deployment.",
        )
    try:
        response = requests.get(
            _GOOGLE_TOKENINFO_URL,
            params={"id_token": id_token},
            timeout=5,
        )
        response.raise_for_status()
        claims = response.json()
    except (requests.RequestException, ValueError):
        error_response(401, "INVALID_GOOGLE_TOKEN", "Google token could not be verified.")

    if (
        claims.get("aud") != client_id
        or claims.get("iss") not in {"accounts.google.com", "https://accounts.google.com"}
        or str(claims.get("email_verified", "")).lower() != "true"
    ):
        error_response(401, "INVALID_GOOGLE_TOKEN", "Google token is not valid for this app.")
    email = claims.get("email")
    if not isinstance(email, str) or not email:
        error_response(401, "INVALID_GOOGLE_TOKEN", "Google token has no verified email.")
    return email.lower()


@router.post("/anonymous", response_model=AnonymousSessionResponse, status_code=201)
def create_anonymous_session():
    """Create an unguessable browsing identity on the server.

    The former /auth/token endpoint signed any UUID supplied by a client,
    which let an attacker impersonate a known user. The UUID and its token are
    now created together and the client can only retain the issued session.
    """
    user_id = uuid4()
    return AnonymousSessionResponse(
        user_id=user_id,
        access_token=create_token(user_id, kind="anonymous"),
    )


@router.post("/register", response_model=AuthUserResponse)
def register(
    body: RegisterRequest,
    authorization: str | None = Header(default=None),
):
    anonymous = get_optional_principal(authorization)
    if anonymous is not None and anonymous.kind != "anonymous":
        error_response(
            409,
            "ALREADY_AUTHENTICATED",
            "An account session cannot register again.",
        )

    existing = get_user_by_email(body.email)
    if existing is not None:
        error_response(409, "EMAIL_TAKEN", "An account with this email already exists.")

    user_id = uuid4()
    create_user(user_id, body.email, body.password)

    profile_migrated = False
    if anonymous is not None:
        profile_migrated = migrate_anonymous_profile(anonymous.user_id, user_id)

    token = create_token(user_id)
    return AuthUserResponse(
        user_id=user_id,
        email=body.email.lower(),
        access_token=token,
        profile_migrated=profile_migrated,
    )


@router.post("/login", response_model=AuthUserResponse)
def login(body: LoginRequest):
    user = get_user_by_email(body.email)
    if user is None:
        error_response(401, "INVALID_CREDENTIALS", "Invalid email or password.")
    if not verify_password(body.password, user.password_hash):
        error_response(401, "INVALID_CREDENTIALS", "Invalid email or password.")

    token = create_token(user.user_id)
    return AuthUserResponse(
        user_id=user.user_id,
        email=user.email,
        access_token=token,
    )


@router.post("/google", response_model=AuthUserResponse)
def login_with_google(
    body: GoogleLoginRequest,
    authorization: str | None = Header(default=None),
):
    email = _verify_google_identity(body.id_token)
    anonymous = get_optional_principal(authorization)
    if anonymous is not None and anonymous.kind != "anonymous":
        error_response(
            409,
            "ALREADY_AUTHENTICATED",
            "An account session cannot be replaced by Google sign-in.",
        )
    user = get_user_by_email(email)
    profile_migrated = False
    if user is None:
        # Google has already verified possession of the email. A random local
        # password keeps the existing account schema and means password login
        # is never accidentally enabled for an OAuth-only account.
        user = create_user(uuid4(), email, uuid4().hex + uuid4().hex)
    if anonymous is not None:
        profile_migrated = migrate_anonymous_profile(anonymous.user_id, user.user_id)
    return AuthUserResponse(
        user_id=user.user_id,
        email=user.email,
        access_token=create_token(user.user_id),
        profile_migrated=profile_migrated,
    )


@router.delete("/account", response_model=DeleteAccountResponse)
def delete_account(user_id=Depends(get_current_user_id)):
    delete_user(user_id)
    return DeleteAccountResponse(user_id=user_id)
