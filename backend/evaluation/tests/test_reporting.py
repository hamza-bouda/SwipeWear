from __future__ import annotations

import json

from evaluation.compare_reports import compare_reports
from evaluation.interfaces import run_golden_scenario
from evaluation.reporting import write_report


def test_versioned_report_contains_reproducibility_metadata(tmp_path) -> None:
    path = write_report("golden", {"passed": True, "score": 0.9}, reports_dir=tmp_path)
    payload = json.loads(path.read_text(encoding="utf-8"))

    assert path.name.count("_") >= 2
    assert payload["report_type"] == "golden"
    assert payload["embedding_version"] == "fashionsiglip-v1"
    assert payload["config"]["mmr_lambda"] == 0.7
    assert len((tmp_path / "INDEX.csv").read_text(encoding="utf-8").splitlines()) == 2


def test_compare_reports_returns_metric_deltas() -> None:
    assert compare_reports({"score": 0.5}, {"score": 0.8}) == {"score": 0.3}


def test_golden_report_can_be_versioned(tmp_path, monkeypatch) -> None:
    import evaluation.reporting as reporting

    monkeypatch.setattr(reporting, "REPORTS_DIR", tmp_path)
    run_golden_scenario(write_report_file=True)
    assert list(tmp_path.glob("*_golden_*.json"))
