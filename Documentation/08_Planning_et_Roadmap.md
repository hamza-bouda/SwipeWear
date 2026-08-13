# 📅 Planning et Roadmap — SwipeWear 2.0

Planification sur 6 mois pour 2 étudiants ingénieurs (~20 h/semaine cumulées), compatible avec les études. **Changement de philosophie vs v1.0 :** le planning n'est plus une suite de jalons de construction, mais une suite de **gates de validation** — chaque phase n'est financée en temps que si la précédente a produit son signal. La v1.0 prévoyait 60 h de MVP ; l'estimation corrigée est de 175-235 h (doc 04 §2.1), d'où un calendrier honnête.

---

## 0. Vue d'ensemble

```
PHASE 0 (Semaines 1-2) ── VALIDATION DEMANDE ─── coût : ~0€, 0 ligne de code produit
   Landing + 8 TikToks (maquettes)
   ▼
 GATE 1 : 300 inscrits OU 1 vidéo >50K vues ?
   ├── NON → itérer le format 2 semaines, puis PIVOT (rien n'a été codé)
   ▼ OUI
PHASE 1 (Mois 1-3) ────── CONSTRUCTION MVP ───── 175-235 h à deux
   Backend + ingestion → App mobile → Alertes/Drop → Beta privée
   ▼
 GATE 2 : ≥30% des beta-testeurs créent ≥2 alertes ET reviennent en S2 ?
   ├── <15% → pivot "comparateur pur" ou arrêt honorable
   ├── 15-30% → itération ciblée 1 mois sur la boucle alerte, re-test
   ▼ ≥30%
PHASE 2 (Mois 4-5) ────── LANCEMENT PUBLIC ───── stores + machine TikTok
   ▼
 GATE 3 (fin Mois 6) : trajectoire vers 5 000 MAU et >1,5% Premium ?
   ├── NON → décision année 2 : niche rentable vs pivot vs arrêt
   ▼ OUI
PHASE 3 (Mois 6+) ─────── V1.5 (matching exact) + creusement du moat
```

---

## 1. Phase 0 — Validation de la demande (Semaines 1-2)

**Objectif :** prouver que le concept génère du désir AVANT d'écrire le produit. Coût : ~0 €.

| Tâche | Qui | Livrable |
| :--- | :--- | :--- |
| Maquettes Figma : swipe, échelle de prix ("Zara 89€ → trouvée 22€, −75%"), notification "ta pépite" | A | 5-6 écrans crédibles |
| Landing page + liste d'attente (email) | A | Page en ligne, analytics |
| 8 vidéos TikTok/Reels sur 2 semaines : "je code l'IA qui chine à ta place", démo maquette, hooks d'économie | B | 8 publications, 4 hooks testés |
| Grille de suivi : vues, CTR bio, inscriptions | B | Tableau de bord simple |

**GATE 1 — critères chiffrés :**
* ✅ **GO :** ≥ 300 inscrits en liste d'attente OU 1 vidéo > 50 000 vues avec CTR bio > 1%.
* 🔁 **Itérer (max 2 semaines de plus) :** 100-300 inscrits — changer les hooks, pas le concept.
* ❌ **Pivot :** < 100 inscrits après ~12 vidéos. Le marché a parlé pour 0 €.

---

## 2. Phase 1 — Construction du MVP (Mois 1 à 3, ~175-235 h)

### 📅 Mois 1 — Données & IA (backend d'abord : le catalogue EST le produit)
* **Ingénieur B (IA/Data) :**
    * PostgreSQL + pgvector (index HNSW), schéma articles/users/alertes/événements.
    * Connecteurs d'ingestion : eBay Browse API, Etsy API, flux Awin/CJ (Vestiaire Collective + 1-2 enseignes neuf). Couche de normalisation (tailles, états, catégories) avec tests par source.
    * Pipeline d'embeddings CLIP `ViT-B-32` (CPU) ; objectif : **30 000 articles indexés, < 5% de doublons**.
* **Ingénieur A (Full-Stack) :**
    * FastAPI : auth (Supabase), endpoints `/feed`, `/like`, `/ladder` ; profil vectoriel (moyenne pondérée, décroissance temporelle).
    * Inscriptions aux programmes d'affiliation (eBay Partner Network, Awin, CJ, Etsy — délais d'approbation : lancer dès la semaine 1).
* **Continu (B) :** 2-3 TikToks/semaine (build in public — la liste d'attente doit grandir pendant la construction).

### 📅 Mois 2 — Application mobile
* **A :** Expo/React Native — onboarding + calibrage (F01-F02), Swipe Deck avec pre-fetching (F03-F06), écran Échelle de prix + redirection affiliée (F07-F08), dressing (F16).
* **B :** règle de composition du feed (70/15/15), qualité de l'échelle de prix (pertinence des similaires), carte de partage (F09).
* ⚠️ **Semaines 6-8 = période d'examens : vélocité réduite à ~4 h/semaine cumulées, planifiée dès maintenant** (le calendrier absorbe 2 semaines creuses sans glisser).

### 📅 Mois 3 — Alertes, Drop, Beta
* **B :** worker de matching d'alertes + file push à deux priorités (F10-F12), Drop quotidien (F15), watcher Vinted isolé (F13).
* **A :** écrans alertes + paywall RevenueCat (F18), réglages/RGPD (F17), déploiement cloud EU, instrumentation analytics complète (doc 07 §6).
* **Beta privée : 100 testeurs** issus de la liste d'attente (TestFlight + Play Beta), 3 semaines d'observation.

**GATE 2 — critères chiffrés (sur les 100 beta-testeurs, semaines 2-3 de beta) :**
* ✅ **GO :** ≥ 30% créent ≥ 2 alertes ET reviennent en semaine 2 ; > 40% d'ouverture des push d'alerte.
* 🔁 **Itérer 1 mois max :** 15-30% — travailler exclusivement la friction de création d'alerte et la qualité du matching, puis re-mesurer.
* ❌ **Pivot/arrêt :** < 15% — la boucle de rétention n'existe pas ; options : comparateur de prix pur (sans alertes), ou arrêt avec un portfolio exceptionnel et ~4 mois investis au lieu de 12.

---

## 3. Phase 2 — Lancement public (Mois 4-5)

### 📅 Mois 4 — Lancement
* Corrections beta, durcissement (rate limits, monitoring, alerting).
* Soumission App Store / Play Store (buffer de 2 semaines pour les reviews Apple — intégré).
* Bascule de la machine TikTok en mode lancement : 5 vidéos/semaine, formats gagnants de la Phase 0, activation de la liste d'attente (email J-3, J0, J+7).
* Micro-créateurs vintage : 10 accès anticipés contre contenu (0 € de budget).

### 📅 Mois 5 — Croissance organique
* Cadence contenu maintenue ; A/B sur les déclencheurs de paywall ; boucle de partage (cartes d'économie) mesurée et optimisée.
* Revue hebdomadaire des KPIs (30 min, mêmes métriques, décisions notées).

**Objectifs fin Mois 5 (réalistes, pas vanity) :**

| Métrique | Cible | Alerte |
| :--- | :---: | :---: |
| Téléchargements cumulés | 5 000 | < 1 500 |
| MAU | 2 500 | < 800 |
| Rétention D30 | > 12% | < 6% |
| Conversion Premium | > 1,5% | < 0,5% |
| CTR sortant (échelle) | > 8% | < 3% |

---

## 4. Phase 3 — V1.5 et moat (Mois 6+, conditionné à GATE 3)

**GATE 3 (fin Mois 6) :** trajectoire crédible vers 5 000 MAU avec Premium > 1,5% et coûts couverts.

Si GO :
* **Catalogue de référence** : 100 produits iconiques (curation manuelle, ~1 h/produit) → échelle "🎯 La même pièce" (F19), historique de prix (F21), alertes de baisse (F20).
* Extension sources (Depop si API exploitable, friperies en ligne partenaires).
* Préparation catégorie sneakers (communauté idéale pour le matching exact).

Si NO-GO : décision structurée — niche rentable à maintenir en 5 h/semaine, pivot documenté, ou arrêt propre (post-mortem écrit, code en portfolio).

---

## 5. Règles de gestion du temps (2 étudiants)

1. **Le calendrier respecte les études, pas l'inverse :** périodes d'examens = vélocité 4 h/semaine, inscrites dans le plan (Mois 2 et Mois 5-6 selon calendrier universitaire).
2. **Rôles nominatifs :** A = produit/infra, B = data/IA + croissance. Le contenu TikTok est une tâche planifiée avec un responsable, pas un reliquat.
3. **Zéro scope creep :** toute idée nouvelle va dans un backlog V2 sans discussion pendant les phases 0-2. Le générateur de tenues, la garde-robe, le B2B : non, pas maintenant.
4. **Les gates sont des engagements :** les seuils sont écrits avant de mesurer, et une décision de gate se prend en une réunion, chiffres à l'appui — c'est la protection contre les 12 mois d'acharnement sur un produit que les données ont invalidé dès le 3ᵉ.
