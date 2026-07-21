"""Latency budgets for the CPU-only recommendation pipeline."""
from __future__ import annotations

from contracts.pipeline import ModuleTrace
from contracts.trace import RequestTrace


MODULE_BUDGETS_MS: dict[str, float] = {
    "hard_filter": 20.0,
    "retrieve": 100.0,
    "rank": 50.0,
    "diversify": 30.0,
    "explain": 30.0,
}
TOTAL_FEED_BUDGET_MS = 300.0


def within_budget(latency_ms: float, module: str, *, tolerance: float = 1.0) -> bool:
    """Whether a module timing respects its configured CI tolerance."""
    return latency_ms <= MODULE_BUDGETS_MS[module] * tolerance


def _with_budget_warning(module: ModuleTrace) -> ModuleTrace:
    budget = MODULE_BUDGETS_MS.get(module.module)
    if budget is None or module.latency_ms <= budget:
        return module
    warning = f"latency budget exceeded: {module.latency_ms:.2f}ms > {budget:.2f}ms"
    return module.model_copy(update={"warnings": [*module.warnings, warning]})


def annotate_budgets(trace: RequestTrace) -> RequestTrace:
    """Attach non-fatal latency-budget warnings to a request trace."""
    modules = [_with_budget_warning(module) for module in trace.modules]
    if trace.total_latency_ms > TOTAL_FEED_BUDGET_MS:
        modules.append(ModuleTrace(
            module="feed_total",
            latency_ms=trace.total_latency_ms,
            warnings=[
                "latency budget exceeded: "
                f"{trace.total_latency_ms:.2f}ms > {TOTAL_FEED_BUDGET_MS:.2f}ms"
            ],
        ))
    return trace.model_copy(update={"modules": modules})


def severe_budget_breaches(trace: RequestTrace) -> list[str]:
    """Describe timings over twice their budget, which merit error-level logging."""
    breaches = [
        module.module
        for module in trace.modules
        if module.module in MODULE_BUDGETS_MS
        and module.latency_ms > 2 * MODULE_BUDGETS_MS[module.module]
    ]
    if trace.total_latency_ms > 2 * TOTAL_FEED_BUDGET_MS:
        breaches.append("feed_total")
    return breaches

