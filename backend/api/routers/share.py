"""Share card generation endpoint (F09).

Generates a shareable PNG image for a product showing:
- Product image
- Price + savings percentage
- SwipeWear watermark

GET /share/{product_id}?savings_pct=72 -> image/png
"""
from __future__ import annotations

import io
import logging
from typing import Any

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse

from api.db import get_conn, put_conn

_LOG = logging.getLogger("swipewear.api.share")

router = APIRouter(prefix="/share", tags=["share"])

_CARD_WIDTH = 1080
_CARD_HEIGHT = 1920


def _fetch_product(conn: Any, product_id: str) -> dict | None:
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT id, title, brand, price, condition, image_urls, listing_url
            FROM products
            WHERE id = %s AND available = true
            """,
            (product_id,),
        )
        row = cur.fetchone()
    if row is None:
        return None
    return {
        "id": row[0],
        "title": row[1],
        "brand": row[2],
        "price": float(row[3]) if row[3] else 0,
        "condition": row[4],
        "image_urls": list(row[5] or []),
        "listing_url": row[6],
    }


def _generate_card(product: dict, savings_pct: int | None) -> bytes:
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        _LOG.warning("Pillow not installed, using SVG fallback")
        return _generate_svg_card(product, savings_pct)

    img = Image.new("RGB", (_CARD_WIDTH, _CARD_HEIGHT), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)

    try:
        font_large = ImageFont.truetype("arial.ttf", 64)
        font_medium = ImageFont.truetype("arial.ttf", 48)
        font_small = ImageFont.truetype("arial.ttf", 36)
    except OSError:
        font_large = ImageFont.load_default()
        font_medium = font_large
        font_small = font_large

    # Yellow accent bar at top
    draw.rectangle([(0, 0), (_CARD_WIDTH, 120)], fill=(250, 204, 21))
    draw.text(
        (_CARD_WIDTH // 2, 60), "SwipeWear",
        fill=(10, 10, 10), font=font_large, anchor="mm",
    )

    # Product info area
    y = 900
    title = product["title"][:50]
    draw.text(
        (_CARD_WIDTH // 2, y), title,
        fill=(10, 10, 10), font=font_medium, anchor="mm",
    )

    y += 80
    brand = product.get("brand") or ""
    if brand:
        draw.text(
            (_CARD_WIDTH // 2, y), brand,
            fill=(120, 120, 120), font=font_small, anchor="mm",
        )
        y += 60

    y += 20
    price_text = f"{product['price']:.0f} EUR"
    draw.text(
        (_CARD_WIDTH // 2, y), price_text,
        fill=(10, 10, 10), font=font_large, anchor="mm",
    )

    if savings_pct and savings_pct > 0:
        y += 100
        draw.rectangle(
            [(_CARD_WIDTH // 2 - 200, y - 40), (_CARD_WIDTH // 2 + 200, y + 40)],
            fill=(250, 204, 21),
        )
        draw.text(
            (_CARD_WIDTH // 2, y), f"-{savings_pct}% vs neuf",
            fill=(10, 10, 10), font=font_medium, anchor="mm",
        )

    # Footer
    draw.rectangle([(0, _CARD_HEIGHT - 100), (_CARD_WIDTH, _CARD_HEIGHT)], fill=(10, 10, 10))
    draw.text(
        (_CARD_WIDTH // 2, _CARD_HEIGHT - 50),
        "swipewear.fr",
        fill=(250, 204, 21), font=font_small, anchor="mm",
    )

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def _generate_svg_card(product: dict, savings_pct: int | None) -> bytes:
    title = product["title"][:50]
    brand = product.get("brand") or ""
    price = f"{product['price']:.0f} EUR"
    savings_block = ""
    if savings_pct and savings_pct > 0:
        savings_block = f"""
        <rect x="340" y="580" width="400" height="60" rx="8" fill="#facc15"/>
        <text x="540" y="618" text-anchor="middle"
              font-size="32" font-weight="bold" fill="#0A0A0A">-{savings_pct}% vs neuf</text>
        """

    svg = f"""<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="1080" height="1920" viewBox="0 0 1080 1920">
  <rect width="1080" height="1920" fill="#FFFFFF"/>
  <rect width="1080" height="120" fill="#facc15"/>
  <text x="540" y="75" text-anchor="middle"
        font-family="Arial,sans-serif" font-size="64" font-weight="bold"
        fill="#0A0A0A">SwipeWear</text>
  <rect y="200" x="140" width="800" height="600" rx="16" fill="#F5F5F5"/>
  <text x="540" y="540" text-anchor="middle" font-family="Arial,sans-serif"
        font-size="24" fill="#999">Image produit</text>
  <text x="540" y="900" text-anchor="middle"
        font-family="Arial,sans-serif" font-size="48" fill="#0A0A0A">{title}</text>
  <text x="540" y="960" text-anchor="middle"
        font-family="Arial,sans-serif" font-size="36" fill="#787878">{brand}</text>
  <text x="540" y="1060" text-anchor="middle"
        font-family="Arial,sans-serif" font-size="64" font-weight="bold"
        fill="#0A0A0A">{price}</text>
  {savings_block}
  <rect y="1820" width="1080" height="100" fill="#0A0A0A"/>
  <text x="540" y="1880" text-anchor="middle"
        font-family="Arial,sans-serif" font-size="36" fill="#facc15">swipewear.fr</text>
</svg>"""
    return svg.encode("utf-8")


@router.get("/{product_id}")
def get_share_card(
    product_id: str,
    savings_pct: int | None = Query(None, ge=0, le=99),
):
    conn = None
    try:
        conn = get_conn()
        product = _fetch_product(conn, product_id)
    finally:
        if conn is not None:
            put_conn(conn)

    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")

    try:
        from PIL import Image  # noqa: F401
        card_bytes = _generate_card(product, savings_pct)
        media_type = "image/png"
    except ImportError:
        card_bytes = _generate_svg_card(product, savings_pct)
        media_type = "image/svg+xml"

    return StreamingResponse(
        io.BytesIO(card_bytes),
        media_type=media_type,
        headers={
            "Content-Disposition": f'inline; filename="swipewear-{product_id}.png"',
            "Cache-Control": "public, max-age=3600",
        },
    )
