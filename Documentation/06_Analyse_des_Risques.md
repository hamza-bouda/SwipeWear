# 📊 Analyse des Risques — SwipeWear

Ce document identifie les risques techniques, juridiques et commerciaux du projet **SwipeWear**, établit une matrice d'impact/probabilité et propose des plans de mitigation précis.

---

## 1. Identification et Classification des Risques

### 1.1 Risques Techniques (T)
*   **T1 - Blocage technique du scraping (IP Ban) :** Vinted/Depop bloquent l'aspiration des annonces via Cloudflare ou des limites de requêtes (rate limits).
*   **T2 - Problème de performance de l'IA sur serveur low-cost :** Latence trop élevée (> 500ms) pour le calcul d'embeddings CLIP sur CPU de base, ruinant la fluidité du swipe.
*   **T3 - Liens d'annonces morts (Articles vendus) :** Redirection de l'utilisateur vers des articles déjà achetés par d'autres utilisateurs sur Vinted.

### 1.2 Risques Juridiques (J)
*   **J1 - Action légale des plateformes sources (Droits de propriété intellectuelle) :** Poursuites ou mises en demeure par Vinted/Depop pour aspiration de données ou violation de leurs conditions d'utilisation.
*   **J2 - Non-conformité RGPD (Profilage) :** Mauvaise gestion des données utilisateur ou non-respect du droit à l'effacement de l'historique de style.

### 1.3 Risques Commerciaux (C)
*   **C1 - Taux de désinstallation élevé (User Churn) :** L'utilisateur s'amuse à swiper les premiers jours mais se lasse et supprime l'application par manque de renouvellement de valeur.
*   **C2 - Coût d'infrastructure supérieur aux revenus :** Les abonnements premium ne couvrent pas les serveurs si le volume d'utilisateurs gratuits est trop grand.

---

## 2. Matrice Probabilité / Impact

| ID | Risque | Probabilité (1-5) | Impact (1-5) | Criticité (P x I) |
| :--- | :--- | :---: | :---: | :---: |
| **T1** | Blocage technique du scraping | 4 | 3 | **12 (Moyen)** |
| **T2** | Latence élevée de l'IA (CPU) | 3 | 4 | **12 (Moyen)** |
| **T3** | Liens d'annonces morts | 5 | 2 | **10 (Moyen)** |
| **J1** | Actions légales de Vinted/Depop | 2 | 5 | **10 (Moyen)** |
| **J2** | Non-conformité RGPD | 1 | 5 | **5 (Faible)** |
| **C1** | Churn élevé (Lassitude) | 4 | 4 | **16 (Élevé)** |
| **C2** | Coût infrastructure trop élevé | 2 | 3 | **6 (Faible)** |

---

## 3. Plan de Mitigation et Stratégies de Secours

### 3.1 Risques Techniques
*   **Mitigation T1 (Blocage Scraping) :** 
    1.  Limiter la fréquence des requêtes en arrière-plan.
    2.  Utiliser un proxy résidentiel rotatif.
    3.  *Plan B :* Permettre aux utilisateurs d'importer eux-mêmes des liens d'annonces qu'ils trouvent sympas (crowdsourcing du catalogue) ou utiliser des flux RSS d'annonces publiques si disponibles.
*   **Mitigation T2 (Latence IA) :** 
    1.  Utiliser le modèle de vision CLIP le plus léger (`clip-ViT-B-32`).
    2.  Mettre en cache les embeddings générés pour éviter de recalculer deux fois la même image.
    3.  Préchager les 10 prochaines cartes (Pre-fetching) côté client pendant que l'utilisateur regarde la carte active.
*   **Mitigation T3 (Liens morts) :**
    1.  Mettre en place un script de nettoyage en tâche de fond (cron job) qui vérifie périodiquement si les articles en base sont toujours en ligne.
    2.  Ajouter un bouton "Signaler comme vendu" dans l'application pour impliquer la communauté.

### 3.2 Risques Juridiques
*   **Mitigation J1 (Actions Vinted/Depop) :**
    1.  Ne pas héberger ni copier les images sur les serveurs de SwipeWear (stocker uniquement les URLs d'origine).
    2.  Ne pas masquer la source : la redirection doit ouvrir directement l'application Vinted officielle sur la bonne fiche produit. SwipeWear agit comme un apporteur d'audience et de trafic qualifié gratuit, réduisant leur intérêt à engager des poursuites.
    3.  Ajuster les conditions générales de vente pour préciser que SwipeWear est un moteur de recherche visuel indépendant.
*   **Mitigation J2 (RGPD) :**
    1.  Ne stocker aucune donnée sensible. L'e-mail peut être haché.
    2.  Le profil de style vectoriel (une suite de 512 nombres décimaux) est anonyme par nature.
    3.  Bouton de suppression instantanée de compte et d'historique en base dans les réglages de l'application.

### 3.3 Risques Commerciaux
*   **Mitigation C1 (Churn élevé) :**
    1.  **Gamification active :** Intégrer un système de streaks de style, de défis de création de looks hebdomadaires ou de votes communautaires sur les meilleures tenues.
    2.  **Notifications push intelligentes :** Alerter l'utilisateur lorsqu'une nouvelle pièce unique correspondant à 95% à son style vectoriel vient d'être indexée dans sa taille.
*   **Mitigation C2 (Coût serveurs) :**
    1.  Architecture backend serverless stateless : payer uniquement pour les requêtes actives.
    2.  Limiter le nombre de requêtes d'outfits gratuites par utilisateur pour forcer la conversion premium ou réduire la charge serveur.
    3.  Limiter la taille de la base de données active à 10 000 articles récents (supprimer automatiquement les anciennes annonces).
