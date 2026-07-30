"""Tests for auth: anonymous sessions, Firebase token verification, deletion.

Accounts moved to Firebase in KAN-91, so there is nothing here about
registering or signing in — the backend never sees a password. What it must
still get exactly right is deciding whether a bearer token is genuine, and for
whom. Those checks run against tokens signed with a keypair generated in the
test, which exercises the real verification path without needing a live
Firebase project.
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import time
import uuid
from uuid import UUID, uuid4

import jwt
import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi.testclient import TestClient

from api import firebase_auth, store
from api.app import app
from api.auth import create_anonymous_token

_PROJECT_ID = "swipewear-e0b74"
_ISSUER = f"https://securetoken.google.com/{_PROJECT_ID}"


@pytest.fixture(autouse=True)
def _clean_store():
    store.reset()
    yield
    store.reset()


@pytest.fixture()
def client():
    return TestClient(app)


@pytest.fixture()
def signing_key():
    return rsa.generate_private_key(public_exponent=65537, key_size=2048)


@pytest.fixture()
def firebase_project(monkeypatch, signing_key):
    """Point the verifier at a project whose signing key we control."""
    monkeypatch.setenv("FIREBASE_PROJECT_ID", _PROJECT_ID)

    class _Key:
        key = signing_key.public_key()

    class _Client:
        def get_signing_key_from_jwt(self, token):
            return _Key()

    monkeypatch.setattr(firebase_auth, "_jwks_client", _Client())
    yield
    firebase_auth.reset_cache()


def _b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def _token(key, *, sub="firebaseUid0123456789abcdef", email="user@example.com",
           phone=None, provider="google.com", issuer=_ISSUER,
           audience=_PROJECT_ID, expires_in=3600, algorithm="RS256"):
    now = int(time.time())
    payload = {
        "sub": sub,
        "user_id": sub,
        "iss": issuer,
        "aud": audience,
        "iat": now,
        "auth_time": now,
        "exp": now + expires_in,
        "firebase": {"sign_in_provider": provider, "identities": {}},
    }
    if email:
        payload["email"] = email
    if phone:
        payload["phone_number"] = phone
    return jwt.encode(payload, key, algorithm=algorithm)


class TestAnonymousSession:
    def test_server_generates_the_identity(self, client):
        resp = client.post("/auth/anonymous")
        assert resp.status_code == 200
        body = resp.json()
        assert UUID(body["user_id"])
        assert body["access_token"]

    def test_two_sessions_get_different_identities(self, client):
        first = client.post("/auth/anonymous").json()["user_id"]
        second = client.post("/auth/anonymous").json()["user_id"]
        assert first != second

    def test_caller_cannot_choose_the_identity(self, client):
        """The takeover this endpoint replaced.

        POST /auth/token signed whatever user_id was in the body, with no
        credential: knowing someone's id was enough to read, modify and delete
        their account. A body is now simply ignored, and the old path is gone.
        """
        victim = uuid4()
        resp = client.post("/auth/anonymous", json={"user_id": str(victim)})
        assert resp.status_code == 200
        assert resp.json()["user_id"] != str(victim)
        assert client.post("/auth/token", json={"user_id": str(victim)}).status_code == 404


class TestLocalUserIdDerivation:
    """Firebase uids are not UUIDs; ten database columns and four contracts are.

    Rather than migrate all of that, user_id is a UUIDv5 of the Firebase uid.
    These properties are what make that safe.
    """

    def test_the_same_uid_always_yields_the_same_uuid(self, firebase_project):
        first = firebase_auth.local_user_id("abc123")
        second = firebase_auth.local_user_id("abc123")
        assert first == second
        assert isinstance(first, UUID)

    def test_different_uids_yield_different_uuids(self, firebase_project):
        assert firebase_auth.local_user_id("abc123") != firebase_auth.local_user_id("abc124")

    def test_the_derivation_is_scoped_to_the_project(self, monkeypatch):
        """Two Firebase projects must not map the same uid onto one row."""
        monkeypatch.setenv("FIREBASE_PROJECT_ID", "project-one")
        first = firebase_auth.local_user_id("sharedUid")
        monkeypatch.setenv("FIREBASE_PROJECT_ID", "project-two")
        assert firebase_auth.local_user_id("sharedUid") != first

    def test_it_matches_a_hand_computed_uuid5(self, firebase_project):
        """Pins the algorithm: changing it would orphan every existing account."""
        expected = uuid.uuid5(uuid.NAMESPACE_URL, f"{_ISSUER}/knownUid")
        assert firebase_auth.local_user_id("knownUid") == expected


class TestFirebaseTokenVerification:
    def test_valid_token_is_accepted(self, firebase_project, signing_key):
        claims = firebase_auth.verify(_token(signing_key, sub="uid-42"))
        assert claims.firebase_uid == "uid-42"
        assert claims.user_id == firebase_auth.local_user_id("uid-42")
        assert claims.email == "user@example.com"
        assert claims.provider == "google.com"

    def test_phone_sign_in_has_no_email(self, firebase_project, signing_key):
        claims = firebase_auth.verify(_token(
            signing_key, email=None, phone="+33612345678", provider="phone",
        ))
        assert claims.email is None
        assert claims.phone_number == "+33612345678"
        assert claims.provider == "phone"

    def test_expired_token_is_rejected(self, firebase_project, signing_key):
        with pytest.raises(Exception) as exc:
            firebase_auth.verify(_token(signing_key, expires_in=-60))
        assert exc.value.status_code == 401
        assert exc.value.detail["error_code"] == "TOKEN_EXPIRED"

    def test_token_signed_by_another_key_is_rejected(self, firebase_project):
        attacker_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        with pytest.raises(Exception) as exc:
            firebase_auth.verify(_token(attacker_key))
        assert exc.value.status_code == 401

    def test_token_for_another_project_is_rejected(self, firebase_project, signing_key):
        """Google signs every Firebase project with the same keys.

        Without the audience check, a token minted by anybody else's Firebase
        project would authenticate here — the signature is genuine.
        """
        with pytest.raises(Exception) as exc:
            firebase_auth.verify(_token(signing_key, audience="someone-elses-app"))
        assert exc.value.status_code == 401

    def test_wrong_issuer_is_rejected(self, firebase_project, signing_key):
        with pytest.raises(Exception) as exc:
            firebase_auth.verify(_token(
                signing_key, issuer="https://securetoken.google.com/evil",
            ))
        assert exc.value.status_code == 401

    def test_hs256_forgery_is_refused(self, firebase_project, signing_key):
        """Guards against algorithm confusion.

        The classic attack re-signs a token as HS256 using the *public* key as
        the HMAC secret — and that key is public by definition. Assembled by
        hand because PyJWT refuses to encode it, which is a guard on the
        writing side only; a real attacker builds the bytes directly.
        """
        public_pem = signing_key.public_key().public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )
        header = _b64url(json.dumps({"alg": "HS256", "typ": "JWT"}).encode())
        payload = _b64url(json.dumps({
            "sub": "uid-forged", "iss": _ISSUER, "aud": _PROJECT_ID,
            "exp": int(time.time()) + 3600,
        }).encode())
        signature = _b64url(
            hmac.new(public_pem, f"{header}.{payload}".encode(), hashlib.sha256).digest()
        )
        with pytest.raises(Exception) as exc:
            firebase_auth.verify(f"{header}.{payload}.{signature}")
        assert exc.value.status_code == 401

    def test_foreign_issuer_is_not_routed_to_firebase(self, firebase_project, signing_key):
        token = _token(signing_key, issuer="https://other.example.com")
        assert firebase_auth.looks_like_firebase_token(token) is False

    def test_nothing_is_a_firebase_token_when_unconfigured(self, monkeypatch, signing_key):
        monkeypatch.delenv("FIREBASE_PROJECT_ID", raising=False)
        assert firebase_auth.looks_like_firebase_token(_token(signing_key)) is False


class TestAccountScopedEndpoints:
    def test_anonymous_token_cannot_delete_an_account(self, client):
        headers = {"Authorization": f"Bearer {create_anonymous_token(uuid4())}"}
        resp = client.delete("/auth/account", headers=headers)
        assert resp.status_code == 401
        assert resp.json()["detail"]["error_code"] == "ACCOUNT_REQUIRED"

    def test_sync_refuses_an_anonymous_token(self, client, firebase_project):
        headers = {"Authorization": f"Bearer {create_anonymous_token(uuid4())}"}
        assert client.post("/auth/sync", json={}, headers=headers).status_code == 401

    def test_sync_reports_unavailable_when_provider_unconfigured(
        self, client, monkeypatch,
    ):
        monkeypatch.delenv("FIREBASE_PROJECT_ID", raising=False)
        resp = client.post(
            "/auth/sync", json={},
            headers={"Authorization": f"Bearer {create_anonymous_token(uuid4())}"},
        )
        assert resp.status_code == 503
        assert resp.json()["detail"]["error_code"] == "AUTH_PROVIDER_UNCONFIGURED"

    def test_missing_auth_header_is_401_not_422(self, client):
        assert client.get("/profile").status_code == 401


@pytest.mark.requires_db
class TestSyncProvisioning:
    def test_first_sync_creates_the_account(self, client, firebase_project, signing_key):
        token = _token(signing_key, sub="uid-new", email="New@Example.com")
        resp = client.post(
            "/auth/sync", json={}, headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["user_id"] == str(firebase_auth.local_user_id("uid-new"))
        # Stored lowercased, so the same address cannot become two accounts.
        assert body["email"] == "new@example.com"

        record = store.get_user(firebase_auth.local_user_id("uid-new"))
        assert record is not None
        # The raw uid is kept: deleting upstream needs it, and the UUIDv5
        # derivation only computes one way.
        assert record.provider_uid == "uid-new"

    def test_phone_account_is_provisioned_without_an_email(
        self, client, firebase_project, signing_key,
    ):
        token = _token(
            signing_key, sub="uid-phone", email=None,
            phone="+33698765432", provider="phone",
        )
        resp = client.post(
            "/auth/sync", json={}, headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        assert resp.json()["email"] is None
        assert resp.json()["phone_number"] == "+33698765432"

    def test_sync_carries_over_the_anonymous_profile(
        self, client, firebase_project, signing_key,
    ):
        anonymous_id = uuid4()
        client.post(
            "/onboarding/styles",
            json={
                "style_ids": ["minimal"], "liked_brands": ["Carhartt"],
                "sizes": ["L"], "max_price_eur": 80.0, "gender": "men",
            },
            headers={"Authorization": f"Bearer {create_anonymous_token(anonymous_id)}"},
        )

        token = _token(signing_key, sub="uid-migrating")
        resp = client.post(
            "/auth/sync", json={"anonymous_user_id": str(anonymous_id)},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        assert resp.json()["profile_migrated"] is True

        profile = client.get(
            "/profile", headers={"Authorization": f"Bearer {token}"},
        ).json()
        assert profile["hard_constraints"]["gender"] == "men"
        assert profile["hard_constraints"]["sizes"] == ["L"]
        assert profile["hard_constraints"]["max_price_eur"] == 80.0

    def test_sync_is_idempotent(self, client, firebase_project, signing_key):
        headers = {"Authorization": f"Bearer {_token(signing_key, sub='uid-twice')}"}
        assert client.post("/auth/sync", json={}, headers=headers).status_code == 200
        assert client.post("/auth/sync", json={}, headers=headers).status_code == 200

    def test_delete_refuses_when_the_provider_cannot_be_reached(
        self, client, firebase_project, signing_key, monkeypatch,
    ):
        """A deletion we could not perform must not report success.

        Removing our rows while the identity survives at Firebase would let the
        same person sign in and be re-provisioned immediately — under a button
        that promises permanent erasure.
        """
        token = _token(signing_key, sub="uid-keep")
        headers = {"Authorization": f"Bearer {token}"}
        client.post("/auth/sync", json={}, headers=headers)

        monkeypatch.setattr("api.routers.auth._delete_firebase_user", lambda _uid: False)
        assert client.delete("/auth/account", headers=headers).status_code == 502
        assert store.get_user(firebase_auth.local_user_id("uid-keep")) is not None

    def test_delete_removes_the_account_when_the_provider_succeeds(
        self, client, firebase_project, signing_key, monkeypatch,
    ):
        token = _token(signing_key, sub="uid-gone")
        headers = {"Authorization": f"Bearer {token}"}
        client.post("/auth/sync", json={}, headers=headers)

        seen: list[str] = []

        def _fake_delete(uid):
            seen.append(uid)
            return True

        monkeypatch.setattr("api.routers.auth._delete_firebase_user", _fake_delete)
        assert client.delete("/auth/account", headers=headers).status_code == 200
        # The raw uid must reach Firebase, not the derived UUID.
        assert seen == ["uid-gone"]
        assert store.get_user(firebase_auth.local_user_id("uid-gone")) is None
