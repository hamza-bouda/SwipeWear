# Prérequis de démarrage SwipeWear

Ce document décrit l'environnement minimal pour lancer SwipeWear en local.

## Outils requis

### Backend

- Docker Desktop avec Docker Compose v2
- Python 3.11 ou plus récent
- Git
- Un compte eBay Developer pour le catalogue réel (optionnel pour lancer les tests)

### Application mobile Flutter

- Flutter 3.32.x ou version compatible avec Dart 3.8
- Android Studio avec Android SDK, Platform Tools et un émulateur Android
- Android API 35 ou plus récent recommandé
- Pour iOS : macOS, Xcode et CocoaPods
- Aucun environnement React Native, Expo ou Node.js n'est requis pour l'application mobile actuelle

## Démarrage du backend

Depuis la racine du dépôt :

```bash
cp .env.example .env
docker compose up --build
```

Sous Windows PowerShell :

```powershell
Copy-Item .env.example .env
docker compose up --build
```

L'API est ensuite disponible sur `http://localhost:8000`.

Pour installer les dépendances Python et lancer la suite de tests sans Docker :

```bash
cd backend
python -m venv .venv
source .venv/bin/activate       # macOS/Linux
# .venv\Scripts\Activate.ps1   # Windows PowerShell
python -m pip install -e ".[dev]"
pytest
```

Les secrets réels restent dans `.env` ou dans le gestionnaire de secrets du
déploiement. Le fichier `.env` ne doit jamais être commité.

## Démarrage de l'application mobile

```bash
cd mobile
flutter pub get
flutter devices
flutter run --dart-define=API_BASE_URL=http://10.0.2.2:8000
```

Adresses de l'API selon la cible :

| Cible | `API_BASE_URL` |
| --- | --- |
| Émulateur Android | `http://10.0.2.2:8000` |
| Appareil Android réel | `http://<IP-DE-L-ORDINATEUR>:8000` |
| Simulateur iOS | `http://localhost:8000` |
| Staging/production | URL HTTPS publique de l'API |

L'application mobile est entièrement en Flutter/Dart. Elle utilise les
contrats backend existants et ne crée pas de produits fictifs lorsque l'API
est indisponible.

## Configuration mobile facultative

Les valeurs sensibles et les identifiants de services sont injectés au build,
jamais écrits en dur dans le dépôt :

```bash
flutter run \
  --dart-define=API_BASE_URL=http://10.0.2.2:8000 \
  --dart-define=GOOGLE_SERVER_CLIENT_ID=... \
  --dart-define=GOOGLE_IOS_CLIENT_ID=... \
  --dart-define=REVENUECAT_ANDROID_KEY=... \
  --dart-define=REVENUECAT_IOS_KEY=...
```

Pour les notifications push, ajouter les fichiers Firebase générés par
FlutterFire dans les projets Android et iOS, puis configurer les variables
Firebase côté backend. Ces fichiers et clés ne doivent pas être versionnés.

## Vérifications locales

```bash
cd mobile
flutter analyze --no-pub
flutter test --no-pub
flutter build apk --debug --no-pub
```

Builds de distribution :

```bash
flutter build appbundle --release --dart-define=API_BASE_URL=https://api.example.com
flutter build ipa --release --dart-define=API_BASE_URL=https://api.example.com
```

La signature Android/iOS, Firebase, Google Sign-In, RevenueCat, les comptes
affiliés et les variables de production doivent être configurés avant une
publication dans Google Play ou l'App Store.

## Catalogue et watcher

Le watcher de production utilise uniquement les connecteurs officiels eBay,
Etsy et/ou Awin :

```bash
OFFICIAL_WATCHER_SOURCES=ebay docker compose --profile watcher up --build
```

Le prototype Vinted reste désactivé jusqu'à validation juridique et ne fait
pas partie du chemin de production.
