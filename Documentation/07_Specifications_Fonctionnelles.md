# 📋 Spécifications Fonctionnelles — SwipeWear 2.0

Spécifications exhaustives du MVP (V1), de la V1.5 et des évolutions V2, avec parcours utilisateur et règles métier. La boucle produit centrale est :

> **Swiper (entraîner l'IA) → Aimer → Échelle de prix (acheter au meilleur prix) → Alerte (être prévenu quand le prix/la pièce voulue existe) → Revenir.**

---

## 1. Fonctionnalités du MVP (V1)

### 1.1 Onboarding
* **F01 — Authentification :** Email / Google / Apple (Supabase Auth). Cible : compte créé en < 60 s.
* **F02 — Calibrage de style (anti cold start) :**
    1. Genre des vêtements recherchés (Homme / Femme / Mixte).
    2. Tailles (hauts, bas, pointures) — utilisées comme filtre dur sur tout le produit.
    3. **Swipe de calibration :** 30 images archétypales couvrant 8-10 clusters de style (streetwear, minimaliste, Y2K, workwear, grunge, bohème, sport, classique). Le vecteur de goût initial = moyenne pondérée des clusters likés.
    * Règle métier : le feed réel n'est servi qu'après ≥ 15 swipes de calibration.

### 1.2 Swipe Deck
* **F03 — Carte article :** photo plein écran ; en superposition : prix (surbrillance), taille, marque, badge source (eBay / Etsy / Vestiaire Collective / enseigne neuf), badge état (neuf / très bon / bon), âge de l'annonce ("il y a 3 h").
* **F04 — Gestes :**
    * *Droite* = Like → dressing + mise à jour du vecteur de goût.
    * *Gauche* = Rejet → l'article ne réapparaît plus ; signal négatif pondéré (poids 0,3× celui d'un like).
    * *Haut* = **Créer une alerte** pré-remplie à partir de la carte (voir F10).
    * Boutons physiques équivalents en bas d'écran (accessibilité).
* **F05 — Pre-fetching :** 10 cartes préchargées (images incluses) ; latence perçue nulle.
* **F06 — Règle de composition du feed :** 70% exploitation (proches du vecteur de goût), 15% exploration (hors profil, pour découvrir et affiner), 15% fraîcheur (annonces < 24 h, favorisant des alertes et des achats réalisables).

### 1.3 Échelle de Prix (cœur de la v2.0)
* **F07 — Vue Échelle :** accessible au tap sur toute carte likée ou depuis le dressing.
    * **Section "👀 Dans le même style, du moins cher au plus cher" (MVP) :** top 20 par similarité CLIP, filtré taille, trié prix croissant. Chaque ligne : vignette, prix, source, état, taille.
    * **Bandeau d'économie :** "Jusqu'à −72% vs le neuf" (calculé contre l'article neuf le plus proche du flux affilié).
    * Filtres : sources, état minimum, fourchette de prix.
* **F08 — Redirection affiliée :** ouverture de la fiche d'origine (deep link app si installée, sinon navigateur) ; lien affilié injecté quand le programme existe ; mention "lien partenaire" visible. Tracking : événement `outbound_click` (source, prix, position dans l'échelle).
* **F09 — Carte de partage :** génération d'une image (pièce + échelle + % d'économie + watermark SwipeWear) exportable en story/TikTok. C'est le vecteur viral principal : soigner le design au niveau "screenshotable".

### 1.4 Alertes
* **F10 — Création d'alerte (friction minimale) :** via Swipe Haut → pré-remplie : style (embedding de la carte), tailles (profil), budget max (prix médian du style −20%). Modifiable en un écran. Alternative : création depuis le profil (style à partir du vecteur global).
* **F11 — Matching d'alertes (worker) :** à chaque ingestion d'article, comparaison aux alertes actives : similarité ≥ 0,90 ∧ taille exacte ∧ prix ≤ budget. File de notification à deux priorités : **Premium = immédiat ; Gratuit = délai 30 min** (l'article peut donc être déjà parti — c'est la démonstration produit du Premium, assumée et affichée honnêtement : "Les membres Gold ont été prévenus il y a 30 min").
* **F12 — Notification type :** *"🎯 Ta pépite : Carhartt Detroit, M, 24 € (−80% vs neuf). Vue il y a 4 min."* → tap = fiche article + échelle de prix.
* **F13 — Watcher Vinted user-initiated (module isolé) :** l'utilisateur colle l'URL d'une recherche/d'un article Vinted ; vérification périodique plafonnée (1 check / 15 min / alerte, budget global par utilisateur) ; notification au changement (nouvel article correspondant / baisse de prix). Règles strictes : aucune donnée stockée au-delà des correspondances de l'utilisateur ; module désactivable globalement par variable d'environnement sans impact sur le reste.
* **F14 — Quotas :** Gratuit = 1 alerte active + 1 watcher Vinted. Premium = illimité (plafond anti-abus : 50).

### 1.5 Drop Quotidien
* **F15 — Sélection :** 15 articles/jour/utilisateur, score = 0,5×proximité de style + 0,3×fraîcheur (< 48 h) + 0,2×rapport qualité/prix (écart au prix médian du style). Notification à 19 h locale. Le Drop est épuisable — une fois les 15 cartes vues, message de clôture ("Reviens demain 19 h — ou crée une alerte") : la rareté du contenu crée le rituel, l'alternative proposée nourrit P1.

### 1.6 Dressing & Profil
* **F16 — Dressing :** grille des articles likés, tri par catégorie/prix/disponibilité ; les articles vendus passent en grisé ("Vendu — crée une alerte pour la prochaine").
* **F17 — Profil & réglages :** tailles, styles, gestion des alertes, fréquence de push, abonnement, suppression de compte en un tap (RGPD).

### 1.7 Premium (SwipeWear Gold — 4,99 €/mois ou 39,99 €/an)
* **F18 — Paywall :** déclencheurs contextuels — création de la 2ᵉ alerte ; affichage "les membres Gold ont été prévenus avant toi" sur une pépite ratée ; fin du Drop. Achat in-app (RevenueCat). Essai 7 jours.

---

## 2. V1.5 (post-Gate 2)

* **F19 — Échelle "🎯 La même pièce" :** matching exact contre le **catalogue de référence** (100-200 produits iconiques vérifiés manuellement : marque, modèle, images canoniques, fourchette de prix marché). Identification = similarité visuelle forte + parsing du titre + OCR d'étiquette en signal secondaire ; seuil de confiance élevé, sinon rétrogradation silencieuse en "même style". Bouton "ce n'est pas la même pièce" → retrait + correction du catalogue.
* **F20 — Alerte de baisse de prix :** sur un article précis ("préviens-moi sous 30 €") et sur un produit de référence ("une 501 W28 sous 25 €, quel que soit le vendeur").
* **F21 — Historique de prix :** sur les produits du catalogue de référence, mini-graphe des prix observés (occasion vs neuf) — argument de confiance et de partage.

---

## 3. V2 (après traction, non spécifié en détail)
* Générateur de tenues par **compatibilité** (règles catégorielles + modèle entraîné sur dataset de tenues type Polyvore — l'approche par similarité de la v1.0 est abandonnée car conceptuellement erronée).
* Numérisation de la garde-robe personnelle (Edge-AI, détection multi-vêtements sur photo de placard).
* Insights tendances anonymisés (B2B).

---

## 4. Parcours Utilisateur Principal

```
     ┌──────────────────────────────┐
     │  Téléchargement & Inscription │  (< 60 s)
     └──────────────┬───────────────┘
                    ▼
     ┌──────────────────────────────┐
     │  Calibrage : tailles + 30    │
     │  swipes archétypaux          │
     └──────────────┬───────────────┘
                    ▼
     ┌──────────────────────────────┐    Swipe Gauche (rejet)
┌───►│        SWIPE DECK            │◄──────────────┐
│    └───┬──────────────────┬───────┘               │
│        │ Swipe Droite     │ Swipe Haut            │
│        ▼ (like)           ▼                       │
│  ┌───────────┐    ┌──────────────┐                │
│  │ DRESSING  │    │ ALERTE créée │                │
│  └─────┬─────┘    │ (pré-remplie)│                │
│        │ tap      └──────┬───────┘                │
│        ▼                 │  … l'app chine 24h/24  │
│  ┌────────────────┐      ▼                        │
│  │ ÉCHELLE DE PRIX│  ┌─────────────────────┐      │
│  │ du − cher au   │  │ 🎯 PUSH "ta pépite" │      │
│  │ + cher         │  │ (Gold: instantané)  │      │
│  │ occasion+neuf  │  └─────────┬───────────┘      │
│  └───┬────────┬───┘            │ tap              │
│      │        │ partage        ▼                  │
│      │        ▼          [Échelle de prix]        │
│      │   [Story/TikTok]                           │
│      ▼                                            │
│  ┌──────────────────────────┐                     │
│  │ REDIRECTION AFFILIÉE     │                     │
│  │ (eBay/Etsy/VC/enseigne)  │                     │
│  └──────────────────────────┘                     │
│                                                   │
└──── Push DROP quotidien 19h (15 cartes) ──────────┘
```

---

## 5. Écrans Clés (wireframes conceptuels)

### 5.1 Écran Swipe
* Header minimal : logo, icône alertes (badge), icône dressing.
* Carte = 90% de l'écran ; overlay bas : marque, taille, **prix en vert**, source, âge de l'annonce.
* Boutons bas : ✕ (rejet) · 🔔 (alerte) · ♥ (like).

### 5.2 Écran Échelle de Prix
* En-tête : la pièce likée + bandeau d'économie ("jusqu'à −72% vs neuf").
* Liste triée prix croissant, badges source/état/taille par ligne.
* (V1.5) Deux sections étiquetées : "🎯 La même pièce" puis "👀 Dans le même style".
* Footer : bouton de partage (carte d'économie) + "Créer une alerte sur ce style".

### 5.3 Écran Alertes
* Liste des alertes actives : miniature du style, taille, budget, source(s), statut ("3 trouvailles cette semaine").
* CTA Premium permanent si quota atteint : "Passe en Gold — sois prévenu·e en premier."

---

## 6. Événements analytics (minimum viable de mesure)

| Événement | Sert à mesurer |
| :--- | :--- |
| `swipe` (direction, latence) | Engagement, qualité du feed |
| `alert_created` / `alert_deleted` | **Gate 2 (P1)** — la métrique décisive |
| `push_sent` / `push_opened` | Qualité des alertes (P4), rétention |
| `ladder_viewed` / `outbound_click` (position, source, prix) | Conversion affiliation, valeur de l'échelle |
| `share_card_generated` | Boucle virale |
| `drop_opened` / `drop_completed` | Rituel quotidien |
| `paywall_viewed` / `subscribe` (déclencheur) | Conversion Premium par contexte |
