from __future__ import annotations

import json
from pathlib import Path

import pytest

from evaluation.bench_qwen import (
    GO_THRESHOLD_SECONDS,
    MODEL_ID,
    REQUIRED_IMAGE_COUNT,
    BenchmarkReport,
    run_benchmark,
    write_report,
)


class FakeRunner:
    model_id = MODEL_ID
    quantization = "int8"

    def __init__(self, *, fail_load: bool = False, fail_image: str | None = None):
        self.fail_load = fail_load
        self.fail_image = fail_image
        self.load_calls = 0
        self.analyzed: list[str] = []

    def load(self) -> None:
        self.load_calls += 1
        if self.fail_load:
            raise RuntimeError("model unavailable")

    def analyze(self, image_path: Path) -> str:
        self.analyzed.append(image_path.name)
        if image_path.name == self.fail_image:
            raise RuntimeError("inference failed")
        return f"fashion description for {image_path.name}"


def _images(tmp_path: Path) -> tuple[Path, ...]:
    paths = tuple(tmp_path / f"fashion-{index}.jpg" for index in range(5))
    for path in paths:
        path.write_bytes(b"fake-image")
    return paths


def _clock(load_seconds: float, image_seconds: float):
    values = [0.0, load_seconds]
    current = load_seconds
    for _ in range(REQUIRED_IMAGE_COUNT):
        values.extend((current, current + image_seconds))
        current += image_seconds
    iterator = iter(values)
    return lambda: next(iterator)


def _ram_reader():
    values = iter((100.0, 900.0, 910.0, 920.0, 930.0, 940.0, 950.0))
    return lambda: next(values)


def _environment() -> dict[str, str | int | float]:
    return {"python": "3.11.9", "total_ram_mb": 16384.0}


def _run(
    tmp_path: Path,
    runner: FakeRunner,
    *,
    image_seconds: float = 1.0,
) -> BenchmarkReport:
    return run_benchmark(
        runner,
        _images(tmp_path),
        clock=_clock(load_seconds=2.0, image_seconds=image_seconds),
        ram_reader=_ram_reader(),
        environment_reader=_environment,
    )


def test_fast_five_image_benchmark_is_go(tmp_path: Path) -> None:
    runner = FakeRunner()
    report = _run(tmp_path, runner, image_seconds=1.0)

    assert report.verdict == "GO"
    assert report.image_count == 5
    assert report.successful_image_count == 5
    assert report.load_latency_seconds == 2.0
    assert report.mean_inference_seconds == 1.0
    assert report.peak_ram_mb == 950.0
    assert report.ram_delta_mb == 850.0
    assert runner.load_calls == 1
    assert len(runner.analyzed) == 5


def test_mean_latency_at_threshold_is_defer(tmp_path: Path) -> None:
    report = _run(tmp_path, FakeRunner(), image_seconds=GO_THRESHOLD_SECONDS)

    assert report.verdict == "DEFER"
    assert "not below" in report.decision_reason


def test_one_failed_image_is_defer_but_remaining_images_run(tmp_path: Path) -> None:
    runner = FakeRunner(fail_image="fashion-2.jpg")
    report = _run(tmp_path, runner)

    assert report.verdict == "DEFER"
    assert report.successful_image_count == 4
    assert len(report.images) == 5
    assert runner.analyzed == [f"fashion-{index}.jpg" for index in range(5)]
    assert report.images[2].error == "RuntimeError: inference failed"


def test_load_failure_is_recorded_as_defer(tmp_path: Path) -> None:
    report = run_benchmark(
        FakeRunner(fail_load=True),
        _images(tmp_path),
        clock=_clock(load_seconds=2.0, image_seconds=1.0),
        ram_reader=lambda: 100.0,
        environment_reader=_environment,
    )

    assert report.verdict == "DEFER"
    assert report.successful_image_count == 0
    assert report.images == []
    assert report.error == "RuntimeError: model unavailable"


@pytest.mark.parametrize("count", [0, 4, 6])
def test_benchmark_requires_exactly_five_images(tmp_path: Path, count: int) -> None:
    paths = tuple(tmp_path / f"image-{index}.jpg" for index in range(count))
    for path in paths:
        path.write_bytes(b"fake-image")

    with pytest.raises(ValueError, match="exactly 5 images"):
        run_benchmark(FakeRunner(), paths)


def test_missing_image_is_rejected_before_model_load(tmp_path: Path) -> None:
    runner = FakeRunner()
    paths = tuple(tmp_path / f"missing-{index}.jpg" for index in range(5))

    with pytest.raises(FileNotFoundError, match="benchmark images not found"):
        run_benchmark(runner, paths)

    assert runner.load_calls == 0


def test_report_json_preserves_metrics_and_outputs(tmp_path: Path) -> None:
    report = _run(tmp_path, FakeRunner())
    output_path = tmp_path / "reports" / "qwen_bench.json"

    write_report(report, output_path)
    data = json.loads(output_path.read_text(encoding="utf-8"))

    assert data["schema_version"] == 1
    assert data["ticket"] == "KAN-30"
    assert data["model_id"] == MODEL_ID
    assert data["quantization"] == "int8"
    assert data["device"] == "cpu"
    assert data["verdict"] == "GO"
    assert len(data["images"]) == 5
    assert data["images"][0]["output"].startswith("fashion description")


def test_report_contains_reproducible_environment_metadata(tmp_path: Path) -> None:
    report = _run(tmp_path, FakeRunner())

    assert report.environment == {"python": "3.11.9", "total_ram_mb": 16384.0}
    assert report.go_threshold_seconds == 3.0
