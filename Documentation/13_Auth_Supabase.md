# 13 — Authentification via Supabase (KAN-90)

## Pourquoi

L'authentification maison a été retirée. Deux raisons, la seconde décisive :

1. Tenir soi-même des mots de passe, des réinitialisations, des confirmations d'email et les échanges OAuth avec Google et Apple est un métier à part entière, pour une équipe de deux.
2. **Le modèle précédent contenait une prise de contrôle de compte.** `POST /auth/token` signait n'importe quel `user_id` fourni dans le corps de la requête, sans aucune preuve d'identité. Vérifié par exécution contre l'API réelle : avec le seul identifiant d'une victime, on obtenait un jeton valide, puis on lisait son profil, le modifiait, et supprimait son compte. Le contrôle du mot de passe dans `/auth/login` était entièrement contournable.

Supabase possède désormais les identifiants. Le backend ne stocke aucun mot de passe : il vérifie le jeton signé par Supabase et provisionne le compte local derrière.

## Les deux identités

| Identité | Émise par | Sert à | Endpoint |
|---|---|---|---|
| **Navigation anonyme** | Notre API (HS256, `JWT_SECRET`) | Personnaliser le feed avant l'inscription | `POST /auth/anonymous` — **le serveur génère l'identifiant** |
| **Compte** | Supabase (RS256/ES256 via JWKS) | Tout ce qui est rattaché à une personne | Émis par Supabase, synchronisé par `POST /auth/sync` |

`require_account` refuse un jeton anonyme sur les opérations qui n'ont de sens que pour un vrai compte — la suppression, par exemple.

> **Conséquence à connaître :** `POST /auth/anonymous` crée toujours une identité neuve — c'est précisément ce qui referme la faille. L'application persiste donc le jeton anonyme. S'il expire (30 jours) sans que la personne se soit inscrite, elle repart d'un profil vierge. Créer un compte est le chemin durable.

## Mise en service (à faire une fois)

Ces étapes demandent un compte Supabase : elles sont à réaliser par toi, pas par un agent.

### 1. Créer le projet

1. https://supabase.com → **New project**. Région : **Central EU (Frankfurt)** — les emails sont des données personnelles, autant les garder dans l'UE.
2. Dans **Security**, décoche **Enable Data API** et **Automatically expose new tables**, coche **Enable automatic RLS**. L'avertissement « client libraries can't query your database » ne nous concerne pas : `supabase-js` n'est utilisé que pour `.auth.*`, servi par GoTrue sur `/auth/v1`, indépendant de PostgREST. Aucun `.from()`, `.rpc()`, `.storage` ni `.channel()` dans le code. Désactiver la Data API empêche la clé publique, embarquée dans l'app, d'interroger la moindre table.
3. Project Settings → **API Keys**, onglet « Publishable and secret API keys » :
   - **Publishable key** (`sb_publishable_…`) → pour l'app. Remplace l'ancienne clé `anon`.
   - **Secret key** (`sb_secret_…`) → pour le backend uniquement. Remplace `service_role`.

   L'onglet « Legacy anon, service_role API keys » reste disponible ; les deux formats fonctionnent. `supabase-js` 2.111 accepte le nouveau.

### 2. Activer les fournisseurs

Authentication → Providers :

| Fournisseur | À faire |
|---|---|
| **Email** | Activé par défaut. Laisse « Confirm email » activé : l'app gère le cas et affiche « Confirme ton email ». |
| **Google** | Créer un OAuth client dans Google Cloud Console, coller Client ID et Secret. |
| **Apple** | Nécessite un compte Apple Developer payant (99 $/an). Obligatoire pour publier sur l'App Store si un autre fournisseur social est proposé. |

### 3. Déclarer les URL de redirection

Authentication → URL Configuration → **Redirect URLs**, ajouter :

```
swipewear://auth
http://localhost:8081
```

Le schéma `swipewear` est déclaré dans `mobile/app.json`. Sans ces entrées, Supabase refuse la redirection après un login Google ou Apple.

### 4. Renseigner les variables

`.env` à la racine (backend) :

```
SUPABASE_URL=https://<ref>.supabase.co
SUPABASE_SERVICE_ROLE_KEY=<service_role>
SUPABASE_JWT_SECRET=
```

`SUPABASE_JWT_SECRET` ne sert qu'aux projets restés sur l'ancien secret HS256 partagé. Un projet récent utilise des clés asymétriques, vérifiées via le JWKS public — laisse la variable vide.

`mobile/.env` :

```
EXPO_PUBLIC_SUPABASE_URL=https://<ref>.supabase.co
EXPO_PUBLIC_SUPABASE_ANON_KEY=<anon public>
```

> La clé **anon** est publique par conception : elle identifie le projet et n'autorise rien par elle-même. La clé **service_role** contourne toutes les règles d'accès — elle ne doit jamais apparaître dans une variable `EXPO_PUBLIC_`, ni dans le bundle mobile.

### 5. Appliquer la migration

```bash
python backend/scripts/run_migrations.py
```

`017_users_external_auth.sql` rend `password_hash` et `email` nullables et ajoute `auth_provider`.

### 6. Vérifier — par exécution, pas de confiance

```bash
python backend/scripts/check_supabase.py
```

Le script interroge réellement le projet : il récupère le JWKS et affiche les algorithmes de signature, teste la clé `service_role` contre l'API admin, et compare le projet visé par l'app à celui visé par le backend (viser deux projets différents ferait rejeter chaque jeton par l'émetteur). Il refuse aussi toute variable `EXPO_PUBLIC_` contenant une clé `service_role`, qui serait une fuite totale.

Aucune clé n'est affichée. Le code de sortie est 1 tant qu'un point reste à corriger.

## Sans configuration

L'application reste utilisable : la navigation fonctionne sous identité anonyme, et l'écran de connexion affiche « La connexion n'est pas configurée sur cet appareil » avec les champs désactivés. Côté API, `POST /auth/sync` répond **503 `AUTH_PROVIDER_UNCONFIGURED`** — il n'y a pas de repli silencieux vers une authentification plus faible.

## Ce qui est vérifié

`backend/api/tests/test_auth.py` signe des jetons avec une paire de clés générée dans le test, ce qui exerce le vrai chemin de vérification sans projet Supabase actif :

- jeton valide accepté, claims (`sub`, email, fournisseur) correctement extraits ;
- jeton expiré → 401 `TOKEN_EXPIRED` ;
- jeton signé par une autre clé → 401 ;
- mauvaise audience (`anon`, service role) → 401 — sans quoi la clé anon, embarquée dans l'app, authentifierait une personne ;
- mauvais émetteur → 401 ;
- **confusion d'algorithme** : jeton re-signé en HS256 avec la clé *publique* comme secret HMAC → 401. Le jeton est assemblé à la main dans le test, car PyJWT refuse de le produire ; un attaquant, lui, écrit les octets directement.

## Suppression de compte (RGPD)

`DELETE /auth/account` supprime l'identité chez Supabase (API admin) **puis** les lignes locales. Si Supabase est injoignable, l'endpoint répond **502 et ne supprime rien** : effacer nos lignes en laissant l'identité vivante permettrait à la personne de se reconnecter et d'être re-provisionnée aussitôt — sous un bouton qui promet une suppression définitive.
