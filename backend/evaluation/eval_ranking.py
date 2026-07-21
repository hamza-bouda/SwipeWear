"""Ranking evaluation — NDCG@10 ranker vs baseline similarity.

Proves the ranker adds value over a naive similarity sort (blueprint SS15).
CI fails if the ranker scores below the baseline.
"""
from __future__ import annotations

import json
import logging
import math
import sys
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

from evaluation.reporting import write_report as write_versioned_report

_LOG = logging.getLogger("swipewear.evaluation.eval_ranking")

REPORTS_DIR = Path(__file__).parent / "reports"


@dataclass
class RankingEvalReport:
    ndcg_baseline: float = 0.0
    ndcg_ranker: float = 0.0
    delta: float = 0.0
    passed: bool = True
    failure_reason: str = ""
    evaluated_at: str = ""
    k: int = 10


def _dcg(relevances: list[float], k: int) -> float:
    total = 0.0
    for i, rel in enumerate(relevances[:k]):
        total += rel / math.log2(i + 2)
    return total


def compute_ndcg(
    ranked_ids: list[str],
    relevance_map: dict[str, float],
    k: int = 10,
) -> float:
    if not relevance_map:
        return 1.0
    actual_rels = [relevance_map.get(pid, 0.0) for pid in ranked_ids[:k]]
    ideal_rels = sorted(relevance_map.values(), reverse=True)[:k]
    idcg = _dcg(ideal_rels, k)
    if idcg < 1e-9:
        return 1.0
    return _dcg(actual_rels, k) / idcg


def evaluate_ranking(
    baseline_ids: list[str],
    ranker_ids: list[str],
    relevance_map: dict[str, float],
    k: int = 10,
    write_report: bool = True,
) -> RankingEvalReport:
    now = datetime.now(timezone.utc).isoformat()

    ndcg_baseline = round(compute_ndcg(baseline_ids, relevance_map, k), 6)
    ndcg_ranker = round(compute_ndcg(ranker_ids, relevance_map, k), 6)
    delta = round(ndcg_ranker - ndcg_baseline, 6)

    passed = True
    failure_reason = ""
    if ndcg_ranker < ndcg_baseline:
        passed = False
        failure_reason = (
            f"Ranker NDCG@{k} = {ndcg_ranker:.4f} < baseline {ndcg_baseline:.4f} "
            f"(delta = {delta:+.4f})"
        )
        _LOG.error("RANKING EVAL FAILED: %s", failure_reason)

    report = RankingEvalReport(
        ndcg_baseline=ndcg_baseline,
        ndcg_ranker=ndcg_ranker,
        delta=delta,
        passed=passed,
        failure_reason=failure_reason,
        evaluated_at=now,
        k=k,
    )

    if write_report:
        report_path = write_versioned_report("ranking", report, reports_dir=REPORTS_DIR)
        _LOG.info("Ranking eval report written to %s", report_path)

    return report


if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).parent.parent))
    print(
        "Ranking evaluation requires both baseline and ranker orderings.\n"
        "Use evaluate_ranking(baseline_ids, ranker_ids, relevance_map)\n"
        "programmatically, or integrate via run_golden.py.",
    )
    sys.exit(0)
