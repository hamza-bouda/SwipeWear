"""Versioned JSON/CSV evaluation report persistence."""
from __future__ import annotations

import csv
import json
import subprocess
from dataclasses import asdict, is_dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from ranking.interfaces import (
    DEFAULT_WEIGHTS,
    FRESHNESS_HALF_LIFE_DAYS,
    PRICE_FIT_THRESHOLD,
)

REPORTS_DIR = Path(__file__).parent / "reports"
INDEX_NAME = "INDEX.csv"


def git_sha() -> str:
    """Return the checked-out short SHA, including when run from a worktree."""
    try:
        root = Path(__file__).resolve().parents[2]
        return subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"], cwd=root,
            check=True, capture_output=True, text=True,
        ).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return "unknown"


def active_config() -> dict[str, Any]:
    return {
        "ranker_weights": asdict(DEFAULT_WEIGHTS),
        "mmr_lambda": 0.7,
        "epsilon": 0.1,
        "thresholds": {
            "price_fit": PRICE_FIT_THRESHOLD,
            "freshness_half_life_days": FRESHNESS_HALF_LIFE_DAYS,
            "recall_at_100": 0.8,
        },
    }


def _metrics(payload: dict[str, Any]) -> dict[str, float | int | bool]:
    metrics: dict[str, float | int | bool] = {}
    for key, value in payload.items():
        if isinstance(value, (float, int, bool)):
            metrics[key] = value
        elif isinstance(value, dict):
            for nested_key, nested_value in value.items():
                if isinstance(nested_value, (float, int, bool)):
                    metrics[f"{key}_{nested_key}"] = nested_value
    return metrics


def write_report(
    report_type: str,
    report: Any,
    *,
    reports_dir: Path | None = None,
    embedding_version: str = "fashionsiglip-v1",
) -> Path:
    """Persist a small, fully reproducible evaluation report and update its index."""
    if report_type not in {"retrieval", "ranking", "golden"}:
        raise ValueError(f"Unsupported report type: {report_type}")
    report_payload = asdict(report) if is_dataclass(report) else dict(report)
    reports_dir = reports_dir or REPORTS_DIR
    now = datetime.now(timezone.utc)
    sha = git_sha()
    payload = {
        **report_payload,
        "report_type": report_type,
        "created_at": now.isoformat(),
        "git_sha": sha,
        "embedding_version": embedding_version,
        "config": active_config(),
    }
    reports_dir.mkdir(parents=True, exist_ok=True)
    filename = f"{now:%Y%m%d}_{report_type}_{sha}.json"
    path = reports_dir / filename
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    index_path = reports_dir / INDEX_NAME
    row = {
        "date": now.date().isoformat(),
        "type": report_type,
        "git_sha": sha,
        "report": filename,
        "metrics": json.dumps(_metrics(report_payload), sort_keys=True),
    }
    write_header = not index_path.exists()
    with index_path.open("a", newline="", encoding="utf-8") as index_file:
        writer = csv.DictWriter(index_file, fieldnames=list(row))
        if write_header:
            writer.writeheader()
        writer.writerow(row)
    return path
