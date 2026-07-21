"""Measure SegFormer impact on a local FashionSigLIP golden image scenario."""
from __future__ import annotations

import importlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from evaluation.segmentation_recall import compare_recall_at_10

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
IMAGE_ROOT = REPOSITORY_ROOT / "tests_ia" / "images"
REPORT_PATH = Path(__file__).resolve().parent / "reports" / "segmentation_recall.json"

CATALOGUE = {
    "bag.jpg": "accessory",
    "glasses.jpg": "accessory",
    "jacket.jpg": "outerwear",
    "jeans.jpg": "pants",
    "man.jpg": "outerwear",
    "rack.jpg": "outerwear",
    "shop.jpg": "outerwear",
    "sneaker.jpg": "footwear",
    "sneaker2.jpg": "footwear",
    "tee.jpg": "tops",
    "tees.jpg": "tops",
    "watch.jpg": "accessory",
    "woman.jpg": "outerwear",
}
QUERIES = {
    "accessory": "a fashion accessory",
    "footwear": "a pair of shoes",
    "outerwear": "a jacket or coat",
    "pants": "a pair of jeans or pants",
    "tops": "a t-shirt or top",
}


def run() -> dict[str, Any]:
    segmentation = importlib.import_module("vision.segmentation")
    embedding_service = _embedding_service()
    segmenter = segmentation.TransformersSegFormerRunner()
    baseline_vectors = {}
    segmented_vectors = {}
    cases = []

    for image_name, category in CATALOGUE.items():
        image = (IMAGE_ROOT / image_name).read_bytes()
        isolation = segmentation.isolate_garment_with_result(
            image,
            runner=segmenter,
        )
        baseline_vectors[image_name] = embedding_service.encode_image(image)
        segmented_vectors[image_name] = embedding_service.encode_image(
            isolation.image
        )
        cases.append(
            {
                "image": image_name,
                "category": category,
                "person_detected": isolation.person_detected,
                "segmentation_applied": isolation.applied,
                "garment_fraction": round(isolation.garment_fraction, 6),
                "fallback_used": isolation.fallback_used,
                "fallback_reason": isolation.fallback_reason,
            }
        )
        print(
            f"{image_name}: person={isolation.person_detected} "
            f"applied={isolation.applied}"
        )

    if getattr(embedding_service, "supports_text", True):
        query_vectors = {
            query_id: embedding_service.encode_text(text)
            for query_id, text in QUERIES.items()
        }
        relevant = {
            query_id: {
                image_name
                for image_name, category in CATALOGUE.items()
                if category == query_id
            }
            for query_id in QUERIES
        }
        scenario = "tests_ia golden image catalogue with five text queries"
    else:
        query_vectors, relevant = _image_queries(baseline_vectors)
        scenario = (
            "tests_ia golden image catalogue with leave-one-out image queries"
        )
    comparison = compare_recall_at_10(
        query_vectors,
        baseline_vectors,
        segmented_vectors,
        relevant,
    )
    report = {
        "ticket": "KAN-68",
        "date": datetime.now(timezone.utc).isoformat(),
        "segmentation_model": segmentation.MODEL_ID,
        "embedding_model": embedding_service.embedding_version,
        "scenario": scenario,
        "catalogue_size": len(CATALOGUE),
        "query_count": len(query_vectors),
        "recall_at_10": comparison.to_dict(),
        "activated": comparison.activated,
        "activation_rule": "activate only when Recall@10 gain is strictly positive",
        "cases": cases,
    }
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return report


def _embedding_service():
    onnx_dir = Path(
        os.getenv(
            "FASHIONSIGLIP_ONNX_DIR",
            str(
                Path("C:/Users/Lenovo/.cache/swipewear/models")
                / "marqo-fashionSigLIP-q4f16"
            ),
        )
    )
    vision_path = Path(
        os.getenv(
            "FASHIONSIGLIP_VISION_ONNX",
            str(onnx_dir / "vision_model_q4f16.onnx"),
        )
    )
    text_path = Path(
        os.getenv(
            "FASHIONSIGLIP_TEXT_ONNX",
            str(onnx_dir / "text_model_q4f16.onnx"),
        )
    )
    vision_only = os.getenv("FASHIONSIGLIP_IMAGE_ONLY") == "1"
    if vision_path.is_file() and (text_path.is_file() or vision_only):
        if vision_only:
            tokenizer_dir = onnx_dir
        else:
            from huggingface_hub import snapshot_download

            tokenizer_dir = Path(
                snapshot_download(
                    "Marqo/marqo-fashionSigLIP",
                    local_files_only=True,
                )
            )
        onnx_module = importlib.import_module("embeddings.fashionsiglip_onnx")
        return onnx_module.OnnxFashionSigLIPService(
            onnx_dir,
            tokenizer_dir,
            vision_only=vision_only,
            vision_model_path=vision_path,
            text_model_path=text_path,
        )
    fashionsiglip = importlib.import_module("embeddings.fashionsiglip")
    return fashionsiglip.get_service()


def _image_queries(baseline_vectors):
    query_vectors = {}
    relevant = {}
    for image_name, category in CATALOGUE.items():
        matches = {
            candidate
            for candidate, candidate_category in CATALOGUE.items()
            if candidate_category == category and candidate != image_name
        }
        if matches:
            query_vectors[image_name] = baseline_vectors[image_name]
            relevant[image_name] = matches
    return query_vectors, relevant


if __name__ == "__main__":
    measured = run()
    print(json.dumps(measured["recall_at_10"], sort_keys=True))
    print(f"activated={measured['activated']}")
