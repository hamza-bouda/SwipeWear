from __future__ import annotations

import json
import logging
import os
from uuid import uuid4

import requests
from fastapi import APIRouter, Depends, Header

from api import firebase_auth
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
    get_user,
    migrate_anonymous_profile,
    upsert_external_user,
)

_LOG = logging.getLogger("swipewear.api.auth")

router = APIRouter(prefix="/auth", tags=["auth"])

_ADMIN_TIMEOUT_SECONDS = 10
_IDENTITY_SCOPE = "https://www.googleapis.com/auth/identitytoolkit"


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
    """Provision the local account behind a Firebase session.

    There is no register endpoint any more: Firebase owns credentials, the
    Google handshake and phone verification. The first time a valid Firebase
    token reaches us, the account is created here — and anything the visitor
    did beforehand is carried over.
    """
    if not firebase_auth.is_configured():
        error_response(
            503, "AUTH_PROVIDER_UNCONFIGURED",
            "La connexion est indisponible : le fournisseur d'identité n'est "
            "pas configuré.",
        )

    user_id, is_anonymous = resolve_identity(authorization)
    if is_anonymous:
        error_response(
            401, "ACCOUNT_REQUIRED",
            "Cet endpoint attend un jeton de session Firebase.",
        )

    # resolve_identity has already verified the signature; re-reading the
    # claims here is what gives us the email, the phone and the provider.
    _, _, token = (authorization or "").partition(" ")
    claims = firebase_auth.verify(token)
    record = upsert_external_user(
        claims.user_id, claims.email, claims.provider,
        provider_uid=claims.firebase_uid, phone_number=claims.phone_number,
    )

    profile_migrated = False
    if body.anonymous_user_id is not None and body.anonymous_user_id != user_id:
        profile_migrated = migrate_anonymous_profile(
            body.anonymous_user_id, claims.user_id,
        )

    return AuthUserResponse(
        user_id=record.user_id,
        email=record.email,
        phone_number=record.phone_number,
        provider=claims.provider,
        profile_migrated=profile_migrated,
    )


def _service_account_info() -> dict | None:
    """Load the service account used to reach the Firebase admin API.

    Accepts the JSON inline (FIREBASE_SERVICE_ACCOUNT_JSON, which is how
    Railway and most hosts inject it) or a path to the file
    (GOOGLE_APPLICATION_CREDENTIALS, the local convention).
    """
    inline = (os.getenv("FIREBASE_SERVICE_ACCOUNT_JSON") or "").strip()
    if inline:
        try:
            return json.loads(inline)
        except ValueError:
            _LOG.error("FIREBASE_SERVICE_ACCOUNT_JSON is not valid JSON.")
            return None

    path = (os.getenv("GOOGLE_APPLICATION_CREDENTIALS") or "").strip()
    if path and os.path.exists(path):
        try:
            with open(path, encoding="utf-8") as handle:
                return json.load(handle)
        except (OSError, ValueError) as exc:
            _LOG.error("Could not read the service account file: %s", exc)
    return None


def _delete_firebase_user(firebase_uid: str) -> bool:
    """Erase the identity at Firebase. False if it could not be done.

    google-auth is already a dependency here, so minting the access token from
    the service account avoids pulling in the whole firebase-admin SDK for one
    call.
    """
    info = _service_account_info()
    if not info or not firebase_auth.is_configured():
        return False
    try:
        from google.auth.transport.requests import Request as GoogleRequest
        from google.oauth2 import service_account

        credentials = service_account.Credentials.from_service_account_info(
            info, scopes=[_IDENTITY_SCOPE],
        )
        credentials.refresh(GoogleRequest())
        response = requests.post(
            "https://identitytoolkit.googleapis.com/v1/projects/"
            f"{firebase_auth.project_id()}/accounts:delete",
            headers={"Authorization": f"Bearer {credentials.token}"},
            json={"localId": firebase_uid},
            timeout=_ADMIN_TIMEOUT_SECONDS,
        )
    except Exception as exc:  # noqa: BLE001 - any failure means "not deleted"
        _LOG.error("Firebase admin delete failed for %s: %s", firebase_uid, exc)
        return False
    if response.status_code == 200:
        return True
    # A user already gone is the state we wanted.
    if response.status_code == 400 and "USER_NOT_FOUND" in response.text:
        return True
    _LOG.error(
        "Firebase admin delete returned %s: %s",
        response.status_code, response.text[:200],
    )
    return False


@router.delete("/account", response_model=DeleteAccountResponse)
def delete_account(user_id=Depends(require_account)):
    """Erase the account here and at Firebase (GDPR erasure).

    Deleting our rows alone would leave the person able to sign in again and be
    re-provisioned on the spot, so the deletion would not be one. If the
    provider cannot be reached we refuse rather than report a success we did
    not achieve.
    """
    record = get_user(user_id)
    if record is None:
        error_response(404, "USER_NOT_FOUND", "Compte introuvable.")
    if not record.provider_uid:
        # Pre-KAN-91 rows have no upstream id, so the identity cannot be
        # reached. Saying so beats deleting half of it.
        error_response(
            409, "PROVIDER_UID_MISSING",
            "Ce compte ne peut pas être supprimé automatiquement. Contacte le "
            "support.",
        )
    if not _delete_firebase_user(record.provider_uid):
        error_response(
            502, "PROVIDER_DELETE_FAILED",
            "Ton compte n'a pas pu être supprimé pour le moment. Rien n'a été "
            "retiré ; réessaie.",
        )
    delete_user(user_id)
    return DeleteAccountResponse(user_id=user_id)
