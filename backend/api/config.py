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
from pathlib import Path

_LOG = logging.getLogger("swipewear.api.config")

_PRODUCTION_NAMES = {"production", "prod"}
_ENV_PATH = Path(__file__).resolve().parent.parent.parent / ".env"


def load_dotenv() -> None:
    """Make the project's .env visible when nothing else supplies the env.

    Railway injects variables directly, so this is for local runs — where
    otherwise nothing read .env at all and every secret silently resolved to
    its development default no matter what the file said.

    setdefault, never overwrite: a real deployment's variables must always win
    over a stray .env that happened to be copied into the image.
    """
    if not _ENV_PATH.exists():
        return
    for line in _ENV_PATH.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), value.strip())


# On import, not on a call: api.auth resolves its signing key at module level,
# so any later hook would run after the secret had already been read.
load_dotenv()


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
