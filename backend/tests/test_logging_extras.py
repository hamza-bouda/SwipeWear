"""Guard against reserved LogRecord attributes in logging `extra` — KAN-87.

logging raises KeyError when `extra` carries a name LogRecord already defines.
orchestrator.py did exactly that with "module" on its latency-breach warning,
so a slow request died with a KeyError instead of being flagged — the failure
only showed up once the catalogue was large enough to breach a budget.
"""
from __future__ import annotations

import ast
import logging
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent

# Attributes logging.LogRecord sets itself and refuses to have overwritten.
_RESERVED = set(
    logging.LogRecord("n", logging.INFO, "p", 1, "m", None, None).__dict__
) | {"message", "asctime"}


def _source_files() -> list[Path]:
    return [
        p for p in BACKEND_DIR.rglob("*.py")
        if not any(part.startswith((".", "__pycache__")) for part in p.parts)
    ]


def test_no_logging_extra_uses_a_reserved_attribute():
    offenders: list[str] = []
    for path in _source_files():
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"))
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            for kw in node.keywords:
                if kw.arg != "extra" or not isinstance(kw.value, ast.Dict):
                    continue
                for key in kw.value.keys:
                    if (
                        isinstance(key, ast.Constant)
                        and key.value in _RESERVED
                    ):
                        rel = path.relative_to(BACKEND_DIR)
                        offenders.append(f"{rel}:{key.lineno} -> {key.value!r}")
    assert offenders == [], (
        "logging extra= uses names LogRecord reserves, which raises KeyError "
        f"at call time: {offenders}. Prefix them (the codebase uses "
        "'pipe_module')."
    )
