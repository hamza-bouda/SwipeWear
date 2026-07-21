from __future__ import annotations

from contracts.pipeline import ModuleTrace
from contracts.profile import UserPreferenceProfile
from contracts.trace import RequestTrace
from orchestration.latency_budgets import (
    MODULE_BUDGETS_MS,
    annotate_budgets,
    severe_budget_breaches,
    within_budget,
)


def test_documented_module_budgets_are_stable() -> None:
    assert MODULE_BUDGETS_MS == {
        "hard_filter": 20.0, "retrieve": 100.0, "rank": 50.0,
        "diversify": 30.0, "explain": 30.0,
    }


def test_budget_excess_adds_trace_warning_and_severe_error_marker() -> None:
    trace = RequestTrace(
        user_id=UserPreferenceProfile().user_id,
        modules=[ModuleTrace(module="rank", latency_ms=110)],
    )
    annotated = annotate_budgets(trace)

    assert "latency budget exceeded" in annotated.modules[0].warnings[0]
    assert severe_budget_breaches(annotated) == ["rank"]


def test_ci_tolerance_can_be_configured() -> None:
    assert within_budget(55, "rank", tolerance=1.2)
