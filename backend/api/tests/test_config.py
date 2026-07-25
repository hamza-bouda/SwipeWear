"""Tests for production secret loading — KAN-88.

The bug this guards against: auth.py read JWT_SECRET_KEY while .env defined
JWT_SECRET, so the configured value was never loaded and every token was
signed with a development literal that is public in this repository. The app
booted, served traffic, and looked healthy the whole time.
"""
from __future__ import annotations

import os
from unittest.mock import patch

import pytest

from api.config import ConfigurationError, app_env, is_production, require_secret

_DEV = "dev-default"


class TestAppEnv:
    def test_defaults_to_development(self):
        with patch.dict(os.environ, {}, clear=True):
            assert app_env() == "development"
            assert is_production() is False

    @pytest.mark.parametrize("value", ["production", "PRODUCTION", " prod "])
    def test_recognises_production_spellings(self, value):
        with patch.dict(os.environ, {"APP_ENV": value}):
            assert is_production() is True

    def test_staging_is_not_production(self):
        with patch.dict(os.environ, {"APP_ENV": "staging"}):
            assert is_production() is False


class TestRequireSecret:
    def test_returns_the_configured_value(self):
        with patch.dict(os.environ, {"JWT_SECRET": "s3cret"}):
            assert require_secret("JWT_SECRET", dev_default=_DEV) == "s3cret"

    def test_accepts_an_alias(self):
        """A renamed variable is the exact failure this function exists to
        prevent, so both spellings have to resolve."""
        with patch.dict(os.environ, {"JWT_SECRET_KEY": "legacy"}, clear=True):
            assert require_secret(
                "JWT_SECRET", "JWT_SECRET_KEY", dev_default=_DEV,
            ) == "legacy"

    def test_primary_name_wins_over_alias(self):
        env = {"JWT_SECRET": "primary", "JWT_SECRET_KEY": "legacy"}
        with patch.dict(os.environ, env):
            assert require_secret(
                "JWT_SECRET", "JWT_SECRET_KEY", dev_default=_DEV,
            ) == "primary"

    def test_blank_value_is_treated_as_unset(self):
        """Railway hands through an empty string for a variable declared but
        never given a value."""
        with patch.dict(os.environ, {"JWT_SECRET": "   "}, clear=True):
            assert require_secret("JWT_SECRET", dev_default=_DEV) == _DEV

    def test_falls_back_to_the_dev_default_outside_production(self):
        with patch.dict(os.environ, {}, clear=True):
            assert require_secret("JWT_SECRET", dev_default=_DEV) == _DEV

    def test_production_refuses_to_start_without_a_secret(self):
        with patch.dict(os.environ, {"APP_ENV": "production"}, clear=True):
            with pytest.raises(ConfigurationError, match="JWT_SECRET"):
                require_secret("JWT_SECRET", dev_default=_DEV)

    def test_production_error_names_the_variable_to_set(self):
        with patch.dict(os.environ, {"APP_ENV": "production"}, clear=True):
            with pytest.raises(ConfigurationError) as exc:
                require_secret("PASSWORD_SALT", dev_default=_DEV)
        assert "PASSWORD_SALT" in str(exc.value)

    def test_production_with_a_secret_starts_normally(self):
        env = {"APP_ENV": "production", "JWT_SECRET": "a-real-secret"}
        with patch.dict(os.environ, env, clear=True):
            assert require_secret("JWT_SECRET", dev_default=_DEV) == "a-real-secret"

    def test_warns_when_using_the_dev_default(self, caplog):
        with patch.dict(os.environ, {}, clear=True):
            require_secret("JWT_SECRET", dev_default=_DEV)
        assert "development default" in caplog.text


class TestAuthUsesTheConfiguredName:
    def test_jwt_secret_from_env_is_what_signs_tokens(self):
        """Regression: .env's JWT_SECRET has to be the key actually used."""
        with patch.dict(os.environ, {"JWT_SECRET": "from-dot-env"}, clear=True):
            assert require_secret(
                "JWT_SECRET", "JWT_SECRET_KEY",
                dev_default="swipewear-dev-secret-change-in-prod",
            ) == "from-dot-env"
