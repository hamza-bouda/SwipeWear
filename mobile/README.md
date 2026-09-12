# SwipeWear mobile

SwipeWear mobile is a Flutter/Dart application for Android and iOS. Flutter is
the only UI/runtime layer in this directory; the old React Native/Expo app has
been removed.

## Architecture

- `lib/core` — API client, secure session storage, FR/EN localization, offline cache and design system.
- `lib/features/auth` — anonymous session, registration and login.
- `lib/features/onboarding` — gender, styles, sizes, budget and inspiration photos.
- `lib/features/feed` — personalised swipe deck, detail view and events.
- `lib/features/ladder` — price comparison, partner links and alerts.
- `lib/features/drop` — daily 15-item selection.
- `lib/features/alerts` — alert creation, pause/resume and deletion.
- `lib/features/dressing` — persistent saves with category and price filters.
- `lib/features/profile` — algorithm controls, notifications and RGPD deletion.
- `lib/features/billing` — Gold status and RevenueCat purchase/restore flow.
- `lib/core/analytics` — best-effort product metrics for swipes, alerts, Drop,
  paywall and share cards.

## Run locally

```bash
flutter pub get
flutter run --dart-define=API_BASE_URL=http://10.0.2.2:8000
```

Use `http://localhost:8000` for an iOS simulator. The app creates and stores
an anonymous backend session, then consumes the existing `/feed` and `/events`
API contracts.

## Release

```bash
flutter build appbundle --release --dart-define=API_BASE_URL=https://your-api.example.com
flutter build ipa --release --dart-define=API_BASE_URL=https://your-api.example.com
```

Pour signer Android en production, renseigner dans l’environnement de
construction `SWIPEWEAR_KEYSTORE_FILE`, `SWIPEWEAR_KEYSTORE_PASSWORD`,
`SWIPEWEAR_KEY_ALIAS` et `SWIPEWEAR_KEY_PASSWORD`. Sans ces variables, le
fallback debug permet uniquement de générer des previews locales.

For Gold purchases, provide `REVENUECAT_IOS_KEY` and
`REVENUECAT_ANDROID_KEY` as `--dart-define` values and configure the matching
entitlement `swipewear_premium_monthly` in RevenueCat.

Google sign-in uses the existing `POST /auth/google` endpoint. Pass the public
OAuth client IDs at build time with `GOOGLE_SERVER_CLIENT_ID` and
`GOOGLE_IOS_CLIENT_ID`, and configure the same server client ID as
`GOOGLE_OAUTH_CLIENT_ID` on the backend. The anonymous profile is migrated when
the user creates or joins an account.

For native push, configure Firebase for both targets with FlutterFire, add the
generated `GoogleService-Info.plist` and `google-services.json`, then provide
the Firebase service-account JSON through `FIREBASE_SERVICE_ACCOUNT_JSON` and
its project id through `FCM_PROJECT_ID` on the API and notification worker.
The backend uses FCM HTTP v1 for Flutter tokens and still accepts old Expo
tokens during the migration.

The app starts in French and lets the user switch to English from Profile >
Language. The selected language is persisted in secure storage. When the API
is temporarily unavailable, the feed, Drop, alerts and wardrobe can show the
last real server response cached for the current user; the UI labels this mode
as offline and never creates production placeholder products.
Account erasure also removes the account-scoped feed, alerts, saves and Drop
cache from secure storage before the local session is discarded.

## Catalogue watcher

The production-safe equivalent of the isolated Vinted prototype is the
`official-watcher` Compose profile. It watches active alert labels through
official eBay Browse, Etsy Open API and/or Awin Product Data connectors, then
reuses the normalisation, pgvector indexing and alert-matching pipeline:

```bash
OFFICIAL_WATCHER_SOURCES=ebay docker compose --profile watcher up --build
```

Credentials are read only from deployment environment variables. The worker
rejects `vinted` explicitly; the legacy `watcher/vinted_watcher.py` stays
disabled behind its database kill switch until legal review is complete.

Backend recommendation logic, database access, secrets, alert matching and
notification scheduling stay on the server.
