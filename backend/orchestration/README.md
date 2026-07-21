# Orchestration latency budgets

The CPU-only feed target is **300 ms** total, excluding network time.  Module
budgets are: hard filter 20 ms, retrieval 100 ms, ranking 50 ms, diversity 30
ms, and explanation 30 ms.  A run over budget adds a warning to its request
trace; a run above twice the budget is logged as an error.  CI can use a
configured tolerance through `within_budget(..., tolerance=...)`.
