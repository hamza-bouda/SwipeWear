#!/usr/bin/env python3
"""Seed the catalogue with 500+ fashion products and pgvector embeddings.

Generates realistic fashion items across 8 categories, inserts them into
the products table, and writes a 768-dim FashionSigLIP embedding for each
product into product_embeddings (HNSW index already in place from migration
005).

Usage:
    cd backend
    python scripts/seed_catalogue.py             # 500 products, synthetic embeddings
    python scripts/seed_catalogue.py --count 800
    python scripts/seed_catalogue.py --embed     # fetch images + real FashionSigLIP
    python scripts/seed_catalogue.py --reset     # clear catalogue first, then seed

Synthetic mode (default): random L2-normalised vectors grouped by category
-- sufficient for testing retrieval, ranking, and feed correctness without
requiring the model to be downloaded.

Real embed mode (--embed): downloads each product image and runs the
FashionSigLIP model. Requires open_clip, torch, and the model weights
(run setup_models.py first).

Reads DATABASE_URL from .env or environment.
"""
from __future__ import annotations

import argparse
import json
import math
import os
import random
import sys
from pathlib import Path

import psycopg2

# ── .env loader ──────────────────────────────────────────────────────────────
_ENV_PATH = Path(__file__).resolve().parent.parent.parent / ".env"
if _ENV_PATH.exists():
    for _line in _ENV_PATH.read_text(encoding="utf-8").splitlines():
        _line = _line.strip()
        if not _line or _line.startswith("#") or "=" not in _line:
            continue
        k, _, v = _line.partition("=")
        os.environ.setdefault(k.strip(), v.strip())

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

EMBEDDING_VERSION = "fashionsiglip-v1"
VECTOR_DIM = 768

# ── Extended catalogue data ───────────────────────────────────────────────────

_BRANDS_BY_STYLE = {
    "streetwear": ["Supreme", "Stussy", "Palace", "Carhartt", "Dickies",
                   "Nike", "Adidas", "Champion", "Kappa", "Fila"],
    "sport":      ["Nike", "Adidas", "New Balance", "ASICS", "Puma",
                   "Reebok", "Under Armour", "Salomon", "On Running", "Hoka"],
    "classic":    ["Ralph Lauren", "Lacoste", "Fred Perry", "Tommy Hilfiger",
                   "Calvin Klein", "Hackett", "Gant", "Brooks Brothers"],
    "outdoor":    ["The North Face", "Patagonia", "Arc'teryx", "Barbour",
                   "Columbia", "Fjallraven", "Mammut", "Rab"],
    "casual":     ["Uniqlo", "Zara", "H&M", "Mango", "COS",
                   "Arket", "Weekday", "& Other Stories"],
    "premium":    ["Stone Island", "CP Company", "Represent", "Aime Leon Dore",
                   "Our Legacy", "Acne Studios"],
}

_CATALOGUE: dict[str, dict] = {
    "sneakers": {
        "models": [
            ("Air Max 90", "Nike"), ("Air Force 1 Low", "Nike"),
            ("Dunk Low", "Nike"), ("Jordan 1 Mid", "Nike"),
            ("Stan Smith", "Adidas"), ("Gazelle", "Adidas"),
            ("Samba OG", "Adidas"), ("Forum Low", "Adidas"),
            ("990v4", "New Balance"), ("574 Classic", "New Balance"),
            ("550", "New Balance"), ("2002R", "New Balance"),
            ("Gel-Lyte III", "ASICS"), ("Gel-Kayano 14", "ASICS"),
            ("Old Skool", "Vans"), ("Era 59", "Vans"),
            ("Chuck Taylor 70", "Converse"), ("Pro Leather", "Converse"),
            ("Club C 85", "Reebok"), ("Classic Leather", "Reebok"),
            ("Suede Classic", "Puma"), ("Clyde", "Puma"),
            ("XT-6", "Salomon"), ("Speedcross 5", "Salomon"),
        ],
        "sizes": ["38", "39", "40", "41", "42", "43", "44", "45", "46"],
        "colors": ["Blanc", "Noir", "Gris", "Bleu", "Rouge", "Beige",
                   "Vert", "Jaune", "Multicolore", "Crème"],
        "conditions": {"new": 0.08, "like_new": 0.3, "good": 0.45, "fair": 0.17},
        "price_range": (20.0, 280.0),
    },
    "vestes": {
        "models": [
            ("Nuptse 1996", "The North Face"), ("Denali Fleece", "The North Face"),
            ("Chore Coat", "Carhartt"), ("Detroit Jacket", "Carhartt"),
            ("Retro-X Fleece", "Patagonia"), ("Torrentshell 3L", "Patagonia"),
            ("Beta AR Gore-Tex", "Arc'teryx"), ("Atom LT Hoody", "Arc'teryx"),
            ("Waxed Bedale", "Barbour"), ("Liddesdale Quilted", "Barbour"),
            ("Harrington Jacket", "Fred Perry"), ("Harrington Jacket", "Lacoste"),
            ("Coach Jacket", "Stussy"), ("Logo Varsity", "Champion"),
            ("Logo Bomber", "Ralph Lauren"), ("Down Puffer", "Tommy Hilfiger"),
            ("Parka Infinium", "Adidas"), ("Windrunner", "Nike"),
            ("Goggle Jacket", "Stone Island"), ("Shell Jacket", "CP Company"),
        ],
        "sizes": ["XS", "S", "M", "L", "XL", "XXL"],
        "colors": ["Noir", "Kaki", "Marine", "Gris", "Bordeaux",
                   "Beige", "Blanc", "Bleu", "Olive", "Marron"],
        "conditions": {"new": 0.05, "like_new": 0.25, "good": 0.5, "fair": 0.2},
        "price_range": (25.0, 350.0),
    },
    "jeans": {
        "models": [
            ("501 Original", "Levi's"), ("505 Regular", "Levi's"),
            ("510 Skinny", "Levi's"), ("Slim Fit Stretch", "Calvin Klein"),
            ("Relaxed Carpenter Pant", "Carhartt"), ("Double-Knee Pant", "Carhartt"),
            ("874 Work Pant", "Dickies"), ("Slim Straight", "Dickies"),
            ("Chino Classic", "Ralph Lauren"), ("Slim Chino", "Tommy Hilfiger"),
            ("Raw Selvedge", "Uniqlo"), ("Wide Leg", "Zara"),
            ("Cargo Relaxed", "Stussy"), ("Nylon Cargo", "Nike"),
        ],
        "sizes": ["28/30", "30/30", "30/32", "32/30", "32/32",
                  "34/30", "34/32", "36/32", "38/32"],
        "colors": ["Bleu indigo", "Noir", "Gris anthracite", "Kaki",
                   "Beige", "Blanc", "Bleu clair délavé"],
        "conditions": {"new": 0.07, "like_new": 0.22, "good": 0.5, "fair": 0.21},
        "price_range": (12.0, 120.0),
    },
    "hauts": {
        "models": [
            ("Basic Logo Tee", "Stussy"), ("World Tee", "Stussy"),
            ("Graphic Tee", "Champion"), ("Reverse Weave Crewneck", "Champion"),
            ("Polo Classic", "Lacoste"), ("Slim Polo", "Fred Perry"),
            ("Polo Regular", "Ralph Lauren"), ("Polo Sport", "Tommy Hilfiger"),
            ("Pocket Tee", "Patagonia"), ("Dri-Fit Tee", "Nike"),
            ("Adicolor Tee", "Adidas"), ("Vintage Tee", "Carhartt"),
            ("Essential Tee", "Uniqlo"), ("Merino Knit", "Uniqlo"),
            ("Oversized Tee", "H&M"), ("Ribbed Polo", "Arket"),
        ],
        "sizes": ["XS", "S", "M", "L", "XL", "XXL"],
        "colors": ["Blanc", "Noir", "Gris chiné", "Bleu marine",
                   "Rouge", "Vert", "Beige", "Jaune", "Orange"],
        "conditions": {"new": 0.1, "like_new": 0.28, "good": 0.45, "fair": 0.17},
        "price_range": (6.0, 80.0),
    },
    "pulls": {
        "models": [
            ("Crewneck Logo", "Champion"), ("Reverse Weave Hood", "Champion"),
            ("Logo Hoodie", "Nike"), ("Swoosh Hoodie", "Nike"),
            ("Trefoil Hoodie", "Adidas"), ("Zip Hoodie", "Carhartt"),
            ("College Sweat", "Ralph Lauren"), ("Teddy Bear Fleece", "Patagonia"),
            ("Quarter-Zip Fleece", "Patagonia"), ("Merino Crewneck", "Uniqlo"),
            ("Fisherman Rib", "COS"), ("Oversized Knit", "Weekday"),
            ("Cable Knit", "Arket"), ("Wool Turtleneck", "Acne Studios"),
        ],
        "sizes": ["XS", "S", "M", "L", "XL", "XXL"],
        "colors": ["Gris chiné", "Noir", "Blanc cassé", "Marine",
                   "Bordeaux", "Kaki", "Bleu glacier"],
        "conditions": {"new": 0.08, "like_new": 0.27, "good": 0.47, "fair": 0.18},
        "price_range": (15.0, 150.0),
    },
    "shorts": {
        "models": [
            ("Mesh 7in Short", "Nike"), ("Dri-Fit Short", "Nike"),
            ("3-Stripe Short", "Adidas"), ("Training Short", "Adidas"),
            ("Running Short", "New Balance"), ("Nylon Short", "Patagonia"),
            ("Cargo Short", "Carhartt"), ("Work Short", "Dickies"),
            ("Chino Short", "Ralph Lauren"), ("Bermuda Short", "Lacoste"),
        ],
        "sizes": ["XS", "S", "M", "L", "XL", "XXL"],
        "colors": ["Noir", "Gris", "Bleu marine", "Kaki", "Rouge", "Bleu"],
        "conditions": {"new": 0.12, "like_new": 0.3, "good": 0.42, "fair": 0.16},
        "price_range": (8.0, 70.0),
    },
    "chaussures_ville": {
        "models": [
            ("1461 Mono Oxford", "Dr. Martens"), ("2976 Chelsea Boot", "Dr. Martens"),
            ("Classic Boot 6-inch", "Timberland"), ("Premium Boot", "Timberland"),
            ("Loafer Classic", "Clarks"), ("Desert Boot", "Clarks"),
            ("Derby Classic", "Ralph Lauren"), ("Leather Chukka", "Tommy Hilfiger"),
            ("Driving Shoe", "Lacoste"), ("Espadrille Canvas", "Lacoste"),
        ],
        "sizes": ["39", "40", "41", "42", "43", "44", "45"],
        "colors": ["Noir", "Marron", "Bordeaux", "Kaki", "Camel"],
        "conditions": {"new": 0.07, "like_new": 0.25, "good": 0.48, "fair": 0.2},
        "price_range": (30.0, 220.0),
    },
    "accessoires": {
        "models": [
            ("6-Panel Cap", "Nike"), ("Trucker Cap", "Carhartt"),
            ("Bucket Hat", "Stussy"), ("Bucket Hat", "New Balance"),
            ("Fitted Cap", "New Era"), ("Beanie Watch Cap", "Carhartt"),
            ("Beanie Ribbed", "Patagonia"), ("Crossbody Bag", "The North Face"),
            ("Canvas Tote", "Patagonia"), ("Gym Bag", "Nike"),
            ("Canvas Belt", "Levi's"), ("Leather Belt", "Ralph Lauren"),
            ("Crew Socks Pack", "Adidas"), ("Sports Socks", "Nike"),
            ("Sunglasses Classic", "Ralph Lauren"), ("Wool Scarf", "Barbour"),
        ],
        "sizes": ["TU"],
        "colors": ["Noir", "Blanc", "Gris", "Bleu marine", "Kaki", "Beige"],
        "conditions": {"new": 0.15, "like_new": 0.3, "good": 0.4, "fair": 0.15},
        "price_range": (4.0, 90.0),
    },
}

_SOURCES = [("ebay", 0.70), ("etsy", 0.20), ("leboncoin", 0.10)]

_CONDITION_SUFFIXES = {
    "new":       "Neuf avec étiquettes",
    "like_new":  "Très bon état",
    "good":      "Bon état",
    "fair":      "Etat correct",
}


# ── generators ───────────────────────────────────────────────────────────────

def _pick_source() -> str:
    sources, weights = zip(*_SOURCES)
    return random.choices(sources, weights=weights, k=1)[0]


def _pick_condition(weights: dict[str, float]) -> str:
    keys = list(weights.keys())
    wts = [weights[k] for k in keys]
    return random.choices(keys, wts, k=1)[0]


def _price(lo: float, hi: float, condition: str) -> float:
    mult = {"new": 1.0, "like_new": 0.72, "good": 0.50, "fair": 0.30}[condition]
    p = random.uniform(lo * mult, hi * mult)
    return round(p, 2)


def _image_url(category: str, idx: int) -> str:
    seed = (hash(category) * 13 + idx * 7) % 900 + 100
    return f"https://picsum.photos/seed/{seed}/400/600"


def _synthetic_embedding(category: str, model_name: str) -> list[float]:
    """L2-normalised random vector with a category-specific bias.

    Products in the same category cluster together in embedding space,
    which makes retrieval meaningful even without the real model.
    """
    import hashlib
    cat_seed = int(hashlib.md5(f"{category}{model_name}".encode()).hexdigest(), 16) % (2**31)
    rng = random.Random(cat_seed)
    # Category centroid
    centroid = [rng.gauss(0, 1) for _ in range(VECTOR_DIM)]
    # Per-product noise
    noise = [random.gauss(0, 0.5) for _ in range(VECTOR_DIM)]
    vec = [c + n for c, n in zip(centroid, noise)]
    # L2 normalise
    norm = math.sqrt(sum(v * v for v in vec))
    if norm == 0:
        norm = 1.0
    return [v / norm for v in vec]


def _real_embedding(image_url: str) -> list[float] | None:
    """Fetch image and compute real FashionSigLIP embedding (--embed mode)."""
    try:
        import urllib.request
        import numpy as np
        import open_clip  # type: ignore[import]
        import torch  # type: ignore[import]
        from PIL import Image  # type: ignore[import]

        _model_repo = os.getenv("FASHIONSIGLIP_MODEL", "hf-hub:Marqo/marqo-fashionSigLIP")

        # Lazy-load model once
        if not hasattr(_real_embedding, "_model"):
            m, _, p = open_clip.create_model_and_transforms(_model_repo)
            m.eval()
            _real_embedding._model = m  # type: ignore[attr-defined]
            _real_embedding._preprocess = p  # type: ignore[attr-defined]

        with urllib.request.urlopen(image_url, timeout=10) as resp:
            img_bytes = resp.read()

        img = Image.open(__import__("io").BytesIO(img_bytes)).convert("RGB")
        tensor = _real_embedding._preprocess(img).unsqueeze(0)  # type: ignore[attr-defined]
        with torch.no_grad():
            feats = _real_embedding._model.encode_image(tensor)  # type: ignore[attr-defined]
        vec = feats.squeeze(0).cpu().numpy().astype(np.float32)
        norm = float(np.linalg.norm(vec))
        if norm > 0:
            vec = vec / norm
        return vec.tolist()
    except Exception as exc:
        print(f"  WARNING: embedding failed for {image_url}: {exc}")
        return None


def generate_catalogue(count: int) -> list[dict]:
    products = []
    cat_names = list(_CATALOGUE.keys())
    per_cat = max(count // len(cat_names), 1)

    idx = 0
    for cat in cat_names:
        spec = _CATALOGUE[cat]
        n = per_cat if cat != cat_names[-1] else (count - len(products))
        n = max(n, 0)

        models = spec["models"]
        sizes = spec["sizes"]
        colors = spec["colors"]
        cond_weights = spec["conditions"]
        lo, hi = spec["price_range"]

        for i in range(n):
            model_name, brand = models[i % len(models)]
            condition = _pick_condition(cond_weights)
            color = colors[i % len(colors)]
            size = sizes[i % len(sizes)]
            price = _price(lo, hi, condition)
            source = _pick_source()
            suffix = _CONDITION_SUFFIXES[condition]

            title = f"{brand} {model_name} {color} Taille {size} — {suffix}"
            n_images = random.randint(1, 3)
            image_urls = [_image_url(cat, idx + j) for j in range(n_images)]

            products.append({
                "id": f"{source}-cat-{idx:05d}",
                "source": source,
                "source_record_id": f"cat-{idx:05d}",
                "title": title,
                "price": price,
                "condition": condition,
                "category": cat,
                "image_urls": image_urls,
                "size_raw": size,
                "size_eu": size,
                "brand": brand,
                "available": True,
                "_category": cat,        # for embedding grouping, stripped before insert
                "_model_name": model_name,
                "_image_url": image_urls[0],
            })
            idx += 1

    return products


# ── DB operations ─────────────────────────────────────────────────────────────

_INSERT_PRODUCT = """\
INSERT INTO products
    (id, source, source_record_id, title, price, condition,
     category, image_urls, size_raw, size_eu, brand, available)
VALUES
    (%(id)s, %(source)s, %(source_record_id)s, %(title)s,
     %(price)s, %(condition)s, %(category)s, %(image_urls)s,
     %(size_raw)s, %(size_eu)s, %(brand)s, %(available)s)
ON CONFLICT (id) DO NOTHING"""

_INSERT_EMBEDDING = """\
INSERT INTO product_embeddings (product_id, embedding, embedding_version)
VALUES (%s, %s::vector, %s)
ON CONFLICT DO NOTHING"""


def seed(conn, products: list[dict], use_real_embed: bool, reset: bool) -> None:
    with conn.cursor() as cur:
        if reset:
            cur.execute("DELETE FROM product_embeddings")
            cur.execute("DELETE FROM interaction_events")
            cur.execute("DELETE FROM products")
            print("  Cleared existing catalogue.")

    inserted_prod = 0
    inserted_emb = 0
    total = len(products)

    for i, p in enumerate(products, start=1):
        cat = p.pop("_category")
        model_name = p.pop("_model_name")
        image_url = p.pop("_image_url")

        with conn.cursor() as cur:
            cur.execute(_INSERT_PRODUCT, {
                **p,
                "image_urls": p["image_urls"],
            })
            if cur.rowcount > 0:
                inserted_prod += 1

                if use_real_embed:
                    vec = _real_embedding(image_url)
                    if vec is None:
                        vec = _synthetic_embedding(cat, model_name)
                else:
                    vec = _synthetic_embedding(cat, model_name)

                vec_str = "[" + ",".join(f"{v:.8f}" for v in vec) + "]"
                cur.execute(_INSERT_EMBEDDING, (p["id"], vec_str, EMBEDDING_VERSION))
                inserted_emb += 1

        conn.commit()
        if i % 50 == 0 or i == total:
            mode = "real" if use_real_embed else "synthetic"
            print(f"  {i}/{total} — {inserted_prod} products, {inserted_emb} embeddings ({mode})")


# ── main ─────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="Seed SwipeWear catalogue")
    parser.add_argument("--count", type=int, default=500,
                        help="Number of products to generate (default: 500)")
    parser.add_argument("--embed", action="store_true",
                        help="Use real FashionSigLIP embeddings (requires model + internet)")
    parser.add_argument("--reset", action="store_true",
                        help="Delete all existing products first")
    args = parser.parse_args()

    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        print("ERROR: DATABASE_URL not set. Check your .env file.")
        sys.exit(1)

    print(f"Generating {args.count} catalogue products "
          f"({'real embeddings' if args.embed else 'synthetic embeddings'})…")
    products = generate_catalogue(args.count)
    print(f"Generated {len(products)} products across {len(_CATALOGUE)} categories.")

    print("Connecting to DB…")
    conn = psycopg2.connect(db_url)
    try:
        seed(conn, products, use_real_embed=args.embed, reset=args.reset)
    finally:
        conn.close()

    with psycopg2.connect(db_url) as conn2:
        with conn2.cursor() as cur:
            cur.execute("SELECT category, COUNT(*) FROM products GROUP BY category ORDER BY category")
            print("\nProducts by category:")
            for cat, cnt in cur.fetchall():
                print(f"  {cat:20s} {cnt}")
            cur.execute("SELECT COUNT(*) FROM products")
            total_p = cur.fetchone()[0]
            cur.execute("SELECT COUNT(*) FROM product_embeddings")
            total_e = cur.fetchone()[0]
            print(f"  {'TOTAL':20s} {total_p} products, {total_e} embeddings indexed")

    print("\nDone. Run backend to verify feed endpoint.")


if __name__ == "__main__":
    main()
