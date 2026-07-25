"""Fetch a single product by id.

ProductDetailScreen fell back to a hardcoded MOCK_PRODUCTS list whenever it was
opened without a product already in hand — from the wardrobe, an alert, or a
deep link. It would then show an invented item under a real id, with a price
nobody could pay.
"""
from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException

from api.auth import get_current_user_id
from api.db import get_conn, put_conn
from contracts.product import ProductCondition, ProductRecord, ProductSource

_LOG = logging.getLogger("swipewear.api.products")

router = APIRouter(prefix="/products", tags=["products"])

_COLUMNS = [
    "id", "source", "source_record_id", "title", "brand", "model", "gender",
    "price", "condition", "size_raw", "size_eu",
    "category", "image_urls", "available", "embedding_version", "listing_url",
]

_QUERY = "SELECT {columns} FROM products AS p WHERE p.id = %(product_id)s"


@router.get("/{product_id:path}", response_model=ProductRecord)
def get_product(product_id: str, _user_id=Depends(get_current_user_id)):
    """Return one product, or 404 — never a substitute.

    The path converter matters: catalogue ids look like
    "ebay-v1|127396173312|428490506", and the pipe would otherwise have to be
    escaped by every caller.
    """
    conn = None
    try:
        conn = get_conn()
        query = _QUERY.format(columns=", ".join(f"p.{c}" for c in _COLUMNS))
        with conn.cursor() as cur:
            cur.execute(query, {"product_id": product_id})
            row = cur.fetchone()
        if row is None:
            raise HTTPException(
                status_code=404,
                detail={
                    "error": "product_not_found",
                    "message": "Ce produit n'existe pas ou n'est plus en ligne.",
                },
            )
        data = dict(zip(_COLUMNS, row))
        data["source"] = ProductSource(data["source"])
        data["condition"] = ProductCondition(data["condition"])
        data["price"] = float(data["price"])
        data["image_urls"] = list(data["image_urls"] or [])
        # The column holds the raw seller URL; affiliate deep links are derived
        # from it at serve time.
        data["affiliate_url"] = data.pop("listing_url", None)
        return ProductRecord(**data)
    except HTTPException:
        raise
    except Exception:
        _LOG.error("Failed to load product %s", product_id, exc_info=True)
        if conn is not None:
            try:
                conn.rollback()
            except Exception:  # noqa: BLE001 - never mask the original failure
                pass
        raise HTTPException(
            status_code=503,
            detail={
                "error": "product_unavailable",
                "message": "Impossible de charger ce produit.",
            },
        )
    finally:
        if conn is not None:
            put_conn(conn)
