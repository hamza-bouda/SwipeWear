# 📋 SwipeWear — Product Backlog

> **Version :** 1.0 · **Date :** 2026-07-18 · **Product Owner :** Hamza Bouda
> **Source de vérité :** ce fichier. Alimenté en continu pendant le développement.
> **Basé sur :** AI Brain Professional Blueprint v3 + Documentation v2.0 (docs 01-09) + tests IA validés (GO 6/6, rapport du 2026-07-16).

---

## Comment lire / alimenter ce backlog

- **Trié du plus prioritaire au moins prioritaire** — l'ordre dans chaque section EST la priorité.
- **Priorité** : `P0` bloquant MVP · `P1` MVP · `P2` post-MVP proche (V1.5) · `P3` plus tard / idée.
- **Taille** (T-shirt) : `XS` ≤ 2h · `S` ≤ 1 jour · `M` 2-3 jours · `L` ~1 semaine · `XL` à découper avant de démarrer.
- **Lane** (règle du blueprint §10 — 2 devs en parallèle) : `🟦 PI` = Product Intelligence (ingestion, vision, embeddings, retrieval) · `🟩 PERSO` = Personnalisation (profil, ranking, policy, explication) · `⬜ COMMUN` = contrats, infra, app, orchestration.
- **Statut** : `📥 Backlog` → `🔍 Refined` (ticket détaillé écrit) → `🔨 En cours` → `✅ Done` → `🧊 Gelé`.
- **Règle d'or (blueprint §11)** : *contracts first* — aucun item d'implémentation ne démarre tant que E1 n'est pas Done.
- Pour ajouter un item : lui donner le prochain ID de son epic, l'insérer À SA PLACE de priorité (pas en fin de liste), remplir toutes les colonnes.

---

## Vision & jalon

**MVP =** un utilisateur fait l'onboarding (styles ou images d'inspiration) → swipe un feed personnalisé qui **réagit de façon prévisible** à ses swipes → sur un like, voit l'**échelle de prix** (occasion + neuf, du moins cher au plus cher, liens affiliés) → peut inspecter/éditer son algorithme.
**Definition of Done globale** : les 9 preuves du blueprint §15 (onboarding, learning, retrieval, ranking, diversité, explicabilité, modularité, debugging, data).

Gates business (doc 08) restent au-dessus du backlog : **Gate 1** (300 waitlist / 50K vues) avant d'investir au-delà de E1-E4 ; **Gate 2** (≥30% beta créent ≥2 alertes) avant V1.5.

---

# ÉPICS (ordre de priorité)

| # | Epic | Lane | Objectif | Priorité |
|---|------|------|----------|----------|
| E1 | Contrats & fondations | ⬜ | Schémas partagés, repo, fixtures — débloque le travail en parallèle | P0 |
| E2 | Ingestion produits | 🟦 | Catalogue normalisé depuis sources autorisées | P0 |
| E3 | Vision & embeddings | 🟦 | FashionSigLIP + Qwen derrière adapters | P0 |
| E4 | Profil utilisateur vivant | 🟩 | UserPreferenceProfile + apprentissage par swipe | P0 |
| E5 | Retrieval | 🟦 | pgvector : bons candidats dans le top set | P0 |
| E6 | Ranking & feed policy | 🟩 | Ordre + diversité (MMR, epsilon-greedy) | P1 |
| E7 | App mobile (swipe + onboarding) | ⬜ | React Native/Expo, écrans cœur | P1 |
| E8 | Échelle de prix & affiliation | 🟦 | Le différenciateur business (F07) | P1 |
| E9 | "Your Algorithm" & explicabilité | 🟩 | Préférences inspectables/éditables | P1 |
| E10 | Observabilité & évaluation | ⬜ | Trace par module, golden scenario, fallbacks | P1 |
| E11 | Growth & Gate 1 | ⬜ | Landing, waitlist, TikTok | P1 (parallèle) |
| E12 | Alertes & matching V1.5 | 🟦 | DINOv2 "même pièce", alertes temps réel | P2 |
| E13 | Premium & monétisation app | 🟩 | 4,99€/mois, priorité d'alertes | P2 |
| E14 | Idées / icebox | — | Tout ce qui arrive en cours de route | P3 |

---

# BACKLOG DÉTAILLÉ (trié par priorité globale)

## E1 · Contrats & fondations — P0 ⬜ COMMUN

| ID | Item | User story / valeur | Taille | Dépend de | Statut |
|----|------|---------------------|--------|-----------|--------|
| E1-01 | Repo monorepo + structure blueprint | `contracts/ ingestion/ vision/ embeddings/ preferences/ retrieval/ ranking/ policy/ explainability/ evaluation/ orchestration/` + CI lint/tests | S | — | 📥 |
| E1-02 | Contrat `ProductRecord` v1 | Schéma normalisé d'un produit (source, prix, taille, état, images, url affiliée, versions) — *"every product traceable to its authorized source record"* | S | E1-01 | 📥 |
| E1-03 | Contrat `UserPreferenceProfile` v1 | 3 couches : hard constraints / préférences éditables / vecteurs denses (+ version de schéma et d'embedding) | S | E1-01 | 📥 |
| E1-04 | Contrat `InteractionEvent` v1 + event log | Swipe droite/gauche(2 types)/save/open/edit — l'event log est **source de vérité**, profil rejouable | S | E1-01 | 📥 |
| E1-05 | Contrats pipeline reco (`CandidateSet`, `RankedFeed`, `Explanation`) | Interfaces entre retrieval → ranking → policy → explainer | S | E1-02, E1-03 | 📥 |
| E1-06 | Fixtures partagées + golden scenario v0 | 1 user fictif + mini-catalogue figé (~50 produits) : les 2 lanes développent contre les mêmes données ; détecte les régressions | M | E1-02..05 | 📥 |
| E1-07 | Squelette orchestrateur | Séquence les appels, zéro logique métier ; typed errors par module | S | E1-05 | 📥 |
| E1-08 | Postgres + pgvector en local (docker-compose) | Base commune dès le début, migrations | S | E1-01 | 📥 |

## E2 · Ingestion produits — P0 🟦 PI

| ID | Item | User story / valeur | Taille | Dépend de | Statut |
|----|------|---------------------|--------|-----------|--------|
| E2-01 | Connector eBay Browse API (occasion) | Source **autorisée** principale ; isolée derrière l'interface `Source` (principe "survivre sans Vinted") | M | E1-02 | 📥 |
| E2-02 | Étape normalisation | Source brute → `ProductRecord` (devise, tailles FR/EU, état, catégorie) | M | E2-01 | 📥 |
| E2-03 | Enrichissement titres via GLiNER | marque/modèle/taille/couleur/état extraits (validé : 5/5, 224 ms/titre) | S | E2-02 | 📥 |
| E2-04 | Connector neuf (Awin **ou** CJ — 1 seul au MVP) | Nécessaire à l'échelle de prix occasion+neuf | M | E2-02 | 📥 |
| E2-05 | Job de rafraîchissement + dédup | Prix/dispo à jour, pas de doublons inter-sources | M | E2-02 | 📥 |
| E2-06 | Connector Etsy | 3e source, élargit l'occasion/artisanal | M | E2-02 | 🧊 (après Gate 1) |

## E3 · Vision & embeddings — P0 🟦 PI

| ID | Item | User story / valeur | Taille | Dépend de | Statut |
|----|------|---------------------|--------|-----------|--------|
| E3-01 | Service embeddings FashionSigLIP (adapter) | Espace vectoriel principal catalogue + profil (validé : 284 ms/img CPU) ; interface remplaçable (Qwen3-VL-Embedding en bench plus tard) | M | E1-01 | 📥 |
| E3-02 | Pipeline d'indexation catalogue | Chaque `ProductRecord` → embedding versionné → pgvector (HNSW) | M | E3-01, E1-08, E2-02 | 📥 |
| E3-03 | Analyse d'images d'inspiration : Qwen3-VL-2B quantisé (adapter) | Scènes complexes → facts structurés + crops de vêtements ; **fallback** : embedding seul + confirmation des tags par l'user | L | E3-01 | 📥 |
| E3-04 | Bench Qwen sur PC 16 GB | Latence/qualité en quantisé, petits batchs — décide si E3-03 reste au MVP ou passe serveur | S | — | 📥 |
| E3-05 | Segmentation SegFormer sur photos portées | Améliore la qualité des crops (validé) — optionnel MVP | S | E3-03 | 🧊 |

## E4 · Profil utilisateur vivant — P0 🟩 PERSO

| ID | Item | User story / valeur | Taille | Dépend de | Statut |
|----|------|---------------------|--------|-----------|--------|
| E4-01 | Store du profil 3 couches | Hard constraints (taille, budget, région) + préférences éditables + vecteurs | M | E1-03 | 📥 |
| E4-02 | Preference updater — règles par action | Table du blueprint §6 : right→positif+poids+intent ; left "pas mon style"→négatif style ; left "trop cher"→budget **seulement** ; save/open→signal fort ; edit→override prioritaire. Transparent, configurable, testé | M | E4-01, E1-04 | 📥 |
| E4-03 | Onboarding route A : choix de styles visuels | Grille de styles → profil v1 immédiat | S | E4-01 | 📥 |
| E4-04 | Onboarding route B : import d'images d'inspiration | Photos perso/Pinterest → même `UserPreferenceProfile` v1 que la route A | M | E4-01, E3-03 | 📥 |
| E4-05 | Rebuild du profil par replay de l'event log | Migration de schéma et debug sans perte | S | E4-02 | 📥 |
| E4-06 | Fallback updater | Échec → profil précédent conservé, event mis en file pour replay | XS | E4-02 | 📥 |

## E5 · Retrieval — P0 🟦 PI

| ID | Item | User story / valeur | Taille | Dépend de | Statut |
|----|------|---------------------|--------|-----------|--------|
| E5-01 | Hard filters | Taille, prix, région, dispo — AVANT le vectoriel (symptôme dédié : "wrong size/price" = ici) | S | E2-02, E4-01 | 📥 |
| E5-02 | Retrieval vectoriel pgvector top-K | Profil (vecteurs) → `CandidateSet` ; métrique : les styles pertinents entrent dans le set | M | E3-02, E5-01 | 📥 |
| E5-03 | Fallback retriever | Échec → produits récents/curés respectant les hard constraints | XS | E5-01 | 📥 |
| E5-04 | Éval retrieval sur golden scenario | Recall@K mesuré à chaque changement | S | E1-06, E5-02 | 📥 |

## E6 · Ranking & feed policy — P1 🟩 PERSO

| ID | Item | User story / valeur | Taille | Dépend de | Statut |
|----|------|---------------------|--------|-----------|--------|
| E6-01 | Ranker v1 : score Python transparent | Features lisibles (similarité, fraîcheur, prix vs budget, marque aimée) ; **reçoit profil + candidats complets, zéro lecture DB cachée** | M | E5-02 | 📥 |
| E6-02 | Diversité MMR | Feed sans quasi-doublons | S | E6-01 | 📥 |
| E6-03 | Exploration epsilon-greedy contrôlée | Découverte sans feed aléatoire | S | E6-02 | 📥 |
| E6-04 | Fallbacks ranking/policy | Ranker KO → tri par similarité ; policy KO → liste rankée brute | XS | E6-01 | 📥 |
| E6-05 | Éval ranking vs baseline similarité | Preuve DoD : les actions utiles s'améliorent vs baseline | S | E6-01, E1-06 | 📥 |
| E6-06 | LightGBM Ranker | Après vraies données d'interaction seulement | L | E6-05 + data réelle | 🧊 |

## E7 · App mobile — P1 ⬜ COMMUN

| ID | Item | User story / valeur | Taille | Dépend de | Statut |
|----|------|---------------------|--------|-----------|--------|
| E7-01 | Setup Expo + navigation + design system | Base des écrans (reprendre le prototype HTML/Figma) | M | — | 📥 |
| E7-02 | Écran swipe (deck de cartes) | Cœur de l'expérience ; gestes + 2 types de left (pas mon style / trop cher) | M | E7-01 | 📥 |
| E7-03 | Écrans onboarding (routes A et B) | Connectés à E4-03/04 | M | E7-01 | 📥 |
| E7-04 | API FastAPI : feed, swipe, profil | L'app consomme l'orchestrateur | M | E1-07, E6-01 | 📥 |
| E7-05 | Fiche produit + save | Signal fort (E4-02) + porte d'entrée de l'échelle de prix | S | E7-02 | 📥 |
| E7-06 | Auth légère + persistance | Comptes simples (email/Apple/Google) | M | E7-01 | 📥 |
| E7-07 | Analytics events produit | Instrumentation des events doc 07 (mesure Gate 2) | S | E7-02 | 📥 |

## E8 · Échelle de prix & affiliation — P1 🟦 PI

| ID | Item | User story / valeur | Taille | Dépend de | Statut |
|----|------|---------------------|--------|-----------|--------|
| E8-01 | Agrégation multi-sources d'un produit liké | "Même style" (FashionSigLIP) cross-sources → une échelle | M | E5-02, E2-04 | 📥 |
| E8-02 | UI échelle de prix (moins cher → plus cher, occasion + neuf) | **Le différenciateur** (F07) ; badges occasion/neuf, état, source | M | E8-01, E7-05 | 📥 |
| E8-03 | Liens affiliés + tracking | eBay Partner Network + Awin/CJ ; ids de tracking corrects = le revenu | S | E8-01 | 📥 |
| E8-04 | Inscriptions programmes d'affiliation | Tâche admin (EPN, Awin/CJ) — délais d'approbation, à lancer TÔT | S | — | 📥 |

## E9 · "Your Algorithm" & explicabilité — P1 🟩 PERSO

| ID | Item | User story / valeur | Taille | Dépend de | Statut |
|----|------|---------------------|--------|-----------|--------|
| E9-01 | API préférences : inspecter/ajouter/retirer/verrouiller | Le cerveau devient contrôlable (blueprint §9) ; edit = override max (E4-02) | M | E4-01 | 📥 |
| E9-02 | Écran "Your Algorithm" | UI des préférences + verrous | M | E9-01, E7-01 | 📥 |
| E9-03 | Explainer : raisons groundées | Chaque raison affichée tracée à une évidence stockée ; fallback : tags éditables sans phrase | M | E6-01 | 📥 |

## E10 · Observabilité & évaluation — P1 ⬜ COMMUN

| ID | Item | User story / valeur | Taille | Dépend de | Statut |
|----|------|---------------------|--------|-----------|--------|
| E10-01 | Trace par requête, par module | warnings + latence + versions à chaque étage — "one trace identifies the failing stage" | M | E1-07 | 📥 |
| E10-02 | Golden scenario en CI | Rejoue le user+catalogue figés après chaque merge | S | E1-06, E10-01 | 📥 |
| E10-03 | Rapports d'éval Git + JSON/CSV | Tracking d'expériences léger (MLflow seulement si ça se multiplie) | S | E5-04, E6-05 | 📥 |
| E10-04 | Table des latences cibles par module | Budget par module, mesuré dans la trace | XS | E10-01 | 📥 |

## E11 · Growth & Gate 1 — P1 (en parallèle, ne dépend de rien) ⬜

| ID | Item | User story / valeur | Taille | Dépend de | Statut |
|----|------|---------------------|--------|-----------|--------|
| E11-01 | Landing page + waitlist | Objectif Gate 1 : 300 inscrits | S | — | 📥 |
| E11-02 | 10 TikToks concept (prototype à l'appui) | Objectif : 50K vues cumulées ; teste le message "AI sniper de pépites" | M | — | 📥 |
| E11-03 | Mesure & décision Gate 1 | Dashboard simple ; si raté → pivot du message avant de coder E6-E9 | XS | E11-01/02 | 📥 |

## E12 · Alertes & matching V1.5 — P2 🟦 (après Gate 2)

| ID | Item | User story / valeur | Taille | Dépend de | Statut |
|----|------|---------------------|--------|-----------|--------|
| E12-01 | Création d'alertes (pièce/style + contraintes) | Rétention cœur (doc 06 : risque P1 = boucle d'alerte) | M | E4-01 | 🧊 |
| E12-02 | Matching "même pièce" DINOv2, seuil ~0.80 | Validé : marge 0.448 (0.956 vs 0.508) ; 2 tiers exact/similaire | L | E12-01, E3-02 | 🧊 |
| E12-03 | Notifications push | La boucle d'alerte devient réelle | M | E12-01 | 🧊 |
| E12-04 | Watcher Vinted isolé (architecture "survivre sans") | Source non-API dans un process séparé, coupable sans casser l'app | L | E12-01 | 🧊 |

## E13 · Premium — P2 🟩 (après Gate 2)

| ID | Item | User story / valeur | Taille | Dépend de | Statut |
|----|------|---------------------|--------|-----------|--------|
| E13-01 | IAP 4,99€/mois (RevenueCat) | Monétisation directe | M | E12-03 | 🧊 |
| E13-02 | Priorité d'alertes (instant vs +30 min) | La feature premium vendue | S | E13-01, E12-03 | 🧊 |

## E14 · Icebox — P3

| ID | Item | Note |
|----|------|------|
| E14-01 | Bench Qwen3-VL-Embedding-2B dans un index séparé | Blueprint §13 "later" |
| E14-02 | Grounding DINO + SAM 2 | Si la qualité des crops l'exige |
| E14-03 | Learned profile updater | Seulement avec assez d'évidence |
| E14-04 | Contextual bandits | Après monitoring mature |
| E14-05 | FAISS offline / MLflow | Si les expériences se multiplient |
| E14-06 | GPU loué ponctuel pour gros batchs catalogue | Blueprint "Local PC reality" |

---

## Sprint 1 proposé (2 devs, ~2 semaines)

> Objectif : **contrats posés + une tranche verticale minuscule qui tourne** (1 source → embeddings → retrieval → feed trié par similarité sur le golden scenario).

- **Ensemble (2-3 j)** : E1-01 → E1-08 (contrats, fixtures, orchestrateur, pgvector).
- **Dev 🟦 PI** : E2-01, E2-02, E3-01, E3-02, E8-04 (lancer les inscriptions affiliation, ça traîne).
- **Dev 🟩 PERSO** : E4-01, E4-02, E4-03, E5-01 (+ démarre E11-01 landing).
- **Démo de fin de sprint** : golden user → feed de vrais produits eBay filtrés + triés par similarité, profil qui bouge après swipes simulés.

---

## Journal du backlog

| Date | Changement |
|------|-----------|
| 2026-07-18 | v1.0 — création initiale depuis Blueprint v3 + docs v2.0 |
