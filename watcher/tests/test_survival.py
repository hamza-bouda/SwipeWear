"""Survival tests: verify the watcher is fully isolated from the backend (KAN-72).

These tests confirm the isolation contract:
- No file in backend/ imports from watcher/
- The watcher process can start and exit cleanly with VINTED_ENABLED=false
- The normalizer is self-contained (no contracts/ imports)
"""
from __future__ import annotations

import importlib
import subprocess
import sys
from pathlib import Path


BACKEND_DIR = Path(__file__).resolve().parent.parent.parent / "backend"
WATCHER_DIR = Path(__file__).resolve().parent.parent


class TestIsolation:
    def test_no_backend_file_imports_watcher(self):
        """No backend source file must contain 'from watcher' or 'import watcher'.

        Test files are excluded — they are allowed to reference the architecture
        in assertions without creating a real runtime dependency.
        """
        violations = []
        for py_file in BACKEND_DIR.rglob("*.py"):
            if "tests" in py_file.parts:
                continue
            text = py_file.read_text(encoding="utf-8", errors="ignore")
            lines = [l for l in text.splitlines() if "from watcher" in l or "import watcher" in l]
            if lines:
                violations.append(str(py_file.relative_to(BACKEND_DIR)))
        assert violations == [], (
            f"backend source imports watcher in: {violations}\n"
            "The watcher must remain fully isolated from the backend."
        )

    def test_normalizer_does_not_import_contracts(self):
        """normalizer.py must not import from backend contracts/."""
        normalizer_path = WATCHER_DIR / "normalizer.py"
        text = normalizer_path.read_text(encoding="utf-8")
        assert "from contracts" not in text, (
            "normalizer.py imports from contracts/ — watcher must be self-contained"
        )
        assert "import contracts" not in text

    def test_watcher_exits_cleanly_when_disabled(self):
        """Running vinted_watcher.py with VINTED_ENABLED=false must exit 0."""
        import os
        env = {**os.environ, "VINTED_ENABLED": "false"}
        # watcher/ is at SwipeWear root; add it to PYTHONPATH so 'watcher' resolves
        project_root = str(WATCHER_DIR.parent)
        env["PYTHONPATH"] = (
            project_root + os.pathsep + env.get("PYTHONPATH", "")
        ).rstrip(os.pathsep)
        result = subprocess.run(
            [sys.executable, str(WATCHER_DIR / "vinted_watcher.py")],
            env=env,
            capture_output=True,
            timeout=10,
        )
        assert result.returncode == 0, (
            f"Watcher exited {result.returncode}:\n"
            f"stdout: {result.stdout.decode()}\n"
            f"stderr: {result.stderr.decode()}"
        )
