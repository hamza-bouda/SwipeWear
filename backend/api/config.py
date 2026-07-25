"""Runtime environment and secret loading.

Secrets used to be read with `os.getenv(NAME, "<dev default>")` scattered across
modules. That is silent by construction: a name that does not match the one in
.env falls back to the development default and the app boots looking healthy —
which is exactly what happened to the JWT signing key, whose literal is public
in this repository.

Production therefore refuses to start on a development default rather than
serving traffic it cannot secure.
"""
from __future__ import annotations

import logging
import os

_LOG = logging.getLogger("swipewear.api.config")

_PRODUCTION_NAMES = {"production", "prod"}


def app_env() -> str:
    """Deployment environment: 'development' (default), 'staging', 'production'."""
    return os.getenv("APP_ENV", "development").strip().lower()


def is_production() -> bool:
    return app_env() in _PRODUCTION_NAMES


def mock_data_allowed() -> bool:
    """Whether the API may substitute fabricated data for a failed pipeline.

    Local development only — staging counts as production here. Serving
    invented products to a real user is worse than an error: the response is
    a 200, so monitoring records a success and nobody finds out.
    """
    return app_env() == "development"


class ConfigurationError(RuntimeError):
    """Raised when production configuration is missing or unsafe."""


def require_secret(
    name: str,
    *aliases: str,
    dev_default: str,
) -> str:
    """Return a secret from the environment, or fail loudly in production.

    Aliases exist because a renamed variable is the failure mode this function
    is here to prevent: accepting both names is what stops a deployment from
    quietly signing tokens with a public string.
    """
    for candidate in (name, *aliases):
        value = os.getenv(candidate)
        if value and value.strip():
            return value

    if is_production():
        raise ConfigurationError(
            f"{name} is not set. Refusing to start in {app_env()!r} with the "
            f"development default, which is public in the repository. "
            f"Set {name} to a random secret before deploying."
        )

    _LOG.warning(
        "%s is not set — using the development default. This is unsafe outside "
        "local development.", name,
    )
    return dev_default
