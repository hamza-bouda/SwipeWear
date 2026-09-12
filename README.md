# SwipeWear — AI Sniper de Pépites

> **Règle d'or : contracts first, connect intelligence second.**

Application mobile B2C de découverte de mode seconde main par swipe.
Le cerveau IA est modulaire, parallélisable, et 100 % CPU au MVP.

> État actuel : l'application mobile est migrée vers Flutter/Dart. Le code
> React Native/Expo historique a été supprimé du répertoire `mobile/`.

## Démarrage en 5 minutes

Prérequis détaillés : [REQUIREMENTS.md](REQUIREMENTS.md).

```bash
git clone https://github.com/hamza-bouda/SwipeWear.git
cd SwipeWear
cp .env.example .env
docker compose up --build
```

Dans un second terminal :

```bash
cd mobile
flutter pub get
flutter run --dart-define=API_BASE_URL=http://10.0.2.2:8000
```

Sous Windows PowerShell, remplacer `cp .env.example .env` par
`Copy-Item .env.example .env`. Pour un simulateur iOS, utiliser
`http://localhost:8000` comme adresse de l'API.

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
mobile/               ← Flutter / Dart (Android + iOS)
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
docker compose --profile watcher up --build
```

Le profil `watcher` surveille les alertes via les APIs officielles eBay/Etsy/Awin
et réutilise le pipeline de normalisation et de matching. Le prototype Vinted
reste isolé, désactivé et soumis à validation juridique.

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

Pour lancer l’application mobile Flutter :

```bash
cd mobile
flutter pub get
flutter run --dart-define=API_BASE_URL=http://10.0.2.2:8000
```

Les livrables Android et iOS se construisent avec `flutter build appbundle`
et `flutter build ipa`. Les identifiants Firebase, Google Sign-In et
RevenueCat restent injectés par environnement ; aucun secret mobile n’est
stocké dans le dépôt.

## Validation

```bash
cd backend
python -m pip install -e ".[dev]"
pytest

cd ../mobile
flutter analyze --no-pub
flutter test --no-pub
flutter build apk --debug --no-pub
```

Le détail des variables, des émulateurs, des builds signés et des prérequis
de production se trouve dans [REQUIREMENTS.md](REQUIREMENTS.md) et
[mobile/README.md](mobile/README.md).

## Gouvernance

Lire `CLAUDE.md` avant de coder. Il s'applique aux humains et aux agents IA.
Backlog : [Jira KAN](https://hamza-bouda.atlassian.net)
