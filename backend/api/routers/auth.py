from __future__ import annotations

from uuid import uuid4

from fastapi import APIRouter, Depends, Header

from api.auth import create_token, get_current_user_id, get_optional_principal
from api.errors import error_response
from api.schemas import (
    AuthUserResponse,
    DeleteAccountResponse,
    LoginRequest,
    RegisterRequest,
    AnonymousSessionResponse,
)
from api.store import (
    create_user,
    delete_user,
    get_user,
    get_user_by_email,
    migrate_anonymous_profile,
    verify_password,
)

router = APIRouter(prefix="/auth", tags=["auth"])


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


@router.delete("/account", response_model=DeleteAccountResponse)
def delete_account(user_id=Depends(get_current_user_id)):
    user = get_user(user_id)
    if user is None:
        error_response(404, "USER_NOT_FOUND", "Account not found.")
    delete_user(user_id)
    return DeleteAccountResponse(user_id=user_id)
