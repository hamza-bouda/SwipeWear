from __future__ import annotations

from uuid import uuid4

from fastapi import APIRouter, Depends

from api.auth import create_token, get_current_user_id
from api.errors import error_response
from api.schemas import (
    AuthUserResponse,
    DeleteAccountResponse,
    LoginRequest,
    RegisterRequest,
    TokenRequest,
    TokenResponse,
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


@router.post("/token", response_model=TokenResponse)
def issue_token(body: TokenRequest):
    token = create_token(body.user_id)
    return TokenResponse(access_token=token)


@router.post("/register", response_model=AuthUserResponse)
def register(body: RegisterRequest):
    existing = get_user_by_email(body.email)
    if existing is not None:
        error_response(409, "EMAIL_TAKEN", "An account with this email already exists.")

    user_id = uuid4()
    create_user(user_id, body.email, body.password)

    profile_migrated = False
    if body.anonymous_user_id is not None:
        profile_migrated = migrate_anonymous_profile(body.anonymous_user_id, user_id)

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
