import os
import sys
from pathlib import Path

import pytest

# Add backend/ to sys.path so that 'from contracts.interfaces import ...' works
# regardless of how pytest is invoked.
sys.path.insert(0, str(Path(__file__).parent))

_ENV_PATH = Path(__file__).parent.parent / ".env"


def _load_dotenv() -> None:
    """Make the project's .env visible to tests.

    Without this, DATABASE_URL is unset during a test run and api.db falls back
    to a localhost DSN pinned to port 5432 — while the project's compose file
    publishes 5433. Five integration tests failed permanently for that reason
    alone, against a database that was running the whole time.
    """
    if not _ENV_PATH.exists():
        return
    for line in _ENV_PATH.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), value.strip())


_load_dotenv()


def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line(
        "markers",
        "requires_db: test needs a reachable PostgreSQL instance",
    )


def _database_reachable() -> bool:
    """One connection attempt per session, cached by the caller."""
    try:
        import psycopg2

        from api.db import _get_database_url

        conn = psycopg2.connect(_get_database_url(), connect_timeout=3)
        conn.close()
        return True
    except Exception:
        return False


@pytest.fixture(scope="session")
def database_available() -> bool:
    return _database_reachable()


@pytest.fixture(autouse=True)
def _skip_when_no_database(request: pytest.FixtureRequest) -> None:
    """Skip DB-backed tests instead of failing them where no database exists.

    CI runs no Postgres service, so these tests could never pass there. A skip
    says that honestly; a failure that everyone learns to ignore is worse than
    no test at all, because it hides the next real regression.
    """
    if request.node.get_closest_marker("requires_db") is None:
        return
    if not request.getfixturevalue("database_available"):
        pytest.skip("no reachable PostgreSQL instance (set DATABASE_URL)")
