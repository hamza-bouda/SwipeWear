#!/usr/bin/env python3
"""Seed the products table with realistic fashion items for development.

Usage:
    cd backend
    python scripts/seed_products.py          # insert 100 products
    python scripts/seed_products.py --count 50
    python scripts/seed_products.py --reset   # delete all then re-seed

Reads DATABASE_URL from .env (via dotenv) or environment.
"""
from __future__ import annotations

import argparse
import os
import random
import sys
from pathlib import Path

import psycopg2

# ── Load .env from project root ──────────────────────────────────────────────
_ENV_PATH = Path(__file__).resolve().parent.parent.parent / ".env"
if _ENV_PATH.exists():
    for line in _ENV_PATH.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" in line:
            key, _, val = line.partition("=")
            os.environ.setdefault(key.strip(), val.strip())

# ── Product catalogue data ───────────────────────────────────────────────────

BRANDS = [
    "Nike", "Adidas", "Levi's", "The North Face", "Carhartt",
    "New Balance", "Stussy", "Dickies", "Patagonia", "Ralph Lauren",
    "Tommy Hilfiger", "Calvin Klein", "Champion", "Converse", "Vans",
    "Dr. Martens", "Timberland", "Lacoste", "Fred Perry", "Barbour",
    "Stone Island", "CP Company", "Arc'teryx", "Salomon", "ASICS",
    "Reebok", "Puma", "Fila", "Kappa", "Ellesse",
    "Uniqlo", "Zara", "H&M", "Mango", "COS",
]

CATEGORIES = {
    "sneakers": {
        "templates": [
            "{brand} Air Max 90",
            "{brand} 574 Classic",
            "{brand} Old Skool",
            "{brand} Chuck Taylor All Star",
            "{brand} Gel-Kayano 14",
            "{brand} Suede Classic",
            "{brand} Club C 85",
            "{brand} Forum Low",
            "{brand} 550",
            "{brand} Dunk Low Retro",
            "{brand} Stan Smith",
            "{brand} Gazelle",
            "{brand} XT-6",
        ],
        "brands": [
            "Nike", "New Balance", "Vans", "Converse", "ASICS",
            "Puma", "Reebok", "Adidas", "New Balance", "Nike",
            "Adidas", "Adidas", "Salomon",
        ],
    },
    "vestes": {
        "templates": [
            "{brand} Nuptse 1996 Retro",
            "{brand} Chore Coat",
            "{brand} Retro-X Fleece Jacket",
            "{brand} Waxed Bedale Jacket",
            "{brand} Harrington Jacket",
            "{brand} Denali Fleece",
            "{brand} Coach Jacket Logo",
            "{brand} Bomber MA-1 Vintage",
            "{brand} Overshirt Workwear",
            "{brand} Beta AR Gore-Tex",
            "{brand} Puffer Jacket",
            "{brand} Denim Trucker Jacket",
        ],
        "brands": [
            "The North Face", "Carhartt", "Patagonia", "Barbour",
            "Fred Perry", "The North Face", "Stussy", "Ralph Lauren",
            "Dickies", "Arc'teryx", "Tommy Hilfiger", "Levi's",
        ],
    },
    "jeans": {
        "templates": [
            "{brand} 501 Original Fit",
            "{brand} 505 Regular Straight",
            "{brand} Slim Fit Stretch Denim",
            "{brand} Relaxed Fit Carpenter Pant",
            "{brand} 874 Original Work Pant",
            "{brand} Chino Classic Fit",
            "{brand} Jogger Pant",
            "{brand} Straight Leg Raw Denim",
            "{brand} Cargo Pant Vintage",
            "{brand} Wide Leg Jean",
        ],
        "brands": [
            "Levi's", "Levi's", "Calvin Klein", "Carhartt",
            "Dickies", "Ralph Lauren", "Nike", "Uniqlo",
            "Stussy", "Zara",
        ],
    },
    "tee-shirts": {
        "templates": [
            "{brand} Basic Logo Tee",
            "{brand} Graphic Print T-Shirt",
            "{brand} Polo Classic Fit",
            "{brand} Heavyweight Crew Neck",
            "{brand} Striped Long Sleeve",
            "{brand} Vintage Wash Tee",
            "{brand} Essential Cotton Tee",
            "{brand} Oversized Box Logo",
            "{brand} Pocket Tee",
            "{brand} Performance Dri-Fit Tee",
        ],
        "brands": [
            "Stussy", "Champion", "Lacoste", "Carhartt",
            "Fred Perry", "Ralph Lauren", "Uniqlo", "Nike",
            "Patagonia", "Nike",
        ],
    },
    "accessoires": {
        "templates": [
            "{brand} Classic Cap",
            "{brand} Beanie Knit",
            "{brand} Crossbody Bag",
            "{brand} Canvas Tote Bag",
            "{brand} Leather Belt",
            "{brand} Crew Socks 3-Pack",
            "{brand} Sunglasses Wayfarer",
            "{brand} Watch Classic",
            "{brand} Scarf Wool Blend",
            "{brand} Bucket Hat",
        ],
        "brands": [
            "Nike", "Carhartt", "The North Face", "Patagonia",
            "Levi's", "Adidas", "Ralph Lauren", "Tommy Hilfiger",
            "Lacoste", "Stussy",
        ],
    },
}

CONDITIONS = ["new", "like_new", "good", "fair"]
CONDITION_WEIGHTS = [0.1, 0.25, 0.4, 0.25]

SIZES_CLOTHING = ["XS", "S", "M", "L", "XL", "XXL"]
SIZES_SHOES = ["38", "39", "40", "41", "42", "43", "44", "45"]

SOURCES = ["ebay", "etsy"]

# Unsplash keywords → realistic fashion photos (public, free)
_IMAGE_SEEDS = {
    "sneakers": [
        "sneakers", "running-shoes", "white-sneakers", "vintage-shoes",
        "basketball-shoes", "skateboard-shoes", "casual-shoes",
    ],
    "vestes": [
        "jacket", "denim-jacket", "leather-jacket", "puffer-jacket",
        "fleece-jacket", "winter-coat", "bomber-jacket",
    ],
    "jeans": [
        "jeans", "denim", "pants", "trousers", "cargo-pants",
        "chinos", "workwear-pants",
    ],
    "tee-shirts": [
        "tshirt", "polo-shirt", "graphic-tee", "cotton-tee",
        "striped-shirt", "casual-shirt", "crew-neck",
    ],
    "accessoires": [
        "cap", "beanie", "crossbody-bag", "tote-bag", "sunglasses",
        "watch", "bucket-hat",
    ],
}


def _price_for_category(category: str, condition: str) -> float:
    base_ranges = {
        "sneakers": (25.0, 180.0),
        "vestes": (30.0, 250.0),
        "jeans": (15.0, 90.0),
        "tee-shirts": (8.0, 55.0),
        "accessoires": (5.0, 75.0),
    }
    lo, hi = base_ranges.get(category, (10.0, 100.0))
    condition_mult = {
        "new": 1.0, "like_new": 0.75, "good": 0.55, "fair": 0.35,
    }
    mult = condition_mult.get(condition, 0.6)
    price = random.uniform(lo * mult, hi * mult)
    return round(price, 2)


def _image_url(category: str, idx: int) -> str:
    seed_id = (hash(category) + idx) % 1000 + 100
    return f"https://picsum.photos/seed/{seed_id}/400/600"


def generate_products(count: int) -> list[dict]:
    products = []
    cat_names = list(CATEGORIES.keys())
    per_cat = max(count // len(cat_names), 1)

    prod_idx = 0
    for cat in cat_names:
        cat_data = CATEGORIES[cat]
        templates = cat_data["templates"]
        cat_brands = cat_data["brands"]

        n = per_cat if cat != cat_names[-1] else count - len(products)
        for i in range(n):
            tmpl_idx = i % len(templates)
            brand = cat_brands[tmpl_idx % len(cat_brands)]
            title = templates[tmpl_idx].format(brand=brand)

            condition = random.choices(CONDITIONS, CONDITION_WEIGHTS)[0]
            price = _price_for_category(cat, condition)
            source = random.choice(SOURCES)

            if cat == "sneakers":
                size_raw = random.choice(SIZES_SHOES)
                size_eu = size_raw
            else:
                size_raw = random.choice(SIZES_CLOTHING)
                size_eu = size_raw

            n_images = random.randint(1, 3)
            image_urls = [
                _image_url(cat, prod_idx + img_i) for img_i in range(n_images)
            ]

            product = {
                "id": f"{source}-seed-{prod_idx:04d}",
                "source": source,
                "source_record_id": f"seed-{prod_idx:04d}",
                "title": title,
                "price": price,
                "condition": condition,
                "category": cat,
                "image_urls": image_urls,
                "size_raw": size_raw,
                "size_eu": size_eu,
                "brand": brand,
            }
            products.append(product)
            prod_idx += 1

    return products


def insert_products(conn, products: list[dict], reset: bool = False) -> int:
    with conn.cursor() as cur:
        if reset:
            cur.execute("DELETE FROM product_embeddings")
            cur.execute("DELETE FROM interaction_events")
            cur.execute("DELETE FROM products")
            print("  Cleared existing products.")

        inserted = 0
        for p in products:
            cur.execute(
                """
                INSERT INTO products
                    (id, source, source_record_id, title, price, condition,
                     category, image_urls, size_raw, size_eu, brand)
                VALUES
                    (%(id)s, %(source)s, %(source_record_id)s, %(title)s,
                     %(price)s, %(condition)s, %(category)s, %(image_urls)s,
                     %(size_raw)s, %(size_eu)s, %(brand)s)
                ON CONFLICT (id) DO NOTHING
                """,
                p,
            )
            if cur.rowcount > 0:
                inserted += 1

    conn.commit()
    return inserted


def main():
    parser = argparse.ArgumentParser(description="Seed products for dev")
    parser.add_argument("--count", type=int, default=100)
    parser.add_argument("--reset", action="store_true")
    args = parser.parse_args()

    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        print("ERROR: DATABASE_URL not set. Check your .env file.")
        sys.exit(1)

    print(f"Generating {args.count} products...")
    products = generate_products(args.count)

    print("Connecting to DB...")
    conn = psycopg2.connect(db_url)
    try:
        inserted = insert_products(conn, products, reset=args.reset)
        print(f"Done! {inserted} products inserted.")

        with conn.cursor() as cur:
            cur.execute(
                "SELECT category, COUNT(*) FROM products"
                " GROUP BY category ORDER BY category"
            )
            print("\nProducts by category:")
            for cat, cnt in cur.fetchall():
                print(f"  {cat}: {cnt}")
            cur.execute("SELECT COUNT(*) FROM products")
            total = cur.fetchone()[0]
            print(f"  TOTAL: {total}")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
