"""Compare two versioned evaluation reports.

Usage: python evaluation/compare_reports.py old.json new.json
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


def _numeric_values(data: dict[str, Any], prefix: str = "") -> dict[str, float]:
    values: dict[str, float] = {}
    for key, value in data.items():
        name = f"{prefix}.{key}" if prefix else key
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            values[name] = float(value)
        elif isinstance(value, dict) and key not in {"config"}:
            values.update(_numeric_values(value, name))
    return values


def compare_reports(old: dict[str, Any], new: dict[str, Any]) -> dict[str, float]:
    """Return ``new - old`` for every numeric metric shared by two reports."""
    old_values = _numeric_values(old)
    new_values = _numeric_values(new)
    return {
        name: round(new_values[name] - old_values[name], 10)
        for name in sorted(old_values.keys() & new_values.keys())
    }


def main(argv: list[str]) -> int:
    if len(argv) != 3:
        print("Usage: python evaluation/compare_reports.py old.json new.json")
        return 2
    old = json.loads(Path(argv[1]).read_text(encoding="utf-8"))
    new = json.loads(Path(argv[2]).read_text(encoding="utf-8"))
    for metric, delta in compare_reports(old, new).items():
        print(f"{metric}: {delta:+.6f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
