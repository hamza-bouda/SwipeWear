"""Title enrichment via GLiNER NER — extracts brand, model, size, color, condition."""
from __future__ import annotations

import logging
import os
from typing import Any

from contracts.product import ProductRecord
from ingestion.normalizer import _normalize_size

_LOG = logging.getLogger(__name__)

_GLINER_LABELS = ["marque", "modèle", "taille", "couleur", "état"]
_MODEL_NAME = os.getenv("GLINER_MODEL", "urchade/gliner_medium-v2.1")

_model: Any = None


def _get_model() -> Any:
    global _model
    if _model is None:
        from gliner import GLiNER  # type: ignore[import]
        _model = GLiNER.from_pretrained(_MODEL_NAME)
    return _model


class TitleEnricher:
    """Enriches ProductRecord fields using GLiNER NER on the product title.

    The GLiNER model is a module-level singleton: loaded once on first call,
    reused for all subsequent calls — no per-instance reload.

    Fallback contract: if GLiNER is unavailable or inference fails, the
    original ProductRecord is returned unchanged. The pipeline never crashes.
    """

    def enrich(self, record: ProductRecord) -> ProductRecord:
        try:
            model = _get_model()
            entities: list[dict[str, Any]] = model.predict_entities(
                record.title, _GLINER_LABELS, threshold=0.5
            )
            attrs: dict[str, str] = {}
            for ent in entities:
                label: str = ent["label"]
                if label not in attrs:
                    attrs[label] = ent["text"]

            update: dict[str, Any] = {"enriched_attrs": attrs}

            if "marque" in attrs and not record.brand:
                update["brand"] = attrs["marque"]
            if "modèle" in attrs and not record.model:
                update["model"] = attrs["modèle"]
            if "taille" in attrs and not record.size_eu:
                _, size_eu = _normalize_size(attrs["taille"])
                if size_eu:
                    update["size_eu"] = size_eu

            return record.model_copy(update=update)
        except Exception:
            _LOG.warning("GLiNER enrichment failed for %r — returning unchanged", record.id)
            return record
