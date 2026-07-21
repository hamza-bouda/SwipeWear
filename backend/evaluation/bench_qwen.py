#!/usr/bin/env python3
"""Benchmark quantized Qwen3-VL-2B-Instruct on five local fashion images.

The benchmark is intentionally separate from the runtime vision adapter. It records
model-load latency, per-image inference latency, process RAM, and the KAN-30 GO/DEFER
decision in a deterministic JSON schema.
"""
from __future__ import annotations

import argparse
import json
import os
import platform
import statistics
import sys
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Literal, Protocol, Sequence

MODEL_ID = "Qwen/Qwen3-VL-2B-Instruct"
GO_THRESHOLD_SECONDS = 3.0
REQUIRED_IMAGE_COUNT = 5
REPORT_SCHEMA_VERSION = 1

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_IMAGES = (
    REPOSITORY_ROOT / "tests_ia" / "images" / "woman.jpg",
    REPOSITORY_ROOT / "tests_ia" / "images" / "man.jpg",
    REPOSITORY_ROOT / "tests_ia" / "images" / "shop.jpg",
    REPOSITORY_ROOT / "tests_ia" / "images" / "rack.jpg",
    REPOSITORY_ROOT / "tests_ia" / "images" / "jacket.jpg",
)
DEFAULT_REPORT_PATH = Path(__file__).parent / "reports" / "qwen_bench.json"

PROMPT = (
    "Describe the visible garments and overall fashion style in one concise sentence. "
    "Mention garment categories, dominant colors, and style only when visible."
)


class BenchmarkRunner(Protocol):
    """Minimal adapter used by the benchmark and deterministic unit tests."""

    @property
    def model_id(self) -> str:
        """Return the benchmarked model identifier."""
        ...

    @property
    def quantization(self) -> str:
        """Return the selected quantization mode."""
        ...

    def load(self) -> None:
        """Load and quantize the model."""
        ...

    def analyze(self, image_path: Path) -> str:
        """Analyze one image and return generated text."""
        ...


@dataclass(frozen=True)
class ImageBenchmarkResult:
    image: str
    latency_seconds: float
    ram_mb: float
    succeeded: bool
    output: str | None = None
    error: str | None = None


@dataclass(frozen=True)
class BenchmarkReport:
    schema_version: int
    ticket: str
    generated_at: str
    model_id: str
    quantization: str
    device: str
    image_count: int
    successful_image_count: int
    load_latency_seconds: float
    mean_inference_seconds: float | None
    median_inference_seconds: float | None
    peak_ram_mb: float
    ram_delta_mb: float
    go_threshold_seconds: float
    verdict: Literal["GO", "DEFER"]
    decision_reason: str
    images: list[ImageBenchmarkResult] = field(default_factory=list)
    environment: dict[str, str | int | float] = field(default_factory=dict)
    error: str | None = None

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


class QwenRunner:
    """Transformers + TorchAO CPU adapter for the KAN-30 benchmark."""

    def __init__(
        self,
        model_id: str = MODEL_ID,
        quantization: Literal["int8", "int4"] = "int8",
        max_new_tokens: int = 64,
    ) -> None:
        self.model_id = model_id
        self.quantization = quantization
        self.max_new_tokens = max_new_tokens
        self._model: Any | None = None
        self._processor: Any | None = None

    def _quantization_config(self) -> Any:
        from transformers import TorchAoConfig  # type: ignore[import-not-found]

        if self.quantization == "int8":
            from torchao.quantization import (  # type: ignore[import-untyped]
                Int8WeightOnlyConfig,
            )

            quant_type = Int8WeightOnlyConfig(group_size=128)
        else:
            from torchao.dtypes import Int4CPULayout  # type: ignore[import-untyped]
            from torchao.quantization import (  # type: ignore[import-untyped]
                Int4WeightOnlyConfig,
            )

            quant_type = Int4WeightOnlyConfig(
                group_size=128,
                layout=Int4CPULayout(),
            )
        return TorchAoConfig(quant_type=quant_type)

    def load(self) -> None:
        from transformers import AutoModelForMultimodalLM, AutoProcessor

        self._processor = AutoProcessor.from_pretrained(self.model_id)
        self._model = AutoModelForMultimodalLM.from_pretrained(
            self.model_id,
            device_map="cpu",
            dtype="auto",
            low_cpu_mem_usage=True,
            quantization_config=self._quantization_config(),
        )
        self._model.eval()

    def analyze(self, image_path: Path) -> str:
        if self._model is None or self._processor is None:
            raise RuntimeError("QwenRunner.load() must be called before analyze()")

        import torch

        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "image", "path": str(image_path.resolve())},
                    {"type": "text", "text": PROMPT},
                ],
            }
        ]
        inputs = self._processor.apply_chat_template(
            messages,
            add_generation_prompt=True,
            tokenize=True,
            return_dict=True,
            return_tensors="pt",
        ).to(self._model.device)

        input_length = inputs["input_ids"].shape[-1]
        with torch.inference_mode():
            output_ids = self._model.generate(
                **inputs,
                max_new_tokens=self.max_new_tokens,
                do_sample=False,
                disable_compile=True,
            )
        generated_ids = output_ids[0][input_length:]
        return self._processor.decode(
            generated_ids,
            skip_special_tokens=True,
            clean_up_tokenization_spaces=False,
        ).strip()


def _process_ram_mb() -> float:
    """Return RSS for this process and its live children."""
    import psutil  # type: ignore[import-untyped]

    process = psutil.Process()
    processes = [process, *process.children(recursive=True)]
    rss_bytes = 0
    for candidate in processes:
        try:
            rss_bytes += candidate.memory_info().rss
        except (psutil.AccessDenied, psutil.NoSuchProcess):
            continue
    return rss_bytes / (1024 * 1024)


def _environment() -> dict[str, str | int | float]:
    import psutil  # type: ignore[import-untyped]

    return {
        "python": platform.python_version(),
        "platform": platform.platform(),
        "cpu": platform.processor() or "unknown",
        "logical_cpu_count": os.cpu_count() or 0,
        "total_ram_mb": round(psutil.virtual_memory().total / (1024 * 1024), 2),
    }


def _validate_images(image_paths: Sequence[Path]) -> tuple[Path, ...]:
    paths = tuple(Path(path) for path in image_paths)
    if len(paths) != REQUIRED_IMAGE_COUNT:
        raise ValueError(
            f"KAN-30 requires exactly {REQUIRED_IMAGE_COUNT} images; got {len(paths)}"
        )
    missing = [str(path) for path in paths if not path.is_file()]
    if missing:
        raise FileNotFoundError(f"benchmark images not found: {', '.join(missing)}")
    return paths


def _defer_reason(
    successful_count: int,
    mean_seconds: float | None,
    error: str | None,
) -> str:
    if error:
        return f"DEFER: benchmark could not complete: {error}"
    if successful_count != REQUIRED_IMAGE_COUNT:
        return (
            f"DEFER: only {successful_count}/{REQUIRED_IMAGE_COUNT} images "
            "completed successfully"
        )
    return (
        f"DEFER: mean inference latency {mean_seconds:.3f}s/image is not below "
        f"the {GO_THRESHOLD_SECONDS:.1f}s target"
    )


def run_benchmark(
    runner: BenchmarkRunner,
    image_paths: Sequence[Path],
    *,
    clock: Callable[[], float] = time.perf_counter,
    ram_reader: Callable[[], float] = _process_ram_mb,
    environment_reader: Callable[[], dict[str, str | int | float]] = _environment,
) -> BenchmarkReport:
    """Run KAN-30 and return a serializable report without writing files."""
    paths = _validate_images(image_paths)
    initial_ram_mb = ram_reader()
    peak_ram_mb = initial_ram_mb
    load_started = clock()
    load_error: str | None = None

    try:
        runner.load()
    except Exception as exc:  # noqa: BLE001 - failures belong in the benchmark report
        load_error = f"{type(exc).__name__}: {exc}"

    load_latency_seconds = max(0.0, clock() - load_started)
    peak_ram_mb = max(peak_ram_mb, ram_reader())
    image_results: list[ImageBenchmarkResult] = []

    if load_error is None:
        for image_path in paths:
            inference_started = clock()
            output: str | None = None
            image_error: str | None = None
            try:
                output = runner.analyze(image_path)
            except Exception as exc:  # noqa: BLE001 - record and continue remaining images
                image_error = f"{type(exc).__name__}: {exc}"
            latency_seconds = max(0.0, clock() - inference_started)
            ram_mb = ram_reader()
            peak_ram_mb = max(peak_ram_mb, ram_mb)
            image_results.append(
                ImageBenchmarkResult(
                    image=image_path.name,
                    latency_seconds=round(latency_seconds, 6),
                    ram_mb=round(ram_mb, 2),
                    succeeded=image_error is None,
                    output=output,
                    error=image_error,
                )
            )

    successful_latencies = [
        result.latency_seconds for result in image_results if result.succeeded
    ]
    successful_count = len(successful_latencies)
    mean_seconds = (
        statistics.fmean(successful_latencies) if successful_latencies else None
    )
    median_seconds = (
        statistics.median(successful_latencies) if successful_latencies else None
    )
    go = (
        load_error is None
        and successful_count == REQUIRED_IMAGE_COUNT
        and mean_seconds is not None
        and mean_seconds < GO_THRESHOLD_SECONDS
    )
    decision_reason = (
        f"GO: mean inference latency {mean_seconds:.3f}s/image is below the "
        f"{GO_THRESHOLD_SECONDS:.1f}s target"
        if go
        else _defer_reason(successful_count, mean_seconds, load_error)
    )

    return BenchmarkReport(
        schema_version=REPORT_SCHEMA_VERSION,
        ticket="KAN-30",
        generated_at=datetime.now(timezone.utc).isoformat(),
        model_id=runner.model_id,
        quantization=runner.quantization,
        device="cpu",
        image_count=len(paths),
        successful_image_count=successful_count,
        load_latency_seconds=round(load_latency_seconds, 6),
        mean_inference_seconds=(round(mean_seconds, 6) if mean_seconds is not None else None),
        median_inference_seconds=(
            round(median_seconds, 6) if median_seconds is not None else None
        ),
        peak_ram_mb=round(peak_ram_mb, 2),
        ram_delta_mb=round(max(0.0, peak_ram_mb - initial_ram_mb), 2),
        go_threshold_seconds=GO_THRESHOLD_SECONDS,
        verdict="GO" if go else "DEFER",
        decision_reason=decision_reason,
        images=image_results,
        environment=environment_reader(),
        error=load_error,
    )


def write_report(report: BenchmarkReport, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(report.to_dict(), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--images",
        nargs=REQUIRED_IMAGE_COUNT,
        type=Path,
        metavar="IMAGE",
        help="exactly five local fashion images (defaults to tests_ia/images)",
    )
    parser.add_argument("--model", default=MODEL_ID)
    parser.add_argument("--quantization", choices=("int8", "int4"), default="int8")
    parser.add_argument("--max-new-tokens", type=int, default=64)
    parser.add_argument("--output", type=Path, default=DEFAULT_REPORT_PATH)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    image_paths = tuple(args.images) if args.images else DEFAULT_IMAGES
    runner = QwenRunner(
        model_id=args.model,
        quantization=args.quantization,
        max_new_tokens=args.max_new_tokens,
    )

    print(f"KAN-30 - loading {runner.model_id} ({runner.quantization}, CPU)")
    report = run_benchmark(runner, image_paths)
    write_report(report, args.output)
    print(f"Report: {args.output}")
    print(report.decision_reason)
    return 0 if report.verdict == "GO" else 1


if __name__ == "__main__":
    sys.exit(main())
