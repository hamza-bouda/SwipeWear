from __future__ import annotations
from dataclasses import dataclass, field
from pathlib import Path

FIXTURES_DIR = Path(__file__).parent / "fixtures"

@dataclass
class EvaluationReport:
    passed: bool
    metrics: dict[str, float] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)
    fixture_hash: str = ""

def run_golden_scenario() -> EvaluationReport:
    # Execute full pipeline on fixed golden fixtures. Called by CI after every push.
    # NEVER modify fixtures to make this pass — fix the code instead.
    raise NotImplementedError
