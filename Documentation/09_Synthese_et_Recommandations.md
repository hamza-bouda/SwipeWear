# 📊 Synthèse et Recommandations — SwipeWear 2.0

Résumé exécutif du projet dans sa version 2.0, évaluation chiffrée, et plan d'action immédiat. Ce document remplace la synthèse v1.0, invalidée par l'analyse critique (dépendance au scraping Vinted, absence de modèle de revenu, estimation d'effort sous-évaluée d'un facteur 3-5).

---

## 1. Résumé Exécutif

**SwipeWear** est une application mobile B2C : un **sniper de pépites personnel** pour la mode. L'utilisateur entraîne une IA visuelle en swipant des vêtements ; l'application chine ensuite pour lui 24h/24 sur l'ensemble du marché — **occasion et neuf** — et lui présente chaque trouvaille sous forme d'**échelle de prix triée du moins cher au plus cher**, puis le **notifie avant les autres** quand la pièce correspondant à son style, sa taille et son budget apparaît.

Le projet est porté par 2 étudiants ingénieurs (full-stack + IA), ~20 h/semaine cumulées, coûts d'exploitation < 50 €/mois.

### La thèse en trois points
1. **La douleur est réelle et solvable :** sur le marché de l'occasion, chaque pièce est unique et disparaît en heures — rater la pépite et surpayer sont des douleurs vécues, et la disposition à payer pour la *vitesse* est déjà prouvée (outils d'alerte Vinted à 10-30 €/mois chez les revendeurs). SwipeWear en est la version grand public, mobile, légale et pilotée par IA de style.
2. **Le modèle économique est aligné et double :** affiliation (1-4% occasion, **5-10% neuf** via eBay/Etsy/Awin/CJ — l'app gagne quand l'utilisateur économise) + Premium 4,99 €/mois vendant la **priorité** (alertes illimitées et instantanées vs 1 alerte différée de 30 min). Point mort infra : ~350 MAU.
3. **La position est incopiables par les géants :** comparer les prix *entre* plateformes concurrentes (Vinted ne montrera jamais eBay ; Zalando ne montrera jamais l'occasion) est structurellement réservé à un acteur neutre. Les actifs défensifs se cumulent avec l'usage : taste graph (jugements esthétiques propriétaires) et catalogue de référence des produits iconiques.

### Ce que la v2.0 a corrigé de la v1.0

| | v1.0 ("Tinder de la fripe") | v2.0 ("Sniper de pépites") |
| :--- | :--- | :--- |
| Données | Scraping massif Vinted (illégal, instable) | API + flux d'affiliation officiels ; Vinted réduit à une surveillance user-initiated, isolée et coupable |
| Rétention | Divertissement swipe (destin Mallzee/Grabble) | Alertes à FOMO réel + Drop quotidien rituel ; le swipe n'est plus que l'entraînement |
| Revenu | 2,99 €/mois improbable, 0 € d'affiliation | Affiliation neuf/occasion + Premium "priorité" 4,99 € |
| Feature IA phare | Tenues par similarité (conceptuellement erroné) | Échelle de prix (similarité bien employée) ; tenues reportées V2 en mode *compatibilité* |
| Effort | "60 h" (irréaliste) | 175-235 h à deux, 6 mois avec gates |
| **Score d'analyse** | **48/100** | **73/100 sur dossier — 78-80 si Gates 1 et 2 passent** |

---

## 2. Évaluation chiffrée (grille d'analyse critique)

| Dimension | Score | Justification synthétique |
| :--- | :---: | :--- |
| Valeur du problème | **20/25** | Douleur urgente (pièces uniques périssables) + promesse universelle ("ne surpaie plus jamais") ; disposition à payer déjà observée sur le marché. |
| Faisabilité | **19/25** | Sources légales et alignées économiquement ; stack éprouvée sans GPU ; 175-235 h tenables à deux ; reste la difficulté du matching exact (bornée par l'architecture à deux étages). |
| Avantage compétitif | **17/25** | Neutralité multi-plateformes incopiables par les incumbents + taste graph + catalogue de référence ; mais surface copiable par un acteur financé — fenêtre de 12 mois. |
| Timing marché | **17/25** | Seconde main : +15-18%/an, lois anti-fast-fashion, inflation ; case "comparateur neuf/occasion mobile avec alertes" encore vide en Europe (Faircado/Beni sont desktop). |
| **TOTAL** | **73/100** | **GO conditionnel — les conditions sont les Gates 1 et 2, à coût quasi nul.** |

### Verdict : **GO AVEC CONDITIONS**
* **Condition 1 (Gate 1, semaines 1-2, ~0 €) :** la demande existe — ≥ 300 inscrits en liste d'attente ou 1 vidéo > 50K vues, avant toute ligne de code produit.
* **Condition 2 (Gate 2, mois 3, ~200 h investies max) :** la boucle de rétention existe — ≥ 30% des 100 beta-testeurs créent ≥ 2 alertes et reviennent en semaine 2.
* Si les deux passent : le projet vaut 78-80/100 et mérite l'année. Si l'une échoue : pivot ou arrêt avec un coût total borné à l'avance — c'est le marché qui décide, pas l'attachement au projet.

### Les 3 risques principaux (et leur plafonnement)
1. **P1 — Les utilisateurs ne créent pas d'alertes** (criticité 15/25) → plafonné par Gate 2 ; friction réduite à un geste (Swipe Haut = alerte pré-remplie).
2. **T1 — Erreur de matching "même pièce"** (12/25) → architecture à deux étages honnêtement étiquetée ; jamais d'affirmation "identique" sous le seuil de confiance.
3. **B2 — Copie par un acteur financé** (12/25) → vitesse d'exécution + actifs cumulatifs (taste graph, catalogue, audience TikTok).

---

## 3. Recommandations Stratégiques

1. **Valider avant de construire — et s'y tenir.** La meilleure décision de la v1.0 (prototype factice + TikTok avant le backend) reste la règle d'or de la v2.0, désormais outillée de seuils chiffrés. Aucune exception : pas une ligne de backend avant Gate 1.
2. **Protéger la confiance comme l'actif n°1.** Un comparateur vit de sa crédibilité : étiquetage honnête ("la même pièce" vs "le même style"), âge des annonces affiché, mention "lien partenaire", notifications rares et précises. Chaque raccourci sur la confiance coûte plus cher que le retard qu'il évite.
3. **Respecter le principe "survivre sans Vinted".** Aucun composant critique (catalogue, échelle, drop, revenus) ne doit dépendre de Vinted — c'est la leçon centrale de l'échec conceptuel de la v1.0, gravée dans l'architecture (module watcher isolé et coupable).
4. **Traiter la distribution comme la moitié du produit.** En B2C sans budget, TikTok n'est pas du marketing d'appoint : 3-5 vidéos/semaine, responsable nominatif (ingénieur B), formats mesurés. Si le contenu ne prend pas en Phase 0, la publicité payante ne sauverait rien — c'est précisément ce que Gate 1 teste.
5. **Discipline de scope absolue.** Tenues, garde-robe numérisée, B2B : backlog V2, sans discussion avant la traction. Les projets à deux, à 20 h/semaine, meurent de dispersion avant de mourir de concurrence.

---

## 4. Plan d'Action Immédiat (Semaines 1 & 2 — coût ~0 €)

### 🚀 Jour 1-2 — Mise en place
* Dépôt Git : `/landing`, `/maquettes`, `/contenu`, `/documentation` (ce dossier).
* Répartition écrite des rôles : A = maquettes + landing ; B = contenu TikTok + tracking.
* Lancer les inscriptions aux programmes d'affiliation (eBay Partner Network, Awin, CJ, Etsy) — les délais d'approbation courent pendant la validation.

### 🚀 Jour 3-6 — Les artefacts de validation
* 5-6 écrans Figma crédibles : swipe, **échelle de prix avec un vrai exemple** ("Carhartt Detroit : 24 € occasion → 119 € neuf, −80%"), notification "🎯 Ta pépite".
* Landing page : promesse ("L'IA qui chine pour toi 24h/24"), 3 écrans, champ email, compteur d'inscrits. Analytics branchées.

### 🚀 Jour 7-14 — Le test de marché
* 8 vidéos TikTok/Reels, 4 hooks différents :
    1. *"Je suis étudiant et je code une IA qui chine sur tout internet à ta place — voilà à quoi elle ressemble."* (build in public)
    2. *"Cette veste coûte 89 € chez Zara. Mon app l'a trouvée à 22 €."* (échelle de prix)
    3. *"Tu rates les pépites Vinted parce que tu arrives trop tard ? Regarde ça."* (alerte/FOMO)
    4. *"J'ai laissé une IA apprendre mon style en 30 swipes."* (magie IA)
* Mesure quotidienne : vues, CTR bio, inscriptions. Doubler ce qui marche, tuer ce qui ne marche pas.

### 🚀 Jour 15 — Réunion Gate 1
* Chiffres sur la table, seuils écrits d'avance (≥ 300 inscrits ou 1 vidéo > 50K vues), décision en une heure : **GO construction / itérer 2 semaines / pivot**.
* Quelle que soit l'issue : le coût total de l'apprentissage aura été de deux semaines et 0 €.

---

## 5. Conclusion

La v1.0 était un beau dossier construit sur un défaut fatal : un produit de divertissement bâti sur les données d'un tiers, sans modèle de revenu. La v2.0 conserve ce qui était juste (le swipe comme interface, l'IA de style invisible, l'asset-light, la validation TikTok-first) et corrige ce qui condamnait le projet : **les données sont désormais légales et rémunératrices, la rétention repose sur une urgence réelle plutôt que sur l'amusement, et le prix vendu est celui de la priorité — la seule chose qui compte sur un marché de pièces uniques.**

Le projet vaut 73/100 sur dossier. Les 5 à 7 points restants ne s'écrivent pas dans un document : ils se gagnent en deux semaines de TikTok et trois mois de beta. **Prochaine étape : Jour 1 du plan d'action.**
