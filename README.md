# SwipeWear — AI Sniper de Pépites

> **Règle d'or : contracts first, connect intelligence second.**

Application mobile B2C de découverte de mode seconde main par swipe.
Le cerveau IA est modulaire, parallélisable, et 100 % CPU au MVP.

## Architecture

```
backend/
  contracts/          ← schémas Pydantic partagés (source de vérité des types)
  ingestion/          ← connecteurs eBay / Awin / CJ
  vision/             ← Qwen3-VL-2B-Instruct (analyse d'images d'inspiration)
  embeddings/         ← FashionSigLIP 768-dim (Marqo / OpenCLIP)
  preferences/        ← profil utilisateur vivant, reconstruit depuis l'event log
  retrieval/          ← ANN pgvector HNSW cosinus
  ranking/            ← score Python transparent (LightGBM gelé)
  policy/             ← MMR + epsilon-greedy + échelle de prix
  explainability/     ← tags éditables + phrase fondée sur le profil
  evaluation/         ← golden scenario (CI regression guard)
  orchestration/      ← séquenceur uniquement, zero logique métier
mobile/               ← React Native / Expo (ticket KAN-xx)
```

## Unités de déploiement

Les modules métier restent isolés dans le code, mais seuls les domaines ayant
un cycle de vie ou un profil de charge différent deviennent des conteneurs :

- `api` : requêtes synchrones et pipeline du feed ; seul service backend exposé.
- `ingestion-worker` : collecte et normalisation du catalogue (profil Compose
  `ingestion`).
- `ai-indexer` : embeddings CPU et index pgvector, avec une image contenant les
  dépendances IA (profil Compose `ai`).
- `alert-matcher`, `notification-dispatcher`, `daily-drop` : traitements
  périodiques indépendants.
- `migrations` : job idempotent terminé avant le démarrage des autres services.
- `db` : PostgreSQL + pgvector ; les conteneurs y accèdent seulement par le
  réseau de données (le port hôte reste publié pour le développement local).

Les workers communiquent par PostgreSQL. Cette frontière évite des appels HTTP
internes et permet de redémarrer ou dimensionner chaque unité séparément. Une
file de messages ne sera ajoutée que lorsqu'un besoin de traitement temps réel
ou de back-pressure sera mesuré.

```bash
# API et workers légers
docker compose up --build

# Ajouter l'ingestion ou l'indexation IA
docker compose --profile ingestion up --build
docker compose --profile ai up --build
```

## Règles d'architecture (blueprint §11)

1. **Contracts first** — modifier `contracts/interfaces.py` avant d'implémenter.
2. **Pas d'imports privés** — un module importe uniquement `autre_module.interfaces`.
3. **Pas de lecture DB cachée** — le ranker reçoit un profil complet en paramètre.
4. **Un seul orchestrateur** — `orchestration/` séquence, ne contient pas de logique.
5. **Tout output versionné** — schema_version + model + embedding_version + vector_dim.
6. **Event log = source de vérité** — le profil se reconstruit par replay d'événements.
7. **Chaque module a un fallback** — voir `CLAUDE.md §3` et `blueprint §12`.
8. **Le golden scenario protège tout** — ne jamais modifier `evaluation/fixtures/` pour passer un test.
9. **Budgets de latence** — total feed < 300 ms · embedding < 350 ms · GLiNER < 300 ms.

## Lancement rapide

```bash
cd backend
pip install -e ".[dev]"
python lint_imports.py   # vérifier les frontières d'imports
pytest                   # lancer les tests
```

## Gouvernance

Lire `CLAUDE.md` avant de coder. Il s'applique aux humains et aux agents IA.
Backlog : [Jira KAN](https://hamza-bouda.atlassian.net)
