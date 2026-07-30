# 14 — Authentification via Firebase (KAN-91)

## Pourquoi

L'authentification maison a été retirée. Deux raisons, la seconde décisive :

1. Tenir soi-même des mots de passe, des réinitialisations, des confirmations d'email et les échanges OAuth avec Google est un métier à part entière, pour une équipe de deux.
2. **Le modèle précédent contenait une prise de contrôle de compte.** `POST /auth/token` signait n'importe quel `user_id` fourni dans le corps de la requête, sans aucune preuve d'identité. Vérifié par exécution contre l'API réelle : avec le seul identifiant d'une victime, on obtenait un jeton valide, puis on lisait son profil, le modifiait, et supprimait son compte. Le contrôle du mot de passe dans `/auth/login` était entièrement contournable.

Firebase possède désormais les identifiants. Le backend ne stocke aucun mot de passe : il vérifie le jeton signé par Google et provisionne le compte local derrière.

**Ce qui ne change pas** : le catalogue, les 50 927 embeddings, l'index HNSW et tout le pipeline de recommandation restent sur PostgreSQL + pgvector. Firestore n'est pas utilisé. Firebase ne fournit que l'identité — la couche la plus facile à remplacer, alors que les données vectorielles, elles, ne se déplacent pas.

## Les deux identités

| Identité | Émise par | Sert à | Endpoint |
|---|---|---|---|
| **Navigation anonyme** | Notre API (HS256, `JWT_SECRET`) | Personnaliser le feed avant l'inscription | `POST /auth/anonymous` — **le serveur génère l'identifiant** |
| **Compte** | Firebase (RS256, clés publiques Google) | Tout ce qui est rattaché à une personne | Émis par Firebase, synchronisé par `POST /auth/sync` |

`require_account` refuse un jeton anonyme sur les opérations qui n'ont de sens que pour un vrai compte — la suppression, par exemple.

> **Conséquence à connaître :** `POST /auth/anonymous` crée toujours une identité neuve — c'est précisément ce qui referme la faille. L'application persiste donc le jeton anonyme. S'il expire (30 jours) sans que la personne se soit inscrite, elle repart d'un profil vierge. Créer un compte est le chemin durable.

## Les identifiants Firebase ne sont pas des UUID

C'est le point d'architecture le plus important de ce changement.

Le claim `sub` d'un jeton Firebase est une chaîne opaque de 28 caractères. Or `user_id` est de type **UUID dans dix colonnes** de la base et dans **quatre modèles de `contracts/`** — une zone protégée qui ne se modifie pas sans l'accord des deux lanes (CLAUDE.md §4 et §8).

Plutôt que de migrer tout cela, `user_id` est dérivé par **UUIDv5** :

```python
uuid.uuid5(uuid.NAMESPACE_URL, f"https://securetoken.google.com/{project_id}/{firebase_uid}")
```

- **Déterministe** : la même personne retombe toujours sur la même ligne, sans table de correspondance qui pourrait se désynchroniser.
- **Cloisonné par projet** : deux projets Firebase ne peuvent pas faire pointer le même uid sur la même ligne.
- **À sens unique** : d'où la colonne `users.provider_uid`, qui conserve l'identifiant d'origine — la suppression du compte chez Firebase en a besoin.

Quatre tests fixent ces propriétés, dont un qui compare à un UUIDv5 calculé à la main : changer l'algorithme orphelinerait tous les comptes existants, et le test le ferait échouer.

## Mise en service

Ces étapes demandent la console Firebase : elles sont à réaliser par toi, pas par un agent.

### 1. Initialiser Authentication

Console Firebase → **Authentication** → **Get started**.

Tant que ce n'est pas fait, l'API Identity Toolkit répond `CONFIGURATION_NOT_FOUND` à toute tentative de connexion.

### 2. Activer les fournisseurs

Authentication → **Sign-in method** :

| Fournisseur | À faire | État |
|---|---|---|
| **Email/Password** | Activer | Fonctionne dans Expo Go |
| **Google** | Activer — Firebase crée l'identifiant client OAuth tout seul, sans passer par Google Cloud Console | Fonctionne dans Expo Go |
| **Phone** | Activer | **Demande un development build**, voir plus bas |

Après avoir activé Google, copie l'**identifiant client Web** (Authentication → Sign-in method → Google → Configuration du SDK Web) dans `mobile/.env` :

```
EXPO_PUBLIC_GOOGLE_WEB_CLIENT_ID=…
```

Tant qu'il est vide, le bouton Google reste désactivé et l'écran l'explique, au lieu d'échouer avec un message anglais.

### 3. Compte de service (suppression de compte)

Paramètres du projet → **Comptes de service** → *Générer une nouvelle clé privée*. Puis, dans le `.env` racine, le JSON sur une ligne :

```
FIREBASE_SERVICE_ACCOUNT_JSON={"type":"service_account",…}
```

ou un chemin de fichier dans `GOOGLE_APPLICATION_CREDENTIALS`.

> Cette clé contourne toutes les règles d'accès. Elle ne doit **jamais** apparaître dans une variable `EXPO_PUBLIC_` ni dans le bundle mobile. Le script de contrôle refuse ce cas.

### 4. Appliquer la migration

```bash
python backend/scripts/run_migrations.py
```

`018_users_firebase.sql` ajoute `provider_uid` et `phone_number`.

### 5. Vérifier — par exécution, pas de confiance

```bash
python backend/scripts/check_firebase.py
```

Le script interroge réellement Google : il récupère les clés de signature, teste le compte de service contre l'API admin, compare le projet visé par l'app à celui visé par le backend (viser deux projets différents ferait rejeter chaque jeton par l'audience), et refuse toute clé privée trouvée dans une variable `EXPO_PUBLIC_`.

Aucune clé n'est affichée. Le code de sortie est 1 tant qu'un point reste à corriger.

## L'authentification par téléphone

Elle n'est **pas** livrée, et c'est une limite technique, pas un oubli.

Firebase exige un reCAPTCHA avant d'envoyer un SMS. Avec le SDK JavaScript en React Native, cela passe par `expo-firebase-recaptcha`, bloqué en version 2.3.1 — une version de l'époque d'Expo 45, incompatible en pratique avec Expo 57.

Le chemin fiable est `@react-native-firebase/auth`, un module natif. Il impose un **development build** : plus de test dans Expo Go, et chaque build passe par EAS (une dizaine de minutes). C'est un changement de méthode de travail, pas seulement une dépendance de plus — d'où la décision laissée ouverte.

Email et Google fonctionnent dans Expo Go dès aujourd'hui.

## Sans configuration

L'application reste utilisable : la navigation fonctionne sous identité anonyme, et l'écran de connexion affiche « La connexion n'est pas configurée sur cet appareil » avec les champs désactivés. Côté API, `POST /auth/sync` répond **503 `AUTH_PROVIDER_UNCONFIGURED`** — il n'y a pas de repli silencieux vers une authentification plus faible.

## Ce qui est vérifié

`backend/api/tests/test_auth.py` signe des jetons avec une paire de clés générée dans le test, ce qui exerce le vrai chemin de vérification sans projet Firebase actif :

- jeton valide accepté, claims (`sub`, email, téléphone, fournisseur) correctement extraits ;
- compte téléphone sans aucune adresse email ;
- jeton expiré → 401 `TOKEN_EXPIRED` ;
- jeton signé par une autre clé → 401 ;
- **jeton d'un autre projet Firebase → 401** — Google signe tous les projets avec les mêmes clés, donc sans contrôle d'audience, le jeton de n'importe quelle autre application authentifierait ici, avec une signature parfaitement valide ;
- mauvais émetteur → 401 ;
- **confusion d'algorithme** : jeton re-signé en HS256 avec la clé *publique* comme secret HMAC → 401. Le jeton est assemblé à la main dans le test, car PyJWT refuse de le produire ; un attaquant, lui, écrit les octets directement ;
- dérivation UUIDv5 : déterminisme, unicité, cloisonnement par projet, et comparaison à une valeur calculée à la main.

## Suppression de compte (RGPD)

`DELETE /auth/account` supprime l'identité chez Firebase (API Identity Toolkit, authentifiée par le compte de service) **puis** les lignes locales. Si Firebase est injoignable, l'endpoint répond **502 et ne supprime rien** : effacer nos lignes en laissant l'identité vivante permettrait à la personne de se reconnecter et d'être re-provisionnée aussitôt — sous un bouton qui promet une suppression définitive.

`google-auth` étant déjà une dépendance, le jeton d'accès est forgé à partir du compte de service sans embarquer tout le SDK `firebase-admin` pour un seul appel.
