"""Retrieval evaluation -- Recall@K on the golden scenario.

Computes Recall@K for K = 10, 20, 50, 100 and writes a JSON report.
Recall@100 < 0.8 causes a CI failure with an explicit message.

Usage:
    python evaluation/eval_retrieval.py          # standalone
    from evaluation.eval_retrieval import ...    # from run_golden.py
"""
from __future__ import annotations

import json
import logging
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from evaluation.reporting import write_report as write_versioned_report

_LOG = logging.getLogger("swipewear.evaluation.eval_retrieval")

REPORTS_DIR = Path(__file__).parent / "reports"

K_VALUES = [10, 20, 50, 100]
RECALL_100_THRESHOLD = 0.8


@dataclass
class RetrievalEvalReport:
    recall_at: dict[int, float] = field(default_factory=dict)
    expected_count: int = 0
    retrieved_count: int = 0
    evaluated_at: str = ""
    passed: bool = True
    failure_reason: str = ""


def compute_recall_at_k(
    retrieved_ids: list[str],
    expected_ids: list[str],
    k: int,
) -> float:
    if not expected_ids:
        return 1.0
    top_k = set(retrieved_ids[:k])
    relevant = set(expected_ids)
    return len(top_k & relevant) / len(relevant)


def evaluate_retrieval(
    retrieved_ids: list[str],
    expected_ids: list[str],
    write_report: bool = True,
) -> RetrievalEvalReport:
    now = datetime.now(timezone.utc).isoformat()
    recall_at: dict[int, float] = {}
    for k in K_VALUES:
        recall_at[k] = round(compute_recall_at_k(retrieved_ids, expected_ids, k), 4)

    passed = True
    failure_reason = ""
    if recall_at.get(100, 0.0) < RECALL_100_THRESHOLD:
        passed = False
        failure_reason = (
            f"Recall@100 = {recall_at[100]:.4f} < {RECALL_100_THRESHOLD} threshold"
        )
        _LOG.error("RETRIEVAL EVAL FAILED: %s", failure_reason)

    report = RetrievalEvalReport(
        recall_at=recall_at,
        expected_count=len(expected_ids),
        retrieved_count=len(retrieved_ids),
        evaluated_at=now,
        passed=passed,
        failure_reason=failure_reason,
    )

    if write_report:
        report_path = write_versioned_report("retrieval", report, reports_dir=REPORTS_DIR)
        _LOG.info("Retrieval eval report written to %s", report_path)

    return report


if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).parent.parent))

    from evaluation.interfaces import FIXTURES_DIR

    expected_data = json.loads(
        (FIXTURES_DIR / "golden_expected.json").read_text(encoding="utf-8"),
    )
    expected_ids = [e["product_id"] for e in expected_data["top10"]]

    print(
        "Recall@K evaluation requires retrieved IDs from a live retriever.\n"
        "Use evaluate_retrieval(retrieved_ids, expected_ids) programmatically,\n"
        "or integrate via run_golden.py.",
    )
    sys.exit(0)
