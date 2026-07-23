"""Backend-side survival test: watcher off, all app tests still pass (KAN-72).

This test is intentionally simple — it verifies that:
1. The backend does not import anything from watcher/
2. The ProductSource enum accepts 'vinted' (needed for DB reads when enabled)
3. The kill-switch filter clause is generated correctly
"""
from __future__ import annotations

from pathlib import Path


BACKEND_DIR = Path(__file__).resolve().parent.parent


class TestBackendSurvivesWithoutWatcher:
    def test_no_backend_import_of_watcher(self):
        """Confirm no backend source file imports from the watcher package."""
        violations = []
        # Exclude tests/ — they may reference watcher architecture intentionally.
        for py_file in BACKEND_DIR.rglob("*.py"):
            if "tests" in py_file.parts:
                continue
            text = py_file.read_text(encoding="utf-8", errors="ignore")
            lines = [
                ln for ln in text.splitlines()
                if "from watcher" in ln or "import watcher" in ln
            ]
            if lines:
                violations.append(str(py_file.relative_to(BACKEND_DIR)))
        assert violations == [], f"backend source imports watcher in: {violations}"

    def test_product_source_includes_vinted(self):
        from contracts.product import ProductSource
        assert ProductSource("vinted") == ProductSource.vinted

    def test_kill_switch_filter_clause(self):
        """apply_hard_filters with blocked_sources adds the exclusion clause."""
        from contracts.profile import HardConstraints, UserPreferenceProfile
        from retrieval.filters import apply_hard_filters
        from uuid import uuid4

        profile = UserPreferenceProfile(
            user_id=uuid4(),
            hard_constraints=HardConstraints(),
        )
        result = apply_hard_filters(profile, blocked_sources=["vinted"])
        assert "filter_blocked_sources" in result.params
        assert result.params["filter_blocked_sources"] == ["vinted"]
        assert "watcher_kill_switch" in result.applied
        assert "source != ALL" in " ".join(result.clauses)

    def test_kill_switch_empty_list_no_clause(self):
        from contracts.profile import HardConstraints, UserPreferenceProfile
        from retrieval.filters import apply_hard_filters
        from uuid import uuid4

        profile = UserPreferenceProfile(
            user_id=uuid4(),
            hard_constraints=HardConstraints(),
        )
        result = apply_hard_filters(profile, blocked_sources=[])
        assert "filter_blocked_sources" not in result.params
        assert "watcher_kill_switch" not in result.applied
