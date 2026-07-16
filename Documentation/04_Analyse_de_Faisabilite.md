# 📊 Analyse de Faisabilité — SwipeWear 2.0

Évaluation de la faisabilité technique, opérationnelle et économique pour une équipe de **2 étudiants ingénieurs** (1 full-stack, 1 IA), ~20h/semaine cumulées, budget < 50€/mois. Cette version corrige les sous-estimations de la v1.0 (MVP "60 heures") et intègre les nouveaux modules : échelle de prix, moteur d'alertes, ingestion multi-sources légale.

---

## 1. Faisabilité Technique

### 1.1 Architecture cible

```
┌──────────────────────────────────────────────────────────────┐
│                    MOBILE APP (React Native / Expo)          │
│  Swipe Deck · Échelle de Prix · Alertes · Drop quotidien     │
│  Push Notifications (Expo Notifications)                     │
└───────────────────────────┬──────────────────────────────────┘
                            │ HTTPS (REST)
                            ▼
┌──────────────────────────────────────────────────────────────┐
│                     BACKEND (FastAPI, Python)                │
│  /feed /like /ladder /alerts /drop  ·  Auth (Supabase)       │
│  Embeddings CLIP ViT-B-32 (CPU, à l'ingestion uniquement)    │
└──────┬──────────────────────────────┬────────────────────────┘
       │ SQL                          │ Jobs (queue légère)
       ▼                              ▼
┌─────────────────────┐   ┌──────────────────────────────────┐
│ PostgreSQL+pgvector │   │        WORKERS (cron/queue)      │
│ articles, vecteurs  │   │ 1. INGESTION : eBay Browse API,  │
│ (HNSW), users,      │   │    Etsy API, flux Awin/CJ (VC,   │
│ alertes, événements │   │    Zalando, ASOS) — 15-60 min    │
└─────────────────────┘   │ 2. MATCHING ALERTES : nouveaux   │
                          │    articles × alertes actives    │
                          │ 3. FRAÎCHEUR : purge annonces    │
                          │    mortes (vérif différée)       │
                          │ 4. WATCHER VINTED user-initiated │
                          │    (isolé, coupable sans impact) │
                          │ 5. DROP : sélection quotidienne  │
                          └──────────────────────────────────┘
```

**Choix structurants :**
* **pgvector + index HNSW** plutôt qu'une base vectorielle managée : similarité cosinus < 15 ms sur 100K articles, coût nul, une seule base à opérer.
* **CLIP `ViT-B-32` sur CPU** : ~100 ms/image, uniquement à l'ingestion (les vecteurs sont pré-calculés ; aucune inférence au moment du swipe). Pas de GPU au MVP.
* **Le watcher Vinted est un module isolé** avec son propre déploiement : sa mort n'affecte ni le catalogue, ni l'échelle de prix, ni les revenus (principe "survivre sans Vinted").

### 1.2 Les quatre briques et leur difficulté réelle

| Brique | Difficulté | Détail |
| :--- | :---: | :--- |
| **Swipe + reco de style** | 🟢 Faible | Problème résolu : deck-swiper éprouvé côté client ; profil = moyenne mobile pondérée des embeddings likés (décroissance temporelle pour suivre l'évolution du goût) ; reco = top-K par similarité cosinus avec quota d'exploration (10-15% d'articles hors profil pour éviter la bulle). |
| **Ingestion multi-sources** | 🟡 Moyenne | Les API sont documentées et stables (c'est leur raison d'être : générer du trafic affilié). Travail réel : normalisation des schémas hétérogènes (tailles US/EU/UK, états, catégories), déduplication, gestion des quotas. Estimation : 30-40h. |
| **Échelle de prix "même style"** | 🟢 Faible | C'est une requête pgvector triée par prix avec filtres (taille, source). Le travail est dans l'UX, pas dans l'algo. |
| **Échelle de prix "même pièce" (V1.5)** | 🔴 Élevée | Le vrai défi technique du projet. Approche retenue : catalogue de référence de 100-200 produits iconiques construit manuellement (marque + modèle + images canoniques + fourchettes de prix) ; identification par classification contre ce catalogue (similarité forte + parsing de titre + OCR d'étiquette en second signal) ; seuil de confiance élevé, sinon rétrogradation en "même style". **Jamais d'affirmation "identique" sous le seuil.** Estimation : 40-60h, incrémental, hors MVP. |
| **Moteur d'alertes + push** | 🟡 Moyenne | Matching à l'ingestion : chaque nouvel article est comparé aux alertes actives (requête vectorielle inversée + filtres SQL). File de priorité Premium/gratuit. La complexité est opérationnelle (fiabilité du push, déduplication) plus qu'algorithmique. Estimation : 25-35h. |

### 1.3 Performance et coûts d'infrastructure

| Poste | Dimensionnement MVP | Coût/mois |
| :--- | :--- | :--- |
| Serveur API + workers (Railway/Scaleway) | 2 vCPU / 4 Go | 15-25€ |
| PostgreSQL managé + pgvector | 100K articles ≈ 2-3 Go avec vecteurs | 10-15€ |
| Push notifications (Expo) | < 100K/mois | 0€ |
| Supabase Auth | < 50K MAU | 0€ |
| Apple Developer / Google Play | 99€/an + 25$ une fois | ~10€ amorti |
| **Total** | | **≈ 35-50€/mois** |

Latences cibles vérifiées par calcul : recherche HNSW < 15 ms (100K vecteurs), échelle de prix < 400 ms bout en bout, carte de swipe servie depuis cache < 200 ms. Aucun poste ne nécessite de GPU ni de service vectoriel payant avant ~500K articles.

### 1.4 Ce qui a été retiré pour rendre le MVP faisable
* **Générateur de tenues :** la v1.0 proposait d'assembler des tenues par *similarité* CLIP — erreur conceptuelle (deux items similaires se ressemblent, ils ne s'assortissent pas ; il faut de la *complémentarité*). Le problème est un sujet de recherche (datasets type Polyvore Outfits, modèles de compatibilité). Reporté en V2, après traction.
* **Scraping de catalogue :** supprimé par principe. Toute l'ingestion passe par API/flux officiels.
* **Stockage d'images :** aucun ; seules les URLs des CDN sources sont référencées (avec fallback si hotlink refusé : proxy de miniatures à la volée, en cache court).

---

## 2. Faisabilité Opérationnelle (2 étudiants, études en parallèle)

### 2.1 Budget temps honnête

La v1.0 annonçait 60h de MVP : irréaliste d'un facteur 3-5. Estimation corrigée, à deux :

| Lot | Heures |
| :--- | :---: |
| Backend : API, auth, modèle de données, profil vectoriel | 35-45h |
| Ingestion multi-sources + normalisation | 30-40h |
| App mobile : swipe, échelle de prix, alertes, onboarding | 50-65h |
| Moteur d'alertes + push + drop quotidien | 25-35h |
| Watcher Vinted user-initiated (module isolé) | 10-15h |
| QA, beta, corrections, soumission stores | 25-35h |
| **Total MVP** | **175-235h** |

À ~20h/semaine cumulées (10h chacun), cela donne **9 à 12 semaines de développement effectif**, soit un MVP en ~3 mois après la Gate 1 — en tenant compte des périodes d'examens (voir doc 08).

### 2.2 Répartition des rôles (critique en B2C)
* **Ingénieur A (Full-Stack) :** app mobile, API, infra, stores.
* **Ingénieur B (IA/Data) :** pipeline d'ingestion, embeddings, matching, moteur d'alertes — **et le contenu TikTok** (3-5 vidéos/semaine). En B2C, la distribution est la moitié du produit ; elle est assignée nominativement, pas "quand on aura le temps".

### 2.3 Multiplicateurs
* Assistants de codage IA (boilerplate, SQL, composants UI) : facteur ×2 réaliste sur les lots standards (pas sur le matching exact ni la normalisation, qui demandent du jugement).
* Stack volontairement banale (FastAPI + Postgres + Expo) : documentation abondante, zéro exotisme à déboguer.

---

## 3. Faisabilité Économique

### 3.1 Structure de revenu et point mort

Hypothèses prudentes : panier moyen occasion 25€ (commission ~2% ≈ 0,50€/vente), panier neuf 60€ (commission ~7% ≈ 4,20€/vente), conversion Premium 2-4% des MAU.

| Scénario | MAU | Premium (3%) | Revenu Premium | Ventes affiliées/mois | Revenu affiliation | Total/mois |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| Pessimiste | 2 000 | 40 | 200€ | 150 | ~120€ | **~320€** |
| Central | 10 000 | 300 | 1 500€ | 900 | ~800€ | **~2 300€** |
| Optimiste | 40 000 | 1 400 | 7 000€ | 4 500 | ~4 000€ | **~11 000€** |

* **Point mort infra (50€/mois) :** ~350 MAU. Le projet est rentable en coûts directs quasi immédiatement — le vrai coût est le temps des fondateurs.
* **Seuil "job étudiant remplacé" (~1 500€/mois) :** ~7 000-8 000 MAU. Atteignable en 6-9 mois si la boucle TikTok fonctionne ; c'est l'objectif réaliste de l'année 1.
* La v1.0 (2,99€ premium seul, 0€ d'affiliation) exigeait ~5× plus d'utilisateurs pour le même revenu.

### 3.2 Coût d'acquisition
* 100% organique au lancement (TikTok/Reels, format "échelle de prix" auto-générant du contenu). Budget publicitaire : 0€ par contrainte et par choix — si le contenu organique ne prend pas (Gate 1), la publicité payante ne sauverait pas un produit B2C à ARPU faible.

---

## 4. Verdict de faisabilité

| Dimension | Note | Justification |
| :--- | :---: | :--- |
| Technique (MVP) | **8/10** | Briques éprouvées, pas de GPU, pas de scraping ; seule la normalisation multi-sources demande de la rigueur. |
| Technique (V1.5 matching exact) | 6/10 | Difficile mais borné par l'approche "catalogue de référence + seuil de confiance". |
| Opérationnelle | **7/10** | 175-235h à deux : tenable en 3 mois post-validation, à condition d'une discipline de scope absolue. |
| Économique | **7/10** | Coûts dérisoires, double revenu ; la sensibilité est sur le volume d'utilisateurs, pas sur les coûts. |

**Conclusion :** le projet est faisable par cette équipe, dans ce budget temps, sans dépendance illégale ni pari technologique. Le risque résiduel n'est pas la faisabilité — c'est l'adoption (couverte par les Gates 1 et 2 du doc 08).
