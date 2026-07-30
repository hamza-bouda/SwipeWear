from __future__ import annotations

import logging
from uuid import UUID, uuid4

import requests
from fastapi import APIRouter, Depends, Header

from api import supabase_auth
from api.auth import create_anonymous_token, require_account, resolve_identity
from api.errors import error_response
from api.schemas import (
    AnonymousSessionResponse,
    AuthUserResponse,
    DeleteAccountResponse,
    SyncAccountRequest,
)
from api.store import (
    delete_user,
    migrate_anonymous_profile,
    upsert_external_user,
)

_LOG = logging.getLogger("swipewear.api.auth")

router = APIRouter(prefix="/auth", tags=["auth"])

_ADMIN_TIMEOUT_SECONDS = 10


@router.post("/anonymous", response_model=AnonymousSessionResponse)
def start_anonymous_session():
    """Hand out a throwaway identity so a visitor can browse before signing up.

    Replaces POST /auth/token, which signed whatever user_id the caller put in
    the body without asking for any credential — knowing an id was enough to
    read, modify and delete that person's account.
    """
    user_id = uuid4()
    return AnonymousSessionResponse(
        user_id=user_id, access_token=create_anonymous_token(user_id),
    )


@router.post("/sync", response_model=AuthUserResponse)
def sync_account(
    body: SyncAccountRequest,
    authorization: str | None = Header(default=None),
):
    """Provision the local account behind a Supabase session.

    There is no register endpoint any more: Supabase owns credentials and the
    OAuth handshakes. The first time a valid Supabase token reaches us, the
    account is created here — and anything the visitor did beforehand is
    carried over.
    """
    if not supabase_auth.is_configured():
        error_response(
            503, "AUTH_PROVIDER_UNCONFIGURED",
            "Sign-in is unavailable: the identity provider is not configured.",
        )

    user_id, is_anonymous = resolve_identity(authorization)
    if is_anonymous:
        error_response(
            401, "ACCOUNT_REQUIRED",
            "This endpoint expects a Supabase session token.",
        )

    # resolve_identity has already verified the signature; re-reading the
    # claims here is what gives us the email and the provider.
    scheme, _, token = (authorization or "").partition(" ")
    claims = supabase_auth.verify(token)
    # Answer with what was stored, not with the raw claim: the address is
    # lowercased on the way in, and returning the provider's casing would let
    # the client believe in an address the database does not hold.
    record = upsert_external_user(claims.user_id, claims.email, claims.provider)

    profile_migrated = False
    if body.anonymous_user_id is not None and body.anonymous_user_id != user_id:
        profile_migrated = migrate_anonymous_profile(
            body.anonymous_user_id, claims.user_id,
        )

    return AuthUserResponse(
        user_id=record.user_id,
        email=record.email,
        provider=claims.provider,
        profile_migrated=profile_migrated,
    )


def _delete_supabase_user(user_id: UUID) -> bool:
    """Erase the identity at the provider. Returns False if it could not be done."""
    key = supabase_auth.service_role_key()
    if not supabase_auth.is_configured() or not key:
        return False
    try:
        response = requests.delete(
            f"{supabase_auth.issuer()}/admin/users/{user_id}",
            headers={"apikey": key, "Authorization": f"Bearer {key}"},
            timeout=_ADMIN_TIMEOUT_SECONDS,
        )
    except requests.RequestException as exc:
        _LOG.error("Supabase admin delete failed for %s: %s", user_id, exc)
        return False
    # 404 means the identity is already gone, which is the state we wanted.
    return response.status_code in (200, 204, 404)


@router.delete("/account", response_model=DeleteAccountResponse)
def delete_account(user_id: UUID = Depends(require_account)):
    """Erase the account here and at the identity provider (GDPR erasure).

    Deleting our rows alone would leave the person able to sign in again and be
    re-provisioned on the spot, so the deletion would not be one. If the
    provider cannot be reached we refuse rather than report a success we did
    not achieve.
    """
    if not _delete_supabase_user(user_id):
        error_response(
            502, "PROVIDER_DELETE_FAILED",
            "Your account could not be deleted right now. Nothing was removed; "
            "please try again.",
        )
    delete_user(user_id)
    return DeleteAccountResponse(user_id=user_id)
