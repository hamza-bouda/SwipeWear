# 📋 Cahier des Charges — SwipeWear

**Nom du Projet :** SwipeWear  
**Version :** 1.0  
**Date :** 15 Juillet 2026  
**Auteur :** Développeur & Ingénieur IA (Solopreneur)  
**Statut :** Spécifications initiales  

---

## 1. Présentation Générale du Projet

### 1.1 Contexte
Le marché de la mode de seconde main connaît une croissance sans précédent en Europe, et particulièrement en France. Poussé par des préoccupations écologiques (lutte contre la fast-fashion, économie circulaire) et des contraintes économiques (inflation, baisse du pouvoir d'achat des jeunes), l'achat d'occasion est devenu un réflexe de consommation majeur. 

Cependant, chiner sur des plateformes comme Vinted ou Depop présente des irritants majeurs :
*   **Surcharge cognitive ("Choice Overload") :** Des millions d'articles sont en ligne, obligeant l'utilisateur à taper des mots-clés imprécis et à faire défiler des flux interminables de photos de qualité inégale.
*   **Recherche frustrante :** Les moteurs de recherche internes sont basés sur du texte brut, incapable de comprendre les subtilités esthétiques d'un style visuel (ex: "look grunge vintage", "esthétique minimaliste scandinave").
*   **Manque d'inspiration :** Contrairement à Pinterest qui inspire par des tenues complètes, les plateformes de seconde main vendent des pièces isolées. L'utilisateur a du mal à visualiser comment associer un vêtement.

### 1.2 Problématique
> Comment transformer l'expérience de recherche fastidieuse sur les plateformes de seconde main en une activité addictive, inspirante et fluide, permettant de découvrir des pièces uniques et d'associer des tenues complètes d'occasion en un clic ?

### 1.3 Vision du Projet
**SwipeWear** est une application mobile B2C mondiale qui transpose la mécanique de "swipe" de Tinder au catalogue de la mode de seconde main. Grâce à un moteur d'intelligence artificielle visuelle fonctionnant en arrière-plan, l'application apprend les goûts esthétiques de l'utilisateur à partir de ses interactions et lui propose :
1.  Un feed personnalisé d'articles isolés à swiper (Aimer / Rejeter).
2.  Des suggestions de tenues complètes (outfits) composées de pièces d'occasion réelles.
3.  Des redirections d'achat directes et transparentes vers les annonces d'origine (Vinted/Depop).

---

## 2. Périmètre du Projet

### 2.1 Dans le périmètre (In Scope) — Version 1 (MVP)
*   **Application Mobile native :** Interface développée avec React Native & Expo (compatible Android et iOS).
*   **Interface de Swipe :** Deck de cartes fluide avec gestes directionnels (Swipe Droite = J'aime, Swipe Gauche = Je n'aime pas, Swipe Haut = Ajouter à mon dressing virtuel).
*   **Moteur de Recommandation IA :** Extraction de caractéristiques d'images via le modèle CLIP et calcul de similarité vectorielle en base de données.
*   **Générateur de Tenues (Outfit Generator) :** Algorithme associant des articles compatibles (ex: un haut, un bas, une paire de chaussures) selon le profil de style de l'utilisateur.
*   **Dressing Virtuel :** Sauvegarde des articles aimés et des tenues enregistrées.
*   **Catalogue d'Annonces Initial :** Base de données pré-alimentée de 5 000 articles réels scrapés ou importés de Vinted/Depop.
*   **Redirection :** Lien direct et transparent vers l'annonce d'origine pour l'achat.

### 2.2 Hors périmètre (Out of Scope) — Version 1
*   **Système de transaction propre :** Pas de paiement direct dans l'application (l'utilisateur achète sur Vinted/Depop).
*   **Messagerie interne :** Pas de chat entre utilisateurs ou avec les vendeurs.
*   **Création de comptes vendeurs :** L'application n'est pas une marketplace de dépôt d'annonces, mais un agrégateur d'inspiration.

---

## 3. Public Cible & Personas

### 3.1 Profils cibles
Le public cible est mondial, jeune, connecté et habitué à l'usage d'applications mobiles intuitives :
*   **La Gen Z (16-25 ans) :** Consommateurs principaux de Vinted, accros à la mode, très sensibles aux prix et aux tendances éphémères de TikTok.
*   **Les Millennials (25-35 ans) :** Cherchant à s'habiller de manière plus écoresponsable, avec un pouvoir d'achat supérieur, privilégiant la qualité et la recherche de pièces vintage uniques.

### 3.2 Personas Types

#### Persona 1 : Chloé, 20 ans — L'étudiante éco-stylée
*   **Profil :** Étudiante en communication à Lyon, budget serré.
*   **Habitudes :** Passe 2 heures par jour sur TikTok et chine sur Vinted plusieurs fois par semaine.
*   **Frustration :** Trouve que chercher sur Vinted prend trop de temps. Elle finit souvent par acheter de la fast-fashion (Zara/Shein) par facilité de choix.
*   **Besoin :** Découvrir rapidement des vêtements vintage originaux et savoir comment les assembler en tenues sympas.

#### Persona 2 : Thomas, 28 ans — Le jeune actif "Eco-Conscient"
*   **Profil :** Développeur junior à Berlin.
*   **Habitudes :** Adepte du minimalisme, il achète uniquement de la seconde main de marques durables (Patagonia, Carhartt).
*   **Frustration :** N'aime pas négocier ni scroller des pages entières de vêtements mal décrits. Il recherche des coupes et matières spécifiques.
*   **Besoin :** Un flux d'inspiration visuel épuré qui lui propose directement des vêtements assortis à son vestiaire existant.

---

## 4. Exigences Fonctionnelles (MVP)

### 4.1 Onboarding & Profiling
*   **F01 - Inscription simplifiée :** Création de compte via Email, Apple ID ou Google Auth.
*   **F02 - Questionnaire d'Affinage (Cold Start) :** Sélection des catégories de vêtements recherchées (Homme/Femme/Mixte), des tailles et des styles d'inspiration (ex: Streetwear, Minimaliste, Vintage, Y2K) pour amorcer l'algorithme.

### 4.2 Module Swipe Deck
*   **F03 - Le Feed Vertical/Horizontal :** Affichage d'une carte à la fois avec une photo haute résolution du vêtement, le prix, la taille et la marque.
*   **F04 - Gestuelle intuitive :** 
    *   *Swipe Droite :* Enregistrer dans le "Dressing Virtuel" (Like).
    *   *Swipe Gauche :* Rejeter (Dislike - l'article ne s'affiche plus).
    *   *Swipe Haut / Double Tap :* Ajouter à la tenue en cours de création.
*   **F05 - Préchargement des cartes (Pre-fetching) :** Chargement asynchrone des 10 prochaines cartes pour garantir une fluidité parfaite sans temps d'attente pour l'utilisateur.

### 4.3 Moteur de Similarité & Recommandation
*   **F06 - Profil de Style Vectoriel :** Calcul et mise à jour en tâche de fond du vecteur de goût utilisateur basé sur ses swipes à droite.
*   **F07 - Recommandation prédictive :** Priorisation dans le feed des articles dont l'embedding visuel est le plus proche du vecteur de l'utilisateur.

### 4.4 Module Outfits (Générateur de Tenues)
*   **F08 - Composition automatique :** L'application propose des suggestions d'associations (ex: Veste + T-shirt + Pantalon) basées sur la cohérence visuelle des vecteurs d'images.
*   **F09 - Sauvegarde d'Outfits :** Enregistrement des combinaisons préférées de l'utilisateur.
*   **F10 - Lien de Redirection :** Bouton "Acheter sur Vinted/Depop" ouvrant directement l'application tierce sur la fiche de l'article pour finaliser la transaction.

---

## 5. Contraintes Techniques & Réglementaires

### 5.1 Contraintes Techniques (Solo Dev)
*   **Temps de réponse de l'IA :** Le calcul d'embedding CLIP et la recherche de similarité vectorielle dans la base de données PostgreSQL doivent prendre moins de 200 ms pour garantir la fluidité de l'application.
*   **Énergie et Batterie :** Le traitement lourd (recherche vectorielle, requêtes API) doit être centralisé sur le serveur FastAPI. L'application mobile doit être ultra-légère et se contenter d'afficher les médias.
*   **Limitation du Scraping :** Les scripts de collecte d'annonces (Vinted/Depop) doivent respecter des limites de requêtes par minute (rate limiting) et utiliser des proxies ou un catalogue importé pour éviter d'être bannis des plateformes sources.

### 5.2 Contraintes Réglementaires (RGPD & Souveraineté)
*   **Données Personnelles :** L'application ne collecte aucune donnée personnelle sensible. Seuls l'e-mail de connexion et le profil de style vectoriel (coordonnées mathématiques) sont stockés.
*   **Droit à l'effacement :** L'utilisateur peut supprimer son compte et l'intégralité de son historique d'interactions en un clic depuis les paramètres.
*   **Consentement et Cookies :** L'application n'utilisant aucun tracker publicitaire tiers pour le MVP, elle est exempte des bandeaux de consentement complexes, ce qui améliore l'UX.

---

## 6. Critères de Succès du MVP

| Métrique | Objectif de Réussite | Indicateur de Mesure |
| :--- | :--- | :--- |
| **Engagement** | > 100 swipes par session moyenne | Logs analytics d'interactions |
| **Rétention** | Rétention à Jours 30 > 25% | Cohortes d'utilisateurs actifs mensuels |
| **Traction** | Conversion vers Vinted > 12% | Clics sur le bouton "Acheter" / Total Swipes Droite |
| **Performance** | Temps d'affichage d'une carte < 1s | Monitoring API de latence |
