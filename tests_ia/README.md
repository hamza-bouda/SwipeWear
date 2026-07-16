# 🧪 Tests de faisabilité IA — SwipeWear

Valide sur **de vraies photos** que chaque brique IA du MVP fonctionne, **avant d'écrire une ligne de backend**. Coût : ~30 min et ~2 Go de téléchargement de modèles (une seule fois, mis en cache par Hugging Face).

## Ce qui est testé

| Étape | Modèle | Fonctionnalité validée | Critère de succès |
|---|---|---|---|
| 1a | [Marqo-FashionSigLIP](https://huggingface.co/Marqo/marqo-fashionSigLIP) | Feed personnalisé + échelle "même style" (F06-F07) | Les paires visuellement proches (2 sneakers, 2 vestes) sont plus similaires que les intrus — et < 500 ms/image sur CPU |
| 1b | idem (tour texte) | Recherche/debug par texte | ≥ 5/6 requêtes texte retrouvent la bonne image en top-1 |
| 2 | [GLiNER](https://github.com/urchade/GLiNER) | Parsing des titres d'annonces (ingestion + F19) | Marque extraite sur ≥ 4/5 titres façon Vinted |
| 3 (`--all`) | [DINOv2](https://huggingface.co/facebook/dinov2-base) | Matching "la même pièce" (V1.5) | même pièce (photo modifiée) > même style > sans rapport, avec une marge exploitable |
| 4 (`--all`) | [SegFormer clothes](https://huggingface.co/mattmdjaga/segformer_b2_clothes) | Isolation du vêtement du fond (qualité des cartes) | Vêtement détecté sur une photo portée |

## Lancer

```bash
cd SwipeWear/tests_ia
python -m venv .venv
.venv\Scripts\activate          # Windows
pip install -r requirements.txt

python test_stack_ia.py          # étapes cœur (1-2)
python test_stack_ia.py --all    # tout (3-4 en plus)
```

## Lire le verdict

- 🟢 **GO** — la brique IA du MVP est validée : passez à la Gate 1 (maquettes + TikTok), le backend peut être construit sans risque IA.
- 🔴 **À corriger** — en général : dépendance manquante (`pip install -r requirements.txt`) ou premier téléchargement Hugging Face interrompu (relancer).

## Notes

- **Tout tourne sur CPU** — c'est volontaire : le cahier des charges (doc 04) interdit le GPU au MVP.
- Les photos de `images/` sont des photos Unsplash libres de droits (les mêmes que le prototype Figma/web).
- Étape suivante logique après un GO : refaire tourner l'étape 1 sur **50 vraies photos d'annonces Vinted/eBay** (photos amateur, fonds encombrés) pour confirmer en conditions réelles.
- Ces tests valident **l'existence et la faisabilité**, pas la qualité produit finale — celle-ci se mesure à la Gate 2 (beta).
