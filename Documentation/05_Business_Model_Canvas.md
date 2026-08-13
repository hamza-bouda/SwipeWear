# 📊 Business Model Canvas — SwipeWear 2.0

Les 9 blocs stratégiques du modèle d'affaires v2.0. Changement central par rapport à la v1.0 : le revenu ne repose plus sur un abonnement de confort à 2,99€, mais sur **deux moteurs alignés avec la valeur créée** — l'affiliation (l'app gagne quand l'utilisateur économise) et le Premium à 4,99€ (l'app vend la priorité sur des pièces uniques).

---

```
┌────────────────────────┬────────────────────────┬────────────────────────┬────────────────────────┬────────────────────────┐
│   Partenaires Clés     │    Activités Clés      │ Proposition de Valeur  │   Relations Clients    │  Segments de Clientèle │
│                        │                        │                        │                        │                        │
│ - eBay Partner Network │ - Ingestion & normali- │ « L'IA qui chine pour  │ - Onboarding < 60s     │ - Gen Z chineuse       │
│ - Awin / CJ (Zalando,  │   sation multi-sources │   toi 24h/24 »         │ - Drop quotidien 19h   │   (16-25, budget serré)│
│   ASOS, Vestiaire Col.)│ - Moteur IA de style   │                        │   (rituel)             │ - Millennials acheteurs│
│ - Etsy Affiliates      │   (embeddings CLIP)    │ 1. Ne rate plus jamais │ - Notifications à      │   rationnels (25-35)   │
│ - Hébergeur EU         │ - Moteur d'alertes     │    ta pépite (alertes  │   forte valeur (pas    │ - Chasseurs de marques │
│   (Scaleway/Railway)   │   temps réel           │    style+taille+budget)│   de spam)             │   iconiques & vintage  │
│ - Créateurs TikTok     │ - Contenu TikTok       │ 2. Ne surpaie plus     │ - Build in public      │ - (secondaire) reven-  │
│   mode/vintage         │   (3-5/semaine)        │    jamais (échelle de  │   TikTok               │   deurs amateurs =     │
│                        │ - Curation catalogue   │    prix neuf/occasion  │                        │   power users Premium  │
│                        │   de référence         │    du - cher au + cher)│                        │                        │
├────────────────────────┼────────────────────────┤ 3. Zéro saisie : l'IA  ├────────────────────────┤                        │
│    Ressources Clés     │        Canaux          │    comprend ton style  │                        │                        │
│                        │                        │    en te regardant     │                        │                        │
│ - Taste graph          │ - App Store /          │    swiper              │                        │                        │
│   (propriétaire)       │   Google Play          │                        │                        │                        │
│ - Catalogue de réfé-   │ - TikTok / Reels /     │                        │                        │                        │
│   rence produits       │   Shorts (organique)   │                        │                        │                        │
│   iconiques            │ - Partage in-app       │                        │                        │                        │
│ - Compétences dev+IA   │   (cartes d'économie)  │                        │                        │                        │
│ - CLIP + pgvector      │                        │                        │                        │                        │
├────────────────────────┴────────────────────────┴────────────────────────┴────────────────────────┴────────────────────────┤
│                    Structure de Coûts                        │                 Sources de Revenus                           │
│                                                              │                                                              │
│ - Infra (API, BDD, workers) : 35-50€/mois                    │ 1. AFFILIATION : 1-4% occasion (eBay/Etsy/VC),               │
│ - Licences stores : ~110€/an                                 │    5-10% neuf (Zalando/ASOS via Awin/CJ)                     │
│ - Marketing : 0€ (100% organique par choix)                  │ 2. PREMIUM 4,99€/mois ou 39,99€/an :                         │
│ - Temps fondateurs : ~20h/sem (le vrai coût)                 │    alertes illimitées + instantanées + multi-tailles         │
│                                                              │ 3. (Futur) Insights tendances anonymisés B2B                 │
└──────────────────────────────────────────────────────────────┴──────────────────────────────────────────────────────────────┘
```

---

## 1. Description Détaillée des 9 Blocs

### 1.1 Segments de Clientèle
* **Cœur : la Gen Z chineuse (16-25 ans).** Native Vinted, culture du fit check et de la bonne affaire revendiquée. Sensible au prix, insensible aux sermons écologiques, très sensible au statut de "celle/celui qui trouve les pépites".
* **Millennials rationnels (25-35 ans).** Moins de temps, plus de budget : la délégation ("l'app chine pour moi") et la garantie du juste prix sont leurs déclencheurs. Meilleur taux de conversion Premium attendu.
* **Segment secondaire assumé : revendeurs amateurs.** Non ciblés par le marketing, mais convertisseurs Premium immédiats (ils paient déjà des outils d'alerte rudimentaires). Ils stress-testent le moteur d'alertes.

### 1.2 Proposition de Valeur
Trois promesses, une hiérarchie claire :
1. **"Ne rate plus jamais ta pépite"** — le moteur d'alertes exploite la seule vraie rareté du marché : chaque pièce d'occasion est unique et disparaît en heures. C'est la promesse de rétention.
2. **"Ne surpaie plus jamais"** — l'échelle de prix (même style / même pièce, occasion et neuf, triée du moins cher au plus cher) transforme chaque coup de cœur en décision d'achat éclairée. C'est la promesse d'acquisition (screenshot viral : "−75%").
3. **"Zéro effort"** — pas de mots-clés, pas de filtres à configurer : l'IA apprend le style en regardant swiper. C'est la promesse différenciante face aux alertes Vinted natives et aux outils de snipe.

### 1.3 Canaux
* **TikTok/Reels organique (canal principal) :** formats éprouvés — "l'IA m'habille pour 30€", "même pièce : Zara 89€ vs trouvée 22€", build in public. Objectif : 3-5 vidéos/semaine, responsabilité nominative (ingénieur B).
* **Boucle de partage in-app :** chaque échelle de prix génère une carte d'économie partageable — l'utilisateur fait le marketing en se vantant de sa trouvaille.
* **Stores :** ASO sur les requêtes "vinted alerte", "seconde main", "comparateur vêtements".

### 1.4 Relations Clients
* **Le Drop quotidien à 19h comme rituel :** mécanique Wordle/BeReal — rare, attendu, épuisable. L'app ne demande pas du temps infini, elle donne un rendez-vous.
* **Notifications = service, jamais spam :** une alerte ne part que si (style ≥ seuil) ∧ (taille exacte) ∧ (budget respecté). La confiance dans le push est l'actif de rétention n°1 ; elle se perd en trois notifications médiocres.
* **Build in public :** la communauté TikTok co-construit (votes de features, accès beta) — acquisition et fidélisation confondues.

### 1.5 Sources de Revenus
* **Affiliation (moteur de volume) :** rémunère l'apport d'affaires sans friction utilisateur. Le neuf (5-10%) subventionne la mission occasion : ironiquement, chaque achat neuf via l'échelle de prix finance l'outil qui convertit à la seconde main. Transparence "lien partenaire" systématique.
* **Premium 4,99€/mois / 39,99€/an (moteur de marge) :** vend la **priorité**, pas le confort — alertes illimitées (vs 1), notification instantanée (vs délai 30 min), multi-tailles, filtres marques. Sur des pièces uniques, 30 minutes de retard = pièce perdue : le gratuit démontre la valeur, le Premium la débloque. Conversion cible : 2-4% des MAU.
* **Futur (année 2+) :** rapports de tendances anonymisés issus du taste graph (quelles pièces/styles montent, à quel prix) pour marques et friperies — optionnel, jamais au prix d'une revente de données individuelles.

### 1.6 Ressources Clés
* **Le taste graph (propriétaire) :** millions de jugements esthétiques horodatés — l'actif qui se creuse avec l'usage et que ni Vinted ni un copieur ne possèdent au jour 1.
* **Le catalogue de référence des produits iconiques (propriétaire) :** 100-200 fiches vérifiées permettant le matching "même pièce" — lent à construire, donc lent à copier.
* **Compétences fondatrices :** full-stack + IA — le produit est exactement à leur intersection.
* **Briques ouvertes :** CLIP, pgvector, Expo — coût nul, maturité élevée.

### 1.7 Activités Clés
1. Ingestion et normalisation multi-sources (la qualité du catalogue EST le produit).
2. Amélioration continue du profil de style et du matching d'alertes (précision = confiance = rétention).
3. Production de contenu TikTok (la distribution est une activité cœur, pas du marketing d'appoint).
4. Curation du catalogue de référence (V1.5).

### 1.8 Partenaires Clés
* **Réseaux d'affiliation (eBay Partner Network, Awin, CJ, Etsy Affiliates) :** fournisseurs d'inventaire légal ET payeurs. Leur intérêt est structurellement aligné : ils existent pour acheter du trafic qualifié.
* **Hébergeur européen** (RGPD, latence, coût).
* **Micro-créateurs mode/vintage TikTok :** échange visibilité contre accès anticipé — pas de budget influence payant.
* *(Notablement absent : Vinted. Par conception, aucun partenariat n'est requis — et aucune dépendance n'est tolérée.)*

### 1.9 Structure de Coûts
* **Cash : < 60€/mois tout compris.** Le point mort en coûts directs est atteint vers 350 MAU (voir doc 04 §3.1).
* **Le vrai coût est le temps fondateur (~20h/sem à deux)** — d'où les gates de validation qui protègent cette ressource : aucun mois de développement n'est dépensé sans signal de demande préalable.

---

## 2. Cohérence du modèle (test de résistance)

| Question test | Réponse v2.0 |
| :--- | :--- |
| Qui paie, pourquoi, et est-ce prouvé ? | Les plateformes paient l'apport d'affaires (programmes publics) ; les utilisateurs paient la priorité (prouvé par les outils de snipe existants à 10-30€/mois). |
| Que se passe-t-il si Vinted bloque tout ? | Rien de critique : Vinted n'est ni dans le catalogue, ni dans les revenus (module isolé F12). |
| Que se passe-t-il si un concurrent copie ? | Il part sans taste graph, sans catalogue de référence, sans audience TikTok. La fenêtre de 12 mois sert à creuser ces trois écarts. |
| Le modèle survit-il à 2 000 MAU seulement ? | Oui financièrement (~320€/mois > coûts), non en ambition — c'est le seuil de décision "continuer/pivoter" de l'année 1. |
| Où le modèle casse-t-il ? | Si les utilisateurs ne créent pas d'alertes (la rétention retombe sur le swipe seul → destin Mallzee). Mesuré par Gate 2 avant tout investissement lourd. |
