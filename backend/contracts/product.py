from __future__ import annotations

from enum import Enum
from typing import Annotated

from pydantic import BaseModel, Field, field_validator


SCHEMA_VERSION = 1


class ProductSource(str, Enum):
    ebay = "ebay"
    awin = "awin"
    cj = "cj"


class ProductCondition(str, Enum):
    new = "new"
    like_new = "like_new"
    good = "good"
    fair = "fair"


class ProductRecord(BaseModel):
    # ── Identity ──────────────────────────────────────────────────────────────
    id: str
    source: ProductSource
    source_record_id: str

    # ── Description ──────────────────────────────────────────────────────────
    title: str
    brand: str | None = None
    model: str | None = None

    # ── Price ─────────────────────────────────────────────────────────────────
    price: Annotated[float, Field(gt=0)]
    currency: str = "EUR"
    condition: ProductCondition

    # ── Size ──────────────────────────────────────────────────────────────────
    size_raw: str | None = None
    size_eu: str | None = None

    # ── Misc ──────────────────────────────────────────────────────────────────
    category: str
    image_urls: Annotated[list[str], Field(min_length=1)]
    affiliate_url: str | None = None
    available: bool = True

    # ── Versioning ────────────────────────────────────────────────────────────
    schema_version: int = SCHEMA_VERSION
    embedding_version: str | None = None

    @field_validator("price")
    @classmethod
    def price_must_be_positive(cls, v: float) -> float:
        if v <= 0:
            raise ValueError(f"price must be > 0, got {v}")
        return v

    @field_validator("image_urls")
    @classmethod
    def image_urls_must_not_be_empty(cls, v: list[str]) -> list[str]:
        if not v:
            raise ValueError("image_urls must contain at least one URL")
        return v
