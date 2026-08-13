#!/usr/bin/env python3
"""
SwipeWear — Test de faisabilité de la stack IA open source (pré-Gate 1).

Valide sur de vraies photos que chaque brique du MVP fonctionne AVANT d'écrire
le backend. Chaque étape est indépendante : un échec n'arrête pas les autres.

Usage :
    python test_stack_ia.py              # étapes cœur : embeddings mode + retrieval texte + parsing titres
    python test_stack_ia.py --all        # + DINOv2 (même pièce) + SegFormer (segmentation)
    python test_stack_ia.py --skip-download-check   # si les modèles sont déjà en cache

Critères GO/NO-GO en fin de rapport.
"""

import argparse
import sys
import time
from pathlib import Path

IMAGES_DIR = Path(__file__).parent / "images"

# Vérités terrain pour les tests de similarité (paire_proche, intrus)
# ex. sneaker doit être plus proche de sneaker2 que de watch.
SIMILARITY_CHECKS = [
    ("sneaker", "sneaker2", "watch"),
    ("jacket", "man", "sneaker"),
    ("tee", "tees", "bag"),
    ("jeans", "tees", "glasses"),
]

# Requêtes texte -> image attendue en top-1 (test du pont texte/image de FashionSigLIP)
TEXT_QUERIES = [
    ("a brown leather jacket", "jacket"),
    ("a pair of sneakers", "sneaker"),
    ("blue denim jeans", "jeans"),
    ("aviator sunglasses", "glasses"),
    ("a wrist watch", "watch"),
    ("a canvas backpack", "bag"),
]

# Titres d'annonces façon Vinted pour le test de parsing (F19 / ingestion)
LISTING_TITLES = [
    "Veste Carhartt Detroit taille M très bon état marron",
    "Levis 501 vintage W30 L32 bleu délavé",
    "Nike Air Force 1 blanches pointure 42 peu portées",
    "Perfecto cuir Schott NYC taille L années 90",
    "tee shirt ralph lauren blanc M neuf avec etiquette",
]
PARSING_LABELS = ["marque", "modèle", "taille", "couleur", "état"]

RESULTS: list[tuple[str, str, str]] = []  # (étape, statut, détail)


def record(step: str, ok: bool, detail: str) -> None:
    status = "PASS" if ok else "FAIL"
    RESULTS.append((step, status, detail))
    icon = "✅" if ok else "❌"
    print(f"\n{icon} [{status}] {step} — {detail}")


def record_skip(step: str, reason: str) -> None:
    RESULTS.append((step, "SKIP", reason))
    print(f"\n⏭️  [SKIP] {step} — {reason}")


def load_images() -> dict:
    from PIL import Image
    images = {}
    for f in sorted(IMAGES_DIR.glob("*.jpg")):
        images[f.stem] = Image.open(f).convert("RGB")
    return images


# ---------------------------------------------------------------- étape 0
def step0_environment() -> bool:
    print("=" * 70)
    print("ÉTAPE 0 · Environnement")
    print("=" * 70)
    py = sys.version_info
    print(f"Python {py.major}.{py.minor}.{py.micro}")
    missing = []
    for mod, pkg in [("PIL", "pillow"), ("torch", "torch"), ("open_clip", "open_clip_torch"),
                     ("numpy", "numpy")]:
        try:
            __import__(mod)
            print(f"  ✓ {pkg}")
        except ImportError:
            print(f"  ✗ {pkg} MANQUANT")
            missing.append(pkg)
    n_img = len(list(IMAGES_DIR.glob("*.jpg")))
    print(f"  {'✓' if n_img >= 10 else '✗'} {n_img} images de test dans {IMAGES_DIR}")
    if missing:
        record("Environnement", False,
               f"dépendances manquantes : {', '.join(missing)} → pip install -r requirements.txt")
        return False
    if n_img < 10:
        record("Environnement", False, "images de test manquantes")
        return False
    record("Environnement", True, f"Python {py.major}.{py.minor}, deps OK, {n_img} images")
    return True


# ---------------------------------------------------------------- étape 1
def step1_fashion_embeddings():
    """FashionSigLIP : embeddings de style + sanity checks de similarité (F06/F07)."""
    print("\n" + "=" * 70)
    print("ÉTAPE 1 · Marqo-FashionSigLIP — embeddings de style (cœur du MVP)")
    print("=" * 70)
    try:
        import numpy as np
        import open_clip
        import torch

        t0 = time.perf_counter()
        model, _, preprocess = open_clip.create_model_and_transforms(
            "hf-hub:Marqo/marqo-fashionSigLIP")
        tokenizer = open_clip.get_tokenizer("hf-hub:Marqo/marqo-fashionSigLIP")
        model.eval()
        load_s = time.perf_counter() - t0
        print(f"Modèle chargé en {load_s:.1f}s (1er lancement = téléchargement ~1 Go)")

        images = load_images()
        names = list(images.keys())

        t0 = time.perf_counter()
        with torch.no_grad():
            batch = torch.stack([preprocess(img) for img in images.values()])
            feats = model.encode_image(batch)
            feats = feats / feats.norm(dim=-1, keepdim=True)
        per_img_ms = (time.perf_counter() - t0) / len(names) * 1000
        print(f"Encodage : {per_img_ms:.0f} ms/image sur CPU "
              f"(budget cahier des charges : ~100-300 ms → "
              f"{'OK' if per_img_ms < 500 else 'LENT'})")

        sim = (feats @ feats.T).numpy()
        idx = {n: i for i, n in enumerate(names)}

        passed = 0
        for a, close, far in SIMILARITY_CHECKS:
            s_close, s_far = sim[idx[a], idx[close]], sim[idx[a], idx[far]]
            ok = s_close > s_far
            passed += ok
            print(f"  {'✓' if ok else '✗'} sim({a},{close})={s_close:.3f} "
                  f"{'>' if ok else '<='} sim({a},{far})={s_far:.3f}")
        ok_sim = passed >= len(SIMILARITY_CHECKS) - 1  # tolère 1 échec
        record("Embeddings mode (similarité visuelle)", ok_sim,
               f"{passed}/{len(SIMILARITY_CHECKS)} sanity checks, {per_img_ms:.0f} ms/img CPU")

        # ------- retrieval texte -> image (utile pour alertes et debug)
        print("\nRetrieval texte → image :")
        with torch.no_grad():
            tokens = tokenizer([q for q, _ in TEXT_QUERIES])
            tfeats = model.encode_text(tokens)
            tfeats = tfeats / tfeats.norm(dim=-1, keepdim=True)
        scores = (tfeats @ feats.T).numpy()
        hits = 0
        for qi, (query, expected) in enumerate(TEXT_QUERIES):
            top1 = names[int(np.argmax(scores[qi]))]
            ok = top1 == expected
            hits += ok
            print(f"  {'✓' if ok else '✗'} « {query} » → {top1} (attendu : {expected})")
        record("Retrieval texte→image", hits >= len(TEXT_QUERIES) - 1,
               f"{hits}/{len(TEXT_QUERIES)} requêtes correctes en top-1")
        return feats, names
    except Exception as e:  # noqa: BLE001
        record("Embeddings mode", False, f"{type(e).__name__}: {e}")
        return None, None


# ---------------------------------------------------------------- étape 2
def step2_title_parsing():
    """GLiNER : extraction marque/modèle/taille depuis des titres d'annonces (ingestion + F19)."""
    print("\n" + "=" * 70)
    print("ÉTAPE 2 · GLiNER — parsing des titres d'annonces")
    print("=" * 70)
    try:
        from gliner import GLiNER

        t0 = time.perf_counter()
        model = GLiNER.from_pretrained("urchade/gliner_multi-v2.1")
        print(f"Modèle chargé en {time.perf_counter() - t0:.1f}s (~500 Mo au 1er lancement)")

        total_brands = 0
        t0 = time.perf_counter()
        for title in LISTING_TITLES:
            ents = model.predict_entities(title, PARSING_LABELS, threshold=0.35)
            found = {e["label"]: e["text"] for e in ents}
            has_brand = "marque" in found
            total_brands += has_brand
            print(f"  {'✓' if has_brand else '✗'} « {title} »")
            print(f"      → {found if found else 'rien extrait'}")
        per_title_ms = (time.perf_counter() - t0) / len(LISTING_TITLES) * 1000
        ok = total_brands >= 4  # marque détectée sur au moins 4/5 titres
        record("Parsing titres (GLiNER)", ok,
               f"marque extraite sur {total_brands}/{len(LISTING_TITLES)} titres, "
               f"{per_title_ms:.0f} ms/titre")
    except Exception as e:  # noqa: BLE001
        record("Parsing titres (GLiNER)", False, f"{type(e).__name__}: {e}")


# ---------------------------------------------------------------- étape 3
def step3_instance_matching():
    """DINOv2 : la même pièce sous un autre angle doit rester plus proche qu'une pièce
    du même style (fondement du matching « même pièce » de la V1.5)."""
    print("\n" + "=" * 70)
    print("ÉTAPE 3 · DINOv2 — matching d'instance (« la même pièce », V1.5)")
    print("=" * 70)
    try:
        import torch
        from PIL import ImageEnhance
        from transformers import AutoImageProcessor, AutoModel

        t0 = time.perf_counter()
        proc = AutoImageProcessor.from_pretrained("facebook/dinov2-base")
        model = AutoModel.from_pretrained("facebook/dinov2-base")
        model.eval()
        print(f"Modèle chargé en {time.perf_counter() - t0:.1f}s (~350 Mo au 1er lancement)")

        images = load_images()

        def embed(img):
            with torch.no_grad():
                out = model(**proc(images=img, return_tensors="pt"))
            v = out.last_hidden_state[:, 0]          # token CLS
            return (v / v.norm(dim=-1, keepdim=True))[0]

        # Simule « la même veste photographiée par un autre vendeur » :
        # recadrage + miroir + luminosité différente.
        jacket = images["jacket"]
        w, h = jacket.size
        variant = jacket.crop((int(w * .12), int(h * .08), int(w * .95), int(h * .97)))
        variant = variant.transpose(0)               # miroir horizontal
        variant = ImageEnhance.Brightness(variant).enhance(1.25)

        e_orig, e_var = embed(jacket), embed(variant)
        e_style = embed(images["man"])               # même style, autre pièce
        e_other = embed(images["sneaker"])           # rien à voir

        s_same = float(e_orig @ e_var)
        s_style = float(e_orig @ e_style)
        s_other = float(e_orig @ e_other)
        print(f"  même pièce (variante photo) : {s_same:.3f}")
        print(f"  même style (autre pièce)    : {s_style:.3f}")
        print(f"  pièce sans rapport          : {s_other:.3f}")
        ok = s_same > s_style > s_other
        margin = s_same - s_style
        record("Matching d'instance (DINOv2)", ok,
               f"même pièce {s_same:.3f} > même style {s_style:.3f} > autre {s_other:.3f} "
               f"(marge {margin:.3f} — seuil de confiance exploitable : {'oui' if margin > 0.05 else 'faible'})")
    except Exception as e:  # noqa: BLE001
        record("Matching d'instance (DINOv2)", False, f"{type(e).__name__}: {e}")


# ---------------------------------------------------------------- étape 4
def step4_segmentation():
    """SegFormer clothes : le vêtement est-il isolable du fond ? (qualité des cartes)."""
    print("\n" + "=" * 70)
    print("ÉTAPE 4 · SegFormer — segmentation vêtements (optionnel)")
    print("=" * 70)
    try:
        import torch
        from transformers import AutoModelForSemanticSegmentation, SegformerImageProcessor

        t0 = time.perf_counter()
        proc = SegformerImageProcessor.from_pretrained("mattmdjaga/segformer_b2_clothes")
        model = AutoModelForSemanticSegmentation.from_pretrained(
            "mattmdjaga/segformer_b2_clothes")
        model.eval()
        print(f"Modèle chargé en {time.perf_counter() - t0:.1f}s")

        images = load_images()
        img = images["man"]  # personne portant une veste
        with torch.no_grad():
            out = model(**proc(images=img, return_tensors="pt"))
        seg = out.logits.argmax(dim=1)[0]
        # classes vêtements du modèle (4=upper clothes, 6=pants, 7=dress, etc.)
        clothes_ratio = float((seg > 0).float().mean())
        upper_ratio = float((seg == 4).float().mean())
        print(f"  pixels non-fond : {clothes_ratio:.1%} · haut du corps détecté : {upper_ratio:.1%}")
        ok = upper_ratio > 0.02
        record("Segmentation vêtements", ok,
               f"vêtement haut détecté sur {upper_ratio:.1%} de l'image")
    except Exception as e:  # noqa: BLE001
        record("Segmentation vêtements", False, f"{type(e).__name__}: {e}")


# ---------------------------------------------------------------- rapport
def final_report():
    print("\n" + "=" * 70)
    print("RAPPORT FINAL — faisabilité de la stack IA SwipeWear")
    print("=" * 70)
    width = max(len(s) for s, _, _ in RESULTS) + 2
    for step, status, detail in RESULTS:
        icon = {"PASS": "✅", "FAIL": "❌", "SKIP": "⏭️ "}[status]
        print(f"{icon} {step:<{width}} {detail}")

    fails = [s for s, st, _ in RESULTS if st == "FAIL"]
    core_ok = all(st == "PASS" for s, st, _ in RESULTS
                  if s.startswith(("Environnement", "Embeddings", "Retrieval", "Parsing")))
    print("\n" + "-" * 70)
    if core_ok:
        print("VERDICT : 🟢 GO — la stack cœur du MVP (embeddings mode + parsing) est")
        print("validée sur de vraies photos. La brique IA n'est pas un risque.")
        print("Prochaine étape : Gate 1 (maquettes + TikTok), puis backend.")
    elif not fails:
        print("VERDICT : 🟡 Partiel — relance avec --all pour tout valider.")
    else:
        print(f"VERDICT : 🔴 À corriger — étapes en échec : {', '.join(fails)}.")
        print("Vérifie l'installation (requirements.txt) et la connexion (téléchargement HF).")
    print("-" * 70)
    return 0 if core_ok else 1


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--all", action="store_true",
                    help="inclut DINOv2 (même pièce) et SegFormer (segmentation)")
    args = ap.parse_args()

    print("\nSwipeWear · Test de faisabilité IA — " + time.strftime("%Y-%m-%d %H:%M"))
    print(f"Images de test : {IMAGES_DIR}\n")

    if not step0_environment():
        return final_report()

    step1_fashion_embeddings()
    step2_title_parsing()

    if args.all:
        step3_instance_matching()
        step4_segmentation()
    else:
        record_skip("Matching d'instance (DINOv2)", "lance avec --all")
        record_skip("Segmentation vêtements", "lance avec --all")

    return final_report()


if __name__ == "__main__":
    sys.exit(main())
