"""Tests for auth: anonymous sessions, Supabase token verification, deletion.

Accounts moved to Supabase in KAN-90, so there is nothing here about
registering or signing in — the backend never sees a password. What it must
still get exactly right is deciding whether a bearer token is genuine, and for
whom. Those checks run against tokens signed with a keypair generated in the
test, which exercises the real verification path without needing a live
Supabase project.
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import time
from uuid import UUID, uuid4

import jwt
import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi.testclient import TestClient

from api import store, supabase_auth
from api.app import app
from api.auth import create_anonymous_token

_PROJECT_URL = "https://testproject.supabase.co"
_ISSUER = f"{_PROJECT_URL}/auth/v1"


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
def supabase_project(monkeypatch, signing_key):
    """Point the verifier at a project whose signing key we control."""
    monkeypatch.setenv("SUPABASE_URL", _PROJECT_URL)
    monkeypatch.delenv("SUPABASE_JWT_SECRET", raising=False)

    class _Key:
        key = signing_key.public_key()

    class _Client:
        def get_signing_key_from_jwt(self, token):
            return _Key()

    monkeypatch.setattr(supabase_auth, "_jwks_client", _Client())
    yield
    supabase_auth.reset_cache()


def _b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def _token(key, *, sub=None, email="user@example.com", provider="google",
           issuer=_ISSUER, audience="authenticated", expires_in=3600,
           algorithm="RS256"):
    now = int(time.time())
    return jwt.encode(
        {
            "sub": str(sub or uuid4()),
            "email": email,
            "app_metadata": {"provider": provider},
            "iss": issuer,
            "aud": audience,
            "iat": now,
            "exp": now + expires_in,
        },
        key,
        algorithm=algorithm,
    )


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


class TestSupabaseTokenVerification:
    def test_valid_token_is_accepted(self, supabase_project, signing_key):
        user_id = uuid4()
        claims = supabase_auth.verify(_token(signing_key, sub=user_id))
        assert claims.user_id == user_id
        assert claims.email == "user@example.com"
        assert claims.provider == "google"

    def test_expired_token_is_rejected(self, supabase_project, signing_key):
        with pytest.raises(Exception) as exc:
            supabase_auth.verify(_token(signing_key, expires_in=-60))
        assert exc.value.status_code == 401
        assert exc.value.detail["error_code"] == "TOKEN_EXPIRED"

    def test_token_signed_by_another_key_is_rejected(self, supabase_project):
        attacker_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        with pytest.raises(Exception) as exc:
            supabase_auth.verify(_token(attacker_key))
        assert exc.value.status_code == 401

    def test_wrong_audience_is_rejected(self, supabase_project, signing_key):
        """`anon` and service-role keys are also signed by the project.

        Without an audience check they would authenticate a person, and the
        anon key ships inside the mobile app.
        """
        with pytest.raises(Exception) as exc:
            supabase_auth.verify(_token(signing_key, audience="anon"))
        assert exc.value.status_code == 401

    def test_wrong_issuer_is_rejected(self, supabase_project, signing_key):
        with pytest.raises(Exception) as exc:
            supabase_auth.verify(
                _token(signing_key, issuer="https://evil.supabase.co/auth/v1"),
            )
        assert exc.value.status_code == 401

    def test_hs256_is_refused_when_no_shared_secret_is_configured(
        self, supabase_project, signing_key,
    ):
        """Guards against algorithm confusion.

        The classic attack re-signs a token as HS256 using the project's
        *public* key as the HMAC secret. The public key is, by definition,
        public. Accepting HS256 without a configured shared secret would make
        that forgery valid.
        """
        public_pem = signing_key.public_key().public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )
        # Assembled by hand: PyJWT refuses to *encode* HS256 with a PEM key,
        # which is a guard on the writing side only. A real attacker builds the
        # bytes directly, so the test has to as well — otherwise it would prove
        # nothing about our verification.
        header = _b64url(json.dumps({"alg": "HS256", "typ": "JWT"}).encode())
        payload = _b64url(json.dumps({
            "sub": str(uuid4()), "iss": _ISSUER, "aud": "authenticated",
            "exp": int(time.time()) + 3600,
        }).encode())
        signature = _b64url(
            hmac.new(public_pem, f"{header}.{payload}".encode(), hashlib.sha256).digest()
        )
        forged = f"{header}.{payload}.{signature}"

        with pytest.raises(Exception) as exc:
            supabase_auth.verify(forged)
        assert exc.value.status_code == 401

    def test_foreign_issuer_is_not_routed_to_supabase(self, supabase_project, signing_key):
        token = _token(signing_key, issuer="https://other.example.com")
        assert supabase_auth.looks_like_supabase_token(token) is False

    def test_nothing_is_a_supabase_token_when_unconfigured(self, monkeypatch, signing_key):
        monkeypatch.delenv("SUPABASE_URL", raising=False)
        assert supabase_auth.looks_like_supabase_token(_token(signing_key)) is False


class TestAccountScopedEndpoints:
    def test_anonymous_token_cannot_delete_an_account(self, client):
        headers = {"Authorization": f"Bearer {create_anonymous_token(uuid4())}"}
        resp = client.delete("/auth/account", headers=headers)
        assert resp.status_code == 401
        assert resp.json()["detail"]["error_code"] == "ACCOUNT_REQUIRED"

    def test_sync_refuses_an_anonymous_token(self, client, supabase_project):
        headers = {"Authorization": f"Bearer {create_anonymous_token(uuid4())}"}
        resp = client.post("/auth/sync", json={}, headers=headers)
        assert resp.status_code == 401

    def test_sync_reports_unavailable_when_provider_unconfigured(
        self, client, monkeypatch,
    ):
        monkeypatch.delenv("SUPABASE_URL", raising=False)
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
    def test_first_sync_creates_the_account(
        self, client, supabase_project, signing_key,
    ):
        user_id = uuid4()
        token = _token(signing_key, sub=user_id, email="New@Example.com")
        resp = client.post(
            "/auth/sync", json={},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["user_id"] == str(user_id)
        # Stored lowercased, so the same address cannot become two accounts.
        assert body["email"] == "new@example.com"
        assert store.get_user(user_id) is not None

    def test_sync_carries_over_the_anonymous_profile(
        self, client, supabase_project, signing_key,
    ):
        anonymous_id = uuid4()
        client.post(
            "/onboarding/styles",
            json={
                "style_ids": ["minimal"], "liked_brands": ["Carhartt"],
                "sizes": ["L"], "max_price_eur": 80.0, "gender": "men",
            },
            headers={
                "Authorization": f"Bearer {create_anonymous_token(anonymous_id)}",
            },
        )

        user_id = uuid4()
        token = _token(signing_key, sub=user_id)
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

    def test_sync_is_idempotent(self, client, supabase_project, signing_key):
        user_id = uuid4()
        token = _token(signing_key, sub=user_id)
        headers = {"Authorization": f"Bearer {token}"}
        assert client.post("/auth/sync", json={}, headers=headers).status_code == 200
        assert client.post("/auth/sync", json={}, headers=headers).status_code == 200

    def test_delete_refuses_when_the_provider_cannot_be_reached(
        self, client, supabase_project, signing_key, monkeypatch,
    ):
        """A deletion we could not perform must not report success.

        Removing our rows while the identity survives at the provider would let
        the same person sign in and be re-provisioned immediately — under a
        button that promises permanent erasure.
        """
        user_id = uuid4()
        token = _token(signing_key, sub=user_id)
        headers = {"Authorization": f"Bearer {token}"}
        client.post("/auth/sync", json={}, headers=headers)

        monkeypatch.setattr(
            "api.routers.auth._delete_supabase_user", lambda _user_id: False,
        )
        resp = client.delete("/auth/account", headers=headers)
        assert resp.status_code == 502
        assert store.get_user(user_id) is not None

    def test_delete_removes_the_account_when_the_provider_succeeds(
        self, client, supabase_project, signing_key, monkeypatch,
    ):
        user_id = uuid4()
        token = _token(signing_key, sub=user_id)
        headers = {"Authorization": f"Bearer {token}"}
        client.post("/auth/sync", json={}, headers=headers)

        monkeypatch.setattr(
            "api.routers.auth._delete_supabase_user", lambda _user_id: True,
        )
        assert client.delete("/auth/account", headers=headers).status_code == 200
        assert store.get_user(user_id) is None
