# 📊 Analyse des Risques — SwipeWear 2.0

Identification, cotation et mitigation des risques de la v2.0. **Note méthodologique :** la matrice v1.0 sous-cotait systématiquement les risques structurels (le scraping Vinted était noté "moyen" alors qu'il était fatal). Cette version applique une règle de cotation stricte : *un risque qui peut tuer le projet à lui seul est coté impact 5, quelle que soit la gêne que ça cause au dossier.*

---

## 1. Registre des Risques

### 1.1 Risques Produit / Marché (P)
* **P1 — La boucle "alerte" ne prend pas :** les utilisateurs swipent mais ne créent pas d'alertes ; la rétention retombe sur le divertissement seul → destin Mallzee/Grabble (churn massif après la nouveauté).
* **P2 — Gate 1 échoue :** le contenu TikTok ne génère ni vues ni liste d'attente ; la demande grand public pour le concept n'est pas démontrée.
* **P3 — Déception du cold start :** les premiers Drops sont médiocres avant que le profil de style ne converge (~30-50 swipes) ; churn J1-J3 élevé.
* **P4 — Notifications perçues comme du spam :** matching d'alertes imprécis → l'utilisateur désactive le push → le moteur de rétention meurt silencieusement.

### 1.2 Risques Techniques (T)
* **T1 — Erreurs de matching "même pièce" (V1.5) :** afficher comme identique un article qui ne l'est pas détruit la confiance dans le comparateur.
* **T2 — Annonces mortes dans l'échelle de prix :** les pièces d'occasion se vendent en heures ; des liens morts frustrent et décrédibilisent.
* **T3 — Qualité/hétérogénéité des flux sources :** tailles non normalisées, catégories incohérentes, doublons inter-plateformes → expérience dégradée.
* **T4 — Hotlinking d'images refusé par une source :** images cassées dans le feed.

### 1.3 Risques Business / Externes (B)
* **B1 — Dégradation des programmes d'affiliation :** baisse des commissions, durcissement des quotas API, exclusion du programme.
* **B2 — Copie par un acteur financé** (Faircado pivotant mobile, startup nouvelle, feature Vinted).
* **B3 — Fermeture de la surveillance Vinted user-initiated** (durcissement anti-bot).
* **B4 — Épuisement des fondateurs :** 20h/semaine sur 12 mois en parallèle des études ; risque d'abandon avant le signal de traction.

### 1.4 Risques Juridiques (J)
* **J1 — Contestation de la surveillance Vinted** (CGU) — périmètre réduit vs v1.0 mais non nul.
* **J2 — Non-conformité RGPD / transparence affiliation** (mentions "lien partenaire", consentements push).

---

## 2. Matrice Probabilité / Impact

| ID | Risque | Prob. (1-5) | Impact (1-5) | Criticité | Tendance vs v1.0 |
| :--- | :--- | :---: | :---: | :---: | :--- |
| **P1** | Boucle alerte ne prend pas | 3 | 5 | **15 — ÉLEVÉ** | Nouveau — LE risque central |
| **P4** | Push perçu comme spam | 3 | 4 | **12 — Élevé** | Nouveau |
| **T1** | Erreur matching "même pièce" | 3 | 4 | **12 — Élevé** | Nouveau (V1.5) |
| **B2** | Copie par acteur financé | 3 | 4 | **12 — Élevé** | ↑ (le concept validé attire) |
| **P2** | Gate 1 échoue | 4 | 3 | **12 — Élevé*** | *Impact limité par design : échec à coût quasi nul, avant tout code |
| **T2** | Annonces mortes | 4 | 3 | **12 — Élevé** | = |
| **B4** | Épuisement fondateurs | 3 | 4 | **12 — Élevé** | Nouveau (honnêteté) |
| **P3** | Déception cold start | 3 | 3 | **9 — Moyen** | = |
| **T3** | Hétérogénéité des flux | 4 | 2 | **8 — Moyen** | Nouveau |
| **B1** | Dégradation affiliation | 2 | 4 | **8 — Moyen** | Remplace le risque scraping |
| **B3** | Fermeture watcher Vinted | 4 | 2 | **8 — Moyen** | ↓↓ (impact 5→2 : le produit y survit par design) |
| **T4** | Hotlink refusé | 3 | 2 | **6 — Faible** | = |
| **J1** | Contestation Vinted | 2 | 2 | **4 — Faible** | ↓↓ (périmètre user-initiated, coupable) |
| **J2** | RGPD / transparence | 1 | 4 | **4 — Faible** | = |

**Lecture :** le profil de risque a changé de nature. La v1.0 concentrait le risque sur des facteurs **externes et subis** (blocage Vinted, procès). La v2.0 le concentre sur des facteurs **comportementaux et mesurables** (P1, P4) — c'est-à-dire testables tôt, à faible coût, par les Gates.

---

## 3. Plans de Mitigation

### 3.1 P1 — La boucle alerte ne prend pas (criticité 15)
1. **Mesurer avant d'investir :** Gate 2 (beta 100 utilisateurs) avec seuil explicite — ≥30% créent ≥2 alertes et reviennent en semaine 2. Sous 15% : pivot vers comparateur pur ou arrêt. Le risque maximal est ainsi plafonné à ~3 mois de travail.
2. **Réduire la friction de création d'alerte à un geste :** le Swipe Haut crée une alerte pré-remplie (style de la carte + taille du profil + budget médian). Pas de formulaire.
3. **Éduquer par la preuve :** après chaque pépite ratée ("vendue il y a 2h"), proposer : *"Crée une alerte pour ne plus la rater."* Le regret est le meilleur vendeur d'alertes.

### 3.2 P4 — Push spam (12)
1. Seuils stricts : aucune notification sous 90% de similarité + taille exacte + budget respecté.
2. Plafond gratuit : max 1 notification/jour hors Drop (le Premium lève le plafond — l'alignement est vertueux : payer = en recevoir plus, donc les seuils gratuits restent exigeants).
3. Kill-switch par alerte + réglage de fréquence dès la V1 (pas "plus tard").

### 3.3 T1 — Matching "même pièce" (12)
1. Architecture à deux étages étiquetée honnêtement : "🎯 La même pièce" (uniquement catalogue de référence vérifié, seuil de confiance élevé) vs "👀 Dans le même style". **Sous le seuil → rétrogradation automatique en "même style". Jamais de fausse promesse.**
2. Bouton "ce n'est pas la même pièce" → retrait immédiat + correction du catalogue de référence.
3. Déploiement incrémental : 100 produits iconiques d'abord, extension seulement quand la précision mesurée > 95%.

### 3.4 T2 — Annonces mortes (12)
1. Vérification différée par worker (priorité aux articles les plus servis dans les feeds/échelles).
2. Tri du feed par fraîcheur : un article de moins de 24h a une probabilité de disponibilité élevée — le Drop ne sert que du < 48h.
3. Bouton communautaire "déjà vendu" (retrait immédiat + signal au worker).
4. Affichage de l'âge de l'annonce ("vue il y a 3h") : l'utilisateur calibre lui-même sa confiance.

### 3.5 B2 — Copie (12)
1. Creuser les trois actifs incopiables à court terme : taste graph (volume de swipes), catalogue de référence (curation manuelle), audience TikTok (marque).
2. Vitesse : lancement France en 5 mois, pas de perfectionnisme — le coût d'un trimestre de retard est supérieur au coût de toute dette technique du MVP.
3. Ne pas publier la méthode de matching (le "comment" reste privé, le build in public montre le produit, pas les entrailles).

### 3.6 B4 — Épuisement (12)
1. Gates = points de sortie honorables prédéfinis : on ne s'épuise pas sur un projet que les chiffres ont invalidé.
2. Rythme soutenable planifié (pauses examens intégrées, doc 08) plutôt que sprints héroïques suivis d'abandon.
3. Règle des rôles : chacun un périmètre clair (produit / croissance) — les projets à deux meurent plus souvent de friction floue que de manque de talent.

### 3.7 B1 / B3 / T3 / T4 — Dépendances externes
* **B1 :** aucune source > 40% du catalogue ; métadonnées en cache local ; le Premium (revenu indépendant des sources) couvre les coûts fixes seul dès ~1 000 MAU.
* **B3 :** module watcher isolé, coupable en une variable d'environnement, sans impact sur catalogue/revenus/échelle de prix. Communication prévue aux utilisateurs le cas échéant.
* **T3 :** couche de normalisation centralisée (tailles, états, catégories) avec tests unitaires par source ; toute nouvelle source passe par elle.
* **T4 :** fallback proxy de miniatures avec cache court ; suppression de la source du feed si son CDN bloque durablement.

### 3.8 J1 / J2 — Juridique
* **J1 :** fréquence de vérification plafonnée par utilisateur et par alerte (comportement assimilable à un utilisateur assidu) ; aucune constitution de base de données Vinted (seules les correspondances aux alertes de l'utilisateur transitent) ; arrêt du module sans discussion en cas de mise en demeure — il est périphérique par design.
* **J2 :** mentions "lien partenaire" sur chaque lien affilié ; opt-in push explicite ; registre de traitement minimal (email haché, tailles, vecteur de style) ; suppression de compte en un tap.

---

## 4. Risques résiduels acceptés (en connaissance de cause)

1. **Le produit peut être copié.** Accepté : la défense est la vitesse et les actifs cumulatifs, pas un moat initial illusoire.
2. **L'inventaire occasion hors Vinted est plus faible en entrée de gamme.** Accepté : positionnement de lancement "marques & vintage", où eBay/VC sont forts.
3. **Le succès dépend de la traction TikTok, partiellement aléatoire.** Accepté et borné : 8 vidéos testées sur 2 semaines avant toute ligne de code (Gate 1) ; l'aléa est acheté au prix le plus bas possible.
