# CLAUDE.md — Règles pour les agents IA sur SwipeWear

> Ce fichier est lu automatiquement par les agents IA (Claude Code, etc.) au début de chaque session.
> **À copier à la racine du repo de code dès sa création (ticket KAN-15).**
> Il s'applique aussi aux humains : ce sont les règles de travail du projet.

---

## 1. Sources de vérité — dans cet ordre

Avant d'écrire du code ou de répondre, l'agent DOIT s'appuyer sur ces sources, jamais sur sa mémoire :

1. **Les contrats du code** (`contracts/`) — si un schéma existe dans le code, c'est LUI qui fait foi, pas la documentation.
2. **Jira** (projet KAN, https://hamza-bouda.atlassian.net) — l'état du travail : quoi faire, dans quel ordre, qui fait quoi. Le backlog Jira prime sur le fichier `Backlog/PRODUCT_BACKLOG.md` (qui est un miroir).
3. **Le blueprint** — `SwipeWear_AI_Brain_Professional_Blueprint_v3.pdf` : l'architecture du cerveau IA (modules, contrats, fallbacks, règles anti-spaghetti).
4. **La documentation** (`Documentation/01-09_*.md`) — la vision produit, le marché, les gates, les risques.

**Règle anti-hallucination n°1 : si une information n'est dans aucune de ces sources, l'agent le DIT et pose la question. Il n'invente jamais** un champ de schéma, un seuil, un endpoint, un nom de module ou une décision produit.

---

## 2. Décisions déjà prises — NE PAS remettre en question sans ticket

Ces décisions sont validées (tests IA GO 6/6 du 2026-07-16, blueprint §13). Un agent ne les change pas de sa propre initiative ; s'il pense qu'il faut changer, il crée un ticket dans l'epic E14 (Icebox) et le signale.

| Sujet | Décision figée |
|---|---|
| Embeddings mode | Marqo-FashionSigLIP (OpenCLIP), vecteurs **768** (corrigé le 2026-07-22, KAN-77 — l'ancienne valeur 512 n'avait jamais été vérifiée contre une exécution réelle du modèle), L2-normalisés, version `fashionsiglip-v1` |
| Analyse de scènes | Qwen3-VL-2B-Instruct quantisé, derrière l'adapter `SceneAnalyzer` — soumis au bench KAN-30 |
| Matching "même pièce" | DINOv2 base, seuil ~0.80 (marge validée : 0.956 vs 0.508 vs 0.074) |
| Parsing titres | GLiNER, labels : marque / modèle / taille / couleur / état |
| Base de données | PostgreSQL + pgvector (index HNSW, distance cosinus) |
| Backend | FastAPI + Pydantic. Frontend : React Native / Expo |
| Inférence | CPU uniquement au MVP — aucun code qui exige un GPU |
| Ranking | Score Python transparent d'abord ; LightGBM SEULEMENT après de vraies données (gelé) |
| Diversité | MMR + epsilon-greedy ; bandits contextuels gelés (E14) |
| Tracking d'expériences | Git + JSON/CSV ; MLflow gelé (E14) |
| Sources produits | eBay Browse API (occasion) + Awin ou CJ (neuf). Vinted = watcher isolé, gelé, kill-switch obligatoire |
| Monétisation | Affiliation (EPN, Awin/CJ) + Premium 4,99 €/mois = priorité d'alertes |
| Gates business | Gate 1 : 300 waitlist ET 50K vues → débloque E6-E9. Gate 2 : ≥30 % beta créent ≥2 alertes → débloque E12-E13 |

---

## 3. Règles d'architecture — NON NÉGOCIABLES (blueprint §11)

Toute PR qui viole une de ces règles est refusée, qu'elle vienne d'un humain ou d'un agent.

1. **Contracts first.** On définit ou modifie le schéma dans `contracts/` AVANT d'implémenter. Tout changement de contrat = une ligne dans `CHANGELOG_contracts.md` + incrément de `schema_version` si cassant.
2. **Pas d'imports privés.** Un module importe les `interfaces.py` et les `contracts/` d'un autre module — JAMAIS ses fichiers internes. Structure : `contracts/ ingestion/ vision/ embeddings/ preferences/ retrieval/ ranking/ policy/ explainability/ evaluation/ orchestration/`.
3. **Pas de lecture DB cachée.** Le ranker (et tout module de calcul) reçoit un profil complet et un CandidateSet complet en paramètres. Il ne fait aucune requête lui-même.
4. **Un seul orchestrateur.** `orchestration/` séquence les appels et ne contient AUCUNE logique métier, modèle ou ranking.
5. **Tout output est versionné.** Chaque embedding, profil, rapport porte : schema_version, model, embedding_version, vector_dim.
6. **L'event log est la source de vérité.** Toute modification du profil passe par un `InteractionEvent`. Jamais d'écriture directe du profil qui contournerait l'event log.
7. **Chaque module a un fallback** (blueprint §12) : Qwen KO → embedding seul + confirmation tags ; retriever KO → produits récents filtrés ; ranker KO → tri par similarité ; policy KO → liste brute ; explainer KO → tags éditables. Un nouvel appel modèle sans fallback = PR refusée.
8. **Le golden scenario protège tout.** Ne JAMAIS modifier les fixtures (`evaluation/fixtures/`) pour faire passer un test. Si le golden échoue, c'est le code qu'on corrige — ou une discussion d'équipe si le nouveau comportement est voulu.
9. **Budgets de latence** (cibles CPU) : hard_filter 20 ms · retrieve 100 ms · rank 50 ms · diversify 30 ms · explain 30 ms · total feed 300 ms · embedding image < 350 ms · GLiNER < 300 ms/titre · échelle de prix < 800 ms.
10. **Tout changement de schéma Postgres est journalisé.** Toute nouvelle migration dans `backend/migrations/` (nouvelle table, colonne, index, contrainte) doit être ajoutée au **Journal des migrations** (section 9 de ce fichier), pas seulement décrite dans le message de commit — c'est ce qui permet à un agent démarrant sur une autre machine de connaître l'état réel de la base sans avoir à relire tous les fichiers `.sql`.

---

## 4. Travail en parallèle sans conflit — les lanes

Deux lanes indépendantes (blueprint §10). Chaque ticket Jira porte son label de lane.

| Lane | Label Jira | Modules possédés |
|---|---|---|
| **Product Intelligence** | `PI` | `ingestion/`, `vision/`, `embeddings/`, `retrieval/` |
| **Personnalisation** | `PERSO` | `preferences/`, `ranking/`, `policy/`, `explainability/` |
| **Commun** | `COMMUN` | `contracts/`, `orchestration/`, `evaluation/`, API, app mobile, infra |

Règles de non-conflit :
- Un agent (ou un dev) travaille dans les modules de SA lane. Il ne modifie pas les modules de l'autre lane.
- **`contracts/` est une zone protégée** : toute modification exige l'accord des deux lanes (mention explicite dans la PR + review de l'autre personne). C'est le seul point de couplage autorisé — c'est pour ça qu'on le protège.
- Besoin d'un changement dans l'autre lane ? On crée un ticket Jira (ou un commentaire sur le ticket concerné), on ne modifie pas soi-même.
- Les deux lanes développent contre les **mêmes fixtures** (`evaluation/fixtures/`) — c'est ce qui garantit que l'assemblage fonctionne.

---

## 5. Workflow Git + Jira

- **Une branche par ticket** : `KAN-<num>-description-courte` (ex. `KAN-23-connector-ebay`). Jamais de commit direct sur `main`.
- **Messages de commit** : commencer par la clé Jira — `KAN-23: connector eBay avec rate limiting`. Pas de co-auteur IA dans les commits.
- **Une PR = un ticket.** Petites PRs (< ~400 lignes d'écart idéalement). La PR référence le ticket, la CI (lint + tests + golden scenario) doit être verte avant merge.
- **Review croisée** : le code d'une lane est relu par l'autre personne quand il touche `contracts/` ou l'orchestrateur ; sinon self-merge autorisé si la CI est verte (équipe de 2, on reste pragmatique).
- **Cycle de vie Jira** : prendre le ticket (s'assigner) → `En cours` → PR ouverte (lier la PR) → mergé → `Terminé`. Un agent qui commence un travail met le ticket `En cours` ; s'il découvre du travail hors périmètre, il crée un NOUVEAU ticket au lieu de gonfler le sien.
- **Rebase plutôt que merge** depuis `main` pour garder un historique lisible.

## 6. Definition of Done d'un ticket

Un ticket n'est `Terminé` que si :

1. Tous les critères d'acceptation du ticket sont cochés.
2. Les tests du module passent + le golden scenario passe.
3. Le lint passe (y compris la règle anti-imports privés).
4. Les contrats modifiés sont documentés dans `CHANGELOG_contracts.md`.
5. Le budget de latence du module est respecté (vérifié dans la trace).
6. Aucun secret en dur (les clés vont dans `.env`, jamais dans le code ni les commits).

## 7. Règles spécifiques aux agents IA

- **Toujours lire le ticket Jira avant de coder.** Les critères d'acceptation sont le cahier des charges — pas d'ajout de features non demandées.
- **Ne jamais inventer un état d'avancement.** Pour savoir si un module existe, lire le code ; pour savoir si un ticket est fait, lire Jira. Ne pas supposer.
- **En cas de contradiction entre sources** (ex. la doc dit X, le code dit Y) : le code fait foi, ET l'agent signale la contradiction pour que la doc soit corrigée.
- **Marquer l'incertitude.** Un agent qui n'est pas sûr d'un seuil, d'un format ou d'une décision écrit explicitement « à confirmer » et pose la question — il ne choisit pas silencieusement.
- **Pas d'installation de dépendances non listées** sans le signaler : toute nouvelle dépendance est mentionnée dans la PR avec sa justification.
- **Respecter les gels** : ne pas implémenter E12/E13 (alertes, Premium) ni les items Icebox tant que les gates ne sont pas atteintes, même si « c'est facile ».
- **Mettre à jour les miroirs** : après une décision qui change le backlog, mettre à jour Jira (source de vérité) puis, si demandé, `Backlog/PRODUCT_BACKLOG.md`.
- **Journaliser tout changement de base de données.** Un agent qui ajoute ou modifie un fichier dans `backend/migrations/` (nouvelle table, colonne, index, contrainte, renommage) ajoute une ligne au **Journal des migrations** (section 9) avant de considérer la tâche terminée — sur quelque machine que ce soit. C'est le seul moyen pour qu'un agent démarrant une session ailleurs connaisse l'état réel du schéma sans devoir relire tous les `.sql`.
- **Langue** : documentation et tickets en français ; code, noms de variables et messages de commit en anglais.

## 8. Ce qu'un agent ne fait JAMAIS sans demander

- Modifier `contracts/` ou les fixtures du golden scenario.
- Pousser sur `main`, forcer un push, ou fusionner une PR dont la CI est rouge.
- Supprimer ou renommer un module.
- Changer un modèle IA, un seuil validé ou un prix (4,99 €).
- Activer le watcher Vinted ou toute collecte de données non autorisée.
- Committer une clé d'API, un token ou un identifiant d'affiliation.

---

## 9. Journal des migrations base de données (`backend/migrations/`)

Historique volontairement tenu ici (et pas seulement dans les fichiers `.sql` ou les messages de commit) pour qu'un agent qui démarre une session sur n'importe quelle machine connaisse l'état réel du schéma sans devoir relire toute la migration history. Chaque agent qui touche `backend/migrations/` ajoute une ligne **avant** de clore sa tâche (règle §7).

| Migration | Ticket | Changement | Raison |
|---|---|---|---|
| `001_init.sql` | E1 | `products`, `product_embeddings` (+ index HNSW), `interaction_events`, `user_profiles` | Schéma initial du MVP. |
| `001_interaction_events.sql` | E1 | (voir fichier) | Compagnon de `001_init.sql` pour l'event log. |
| `002_catalog_indexer.sql` | KAN-29 | `products.embedding_version`, `products.needs_reindex`, `product_embeddings.indexed_at` + index unique sur `product_embeddings.product_id` | Support de l'indexeur d'embeddings catalogue. |
| `004_products_available.sql` | KAN-76 | `products.available` (BOOLEAN NOT NULL DEFAULT TRUE) | Colonne manquante dans 001_init — le hard_filter `WHERE available = true` échouait sans elle. |
| `003_user_profiles_event_count.sql` | KAN-31 | `user_profiles.event_count` (INTEGER NOT NULL DEFAULT 0) | Le contrat `UserPreferenceProfile` porte `event_count` depuis KAN-17, mais `001_init.sql` avait omis la colonne — sans elle, un `save()` suivi d'un `load()` ne pouvait pas restituer le profil à l'identique. **Décision confirmée (2026-07-21) :** `user_profiles.vectors` reste en JSONB (positive + negative, cf. `contracts/profile.py::StyleVectors`) et non un unique `vector(512)` natif pgvector — un seul vecteur était l'intention initiale du ticket KAN-31, mais le design à deux vecteurs (déjà dans le contrat) est celui qui prime. |
| `005_embedding_dim_768.sql` | KAN-77 | `product_embeddings.embedding` élargi de `vector(512)` à `vector(768)` (drop + recreate de l'index HNSW) | Le modèle réel Marqo-FashionSigLIP sort du 768-dim, pas 512 — jamais vérifié avant car les tests mockent entièrement l'appel modèle. Confirmé en exécutant le vrai pipeline pour générer les embeddings des archétypes de style (KAN-33). Sans risque aujourd'hui (aucun embedding réel encore calculé) ; ne le serait plus après un vrai import catalogue. |
| `006_alerts.sql` | KAN-69 | Table `alerts` : alert_id (UUID PK), user_id, alert_type (specific_item\|style), label, reference_embedding (JSONB), reference_product_id, constraints (JSONB), status (active\|paused), created_at, schema_version + index `alerts_user_status_idx` | Tier alertes E12 débloqué par Gate 2 ; free tier limité à 3 alertes actives. |
| `007_alerts_dinov2_embedding.sql` | KAN-70 | `alerts.reference_dinov2_embedding JSONB DEFAULT NULL` | DINOv2 CLS-token embedding de l'article de référence pour le matching "même pièce" (seuil 0.80). Séparé de reference_embedding (FashionSigLIP). |
| `010_premium_subscriptions.sql` | KAN-73 | Table `user_subscriptions` (user_id UUID PK, revenuecat_customer_id, status CHECK active\|trialing\|expired\|refunded\|cancelled, expires_at TIMESTAMPTZ) + index `user_subscriptions_status_idx` | Mirror du statut Premium depuis RevenueCat webhook. `is_user_premium()` = status IN (active, trialing, cancelled) ET expires_at > now(). Alerts endpoint bypasse FREE_ALERT_LIMIT si premium. |
| `009_watcher_kill_switch.sql` | KAN-72 | Table `watcher_sources` (source TEXT PK, enabled BOOLEAN DEFAULT FALSE, updated_at TIMESTAMPTZ) + INSERT ('vinted', false) | Kill switch for isolated watcher sources. Checked by retriever at query time (< 1 request to take effect); toggled via POST /admin/watcher/{source}/enable or /disable. Vinted starts disabled pending legal review. |
| `008_notifications.sql` | KAN-71 | Tables `device_tokens` (expo_token + platform), `alert_notification_prefs` (instant\|daily_digest\|disabled), `notification_queue` (scheduled_for, sent_at, is_digest, match_tier CHECK), `notification_log` (opened_at) + index `notification_queue_pending_idx` (WHERE sent_at IS NULL), `notification_queue_user_date_idx` | Infrastructure push Expo : queue asynchrone pour délai 30 min free tier, anti-spam (max 3/jour → digest, quiet hours 22h-8h, fenêtre 1h par alerte). |
| `016_products_gender.sql` | KAN-88 | `products.gender` (TEXT, CHECK men\|women\|unisex) + index partiel `products_gender_idx` | Le feed mélangeait vêtements homme et femme sans qu'on puisse choisir : la moitié de chaque deck était hors sujet. Le genre est déduit du titre et des identifiants de catégorie eBay (`ingestion/normalizer.infer_gender`) — **attention, « women » contient « men »**, donc le féminin est testé en premier avec des frontières de mots. Backfill sur 50 927 produits : 17 879 homme, 8 390 femme, 2 215 unisexe, 22 443 non renseignés. `unisex` est une valeur qui doit apparaître dans tous les feeds ; NULL est aussi montré à tout le monde, sinon on jetterait 44 % du catalogue. Filtre appliqué **au retrieval** (`retrieval/filters.py`) et non après, pour ne pas gaspiller le pool de candidats. |
| `015_seen_products_index.sql` | KAN-88 | Index `interaction_events_user_product_idx` (user_id, product_id) | Le retriever exclut désormais les produits déjà vus via `NOT EXISTS`. Les deux index existants sont sur (user_id, timestamp) et ne peuvent pas servir cette recherche : sans celui-ci, la sous-requête parcourt tous les événements de l'utilisateur à chaque appel du feed. |
| `014_users_and_profile_events.sql` | KAN-88 | Table `users` (user_id UUID PK, email UNIQUE, password_hash, created_at) + index `users_email_idx` ; `interaction_events.product_id` devient nullable | **Aucune table `users` n'existait** : comptes, profils et onboarding vivaient dans des dicts Python (`api/store.py`), donc chaque redémarrage effaçait tous les clients et deux réplicas ne voyaient pas les mêmes utilisateurs. `POST /events` écrivait déjà dans `user_profiles` pendant que `GET /profile` lisait la mémoire — les deux ne pouvaient pas être d'accord. `product_id` devient nullable car une édition de préférence ne concerne aucun produit : `profile.py` inventait `product_id="profile"`, que la clé étrangère vers `products` rejette. |
| `013_products_model.sql` | KAN-87 | `products.model` (TEXT, nullable) | `ProductRecord.model` existe au contrat et `normalize()` le remplit, mais `001_init.sql` n'avait jamais créé la colonne. Sans elle, `_compute_confidence` (qui exige marque ET modèle) ne pouvait jamais renvoyer `MatchConfidence.exact` : l'échelle de prix était réduite à « article ressemblant » au lieu de « le même article, moins cher » — sa promesse centrale. Détecté parce que le golden scenario du ladder exige des correspondances `exact`. eBay n'expose pas de champ modèle : la colonne reste NULL jusqu'au parsing de titres (GLiNER). |
| `012_products_listing_url.sql` | KAN-87 | `products.listing_url` (TEXT, nullable) | Le lien vers l'annonce vendeur était perdu : `normalize()` le portait sur `ProductRecord.affiliate_url` mais aucune colonne ne le stockait, donc un tap produit n'avait nulle part où mener. On stocke l'URL brute (jamais la version affiliée) — les deep links Awin/EPN sont construits à la volée par `ingestion/affiliate.py`, ce qui permet de changer de programme d'affiliation sans ré-ingérer le catalogue. |
| `011_missed_deals.sql` | KAN-74 | Table `missed_deals` (id UUID PK, user_id UUID, alert_id UUID, product_id TEXT, created_at TIMESTAMPTZ) + index `missed_deals_user_idx` (user_id), `missed_deals_user_alert_idx` (user_id, alert_id) | "Pépites manquées" : produits vendus pendant le délai 30 min du free tier. Enregistrées par `flush_due_notifications()` quand un produit n'est plus disponible au moment de l'envoi. Affichées dans `GET /alerts` (champ `missed_deals_count`) comme argument de conversion Premium. |
