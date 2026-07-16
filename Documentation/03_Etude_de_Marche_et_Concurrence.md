# 📊 Étude de Marché et Concurrence — SwipeWear 2.0

Analyse sectorielle, étude de la demande et cartographie concurrentielle à l'horizon 2026-2027. Cette version corrige l'angle mort majeur de l'étude v1.0 : l'omission des précédents du swipe-shopping (presque tous morts) et des comparateurs occasion existants (Faircado, Beni, Gem).

---

## 1. Le Marché

### 1.1 Taille et dynamique
* **France :** marché de la seconde main > 7 Md€ (2025-2026). Vinted : 23 millions d'utilisateurs français (~35% de la population). Plus d'un tiers des Français achètent régulièrement d'occasion.
* **Europe :** > 30 Md€ attendus d'ici 2027, croissance +15-18%/an — 4× plus rapide que le neuf.
* **Affiliation mode :** le neuf en ligne (Zalando ~10 Md€ GMV Europe, ASOS, etc.) rémunère l'apport d'affaires à 5-10% — un gisement de revenu que la v1.0 ignorait totalement.

### 1.2 Les moteurs de la demande
1. **Pouvoir d'achat :** les 15-30 ans, les plus touchés par l'inflation, veulent des marques de qualité (Nike, Levi's, Carhartt) au prix de l'occasion.
2. **Régulation :** lois anti-fast-fashion françaises (taxes sur le neuf jetable importé, encadrement de la publicité Shein/Temu) — le différentiel de prix neuf/occasion se creuse par la loi.
3. **Culture :** l'esthétique vintage/Y2K et le "fit check" TikTok valorisent la pièce unique. Payer moins cher n'est plus honteux, c'est **revendiqué** — la bonne affaire est un contenu social.

### 1.3 La douleur précise que SwipeWear v2.0 adresse (et que la v1.0 ratait)
La v1.0 visait "la recherche est ennuyeuse" — un irritant. La v2.0 vise deux douleurs chiffrables :

| Douleur | Preuve d'intensité | Qui paie déjà pour la résoudre |
| :--- | :--- | :--- |
| **Rater la pièce unique** (vendue en heures) | Outils d'alerte/snipe Vinted payants utilisés par les revendeurs (10-30€/mois) ; groupes Telegram d'alertes | Revendeurs, collectionneurs sneakers |
| **Surpayer** (ne pas savoir que la même pièce existe moins cher ailleurs, occasion ou neuf) | Croissance de Faircado/Beni ; réflexe généralisé "je vérifie sur Vinted avant d'acheter neuf" (friction manuelle : 4 apps, 40 min) | Utilisateurs d'extensions cashback/comparateurs (Joko, Ideal) |

---

## 2. Cartographie de la Concurrence

### 2.1 Vue d'ensemble

```
                        [ COMPARAISON DE PRIX ]
                                  ▲
                                  │   Faircado, Beni
                                  │   (extensions desktop,
                                  │    pas d'IA de style)
                                  │
                                  │        🎯 SwipeWear 2.0
                                  │        (mobile + IA de style
                                  │         + alertes + neuf/occasion)
                                  │
 [ RECHERCHE UTILITAIRE ] ────────┼──────────── [ DÉCOUVERTE PERSONNALISÉE ]
                                  │
   Vinted, Depop, eBay            │        Pinterest, TikTok Shop
   (silos mono-plateforme,        │        (inspiration sans achat
    mots-clés textuels)           │         d'occasion réel)
                                  │
                                  ▼
                        [ ALERTES / SNIPE ]
                     Outils d'alerte Vinted pour
                     revendeurs (fonctionnels, laids,
                     mono-plateforme, non grand public)
```

### 2.2 Analyse par catégorie

#### A. Les plateformes sources (Vinted, Depop, eBay, Vestiaire Collective)
* **Vinted :** leader absolu de l'inventaire d'occasion en France. Recherche utilitaire par mots-clés, alertes "recherches sauvegardées" lentes et sans compréhension du style. Pas d'API publique, pas d'affiliation. **À la fois la plus grosse menace concurrentielle (peut copier le swipe) et structurellement incapable de copier la proposition centrale : Vinted ne comparera jamais ses prix avec eBay et Zalando.**
* **eBay :** inventaire vintage/streetwear massif et sous-estimé en France ; API riche (Browse API) + programme partenaire rémunérateur. **Allié structurel n°1 du projet.**
* **Vestiaire Collective :** milieu/haut de gamme, affiliation via Awin. Complète l'échelle de prix vers le haut.
* **Depop :** esthétique forte, présence UK ; API limitée — source secondaire.

#### B. Les comparateurs seconde main (les vrais concurrents directs)
* **Faircado (Berlin) :** extension navigateur qui propose des alternatives d'occasion quand on consulte un produit neuf. Financée, en croissance. **Validation directe du concept** — mais desktop, orientée "consommation responsable", sans IA de style personnalisée ni dimension découverte/alertes.
* **Beni (US) :** même modèle, marché américain.
* **Gem :** moteur de recherche vintage agrégé (US/global), orienté recherche experte par mots-clés, pas de personnalisation visuelle.
* **Lecture stratégique :** ces acteurs prouvent que l'agrégation légale par affiliation fonctionne. Aucun n'occupe le **mobile-first + IA de style + alertes temps réel** — la combinaison SwipeWear. Le risque est qu'ils y viennent ; la réponse est la vitesse.

#### C. Les outils d'alerte/snipe (préexistants, non grand public)
* Divers bots et services d'alerte Vinted (souvent semi-clandestins, 10-30€/mois) utilisés par les revendeurs. UX rudimentaire, mots-clés uniquement, zéro dimension style, gris juridiquement. **Ils prouvent la disposition à payer pour la vitesse** ; SwipeWear en est la version légale, visuelle et grand public.

#### D. Le cimetière du swipe-shopping (leçon d'histoire assumée)
* **Mallzee, Grabble, Stylect (2014-2018) : morts.** Le swipe comme *divertissement* d'achat ne retient pas : la nouveauté s'use en semaines et le neuf n'a aucune urgence (l'article sera encore là demain).
* **Pourquoi SwipeWear v2.0 échappe à ce destin (thèse) :** (1) l'occasion a une urgence *réelle* que le neuf n'a pas — la pièce disparaît ; (2) le swipe n'est plus le produit mais l'*entraînement* de l'IA ; la rétention repose sur les alertes et le drop, pas sur l'amusement ; (3) la monétisation ne dépend pas du temps passé mais de la valeur des transactions. **Cette thèse est exactement ce que Gate 2 doit prouver ou infirmer.**

#### E. Les inspirationnels (Pinterest, TikTok Shop)
* Pinterest inspire mais ne vend pas d'occasion (liens morts, produits neufs). TikTok Shop pousse du neuf bas de gamme. Ils définissent les codes visuels de la cible mais ne résolvent ni le prix ni la disponibilité — complémentaires plus que concurrents.

### 2.3 Tableau de positionnement

| Caractéristique | Vinted | Faircado | Outils d'alerte | Pinterest | **SwipeWear 2.0** |
| :--- | :---: | :---: | :---: | :---: | :---: |
| Inventaire occasion | ✅ (le meilleur) | ✅ | Vinted seul | ❌ | ✅ (multi-sources) |
| Comparaison neuf vs occasion | ❌ | ✅ | ❌ | ❌ | ✅ |
| Compréhension du style (IA visuelle) | ❌ | ❌ | ❌ | Partielle | ✅ |
| Alertes rapides personnalisées | Basiques | ❌ | ✅ (rudimentaires) | ❌ | ✅ |
| Mobile-first Gen Z | ✅ | ❌ (desktop) | ❌ | ✅ | ✅ |
| Cross-plateformes | ❌ (silo) | ✅ | ❌ | — | ✅ |
| Modèle de revenu aligné | Commissions internes | Affiliation | Abonnement gris | Publicité | Affiliation + Premium |

---

## 3. Positionnement Stratégique

### 3.1 La formule
> **SwipeWear est le sniper de pépites : l'IA apprend ton style en te faisant swiper, puis chine à ta place sur tout le marché — occasion et neuf — et te présente chaque trouvaille du moins cher au plus cher, avant que quelqu'un d'autre ne la prenne.**

### 3.2 Les trois angles d'attaque marketing
1. **L'économie revendiquée :** "−75% sur la même veste" — le screenshot d'échelle de prix comme preuve sociale virale.
2. **La délégation :** "elle chine pendant que tu dors" — le luxe du personal shopper, démocratisé.
3. **L'écologie sans sermon :** le neuf affiché à côté de l'occasion à −70% convertit à la seconde main plus efficacement que n'importe quel discours — l'argument vert est un *résultat* du produit, pas son pitch.

### 3.3 Séquencement géographique et de niche
* **Phase 1 (lancement) :** France, niche "vintage et marques iconiques" (là où l'inventaire eBay/VC est fort et le matching exact faisable). Une niche dense et communautaire (TikTok #vintage #thrift) plutôt qu'un marché large et flou.
* **Phase 2 :** élargissement catégories (sneakers — communauté ultra-sensible au prix et à la rareté) puis marchés UK/DE où eBay et Depop sont puissants.

### 3.4 Ce que le projet ne cherche pas à être
* Pas un concurrent de Vinted (pas de transactions, pas de vendeurs).
* Pas un média d'inspiration (pas de contenu éditorial).
* Pas un outil de revendeur pro (le segment existe mais tire le produit vers le B2B — hors stratégie B2C assumée ; les revendeurs amateurs restent bienvenus comme power users du Premium).
