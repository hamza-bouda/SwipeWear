# 📅 Planning et Roadmap — SwipeWear

Ce document définit la planification macroscopique et le calendrier de développement de **SwipeWear** sur une période de 4 mois, structurée de manière réaliste pour concilier le projet et les études supérieures.

---

## 1. Calendrier des Jalons (Milestones)

Le projet est découpé en 4 jalons mensuels de 40 heures de travail chacun (environ 10 heures par semaine, concentrées sur le week-end et les soirées de semaine).

```
JALON 1 (Mois 1) : Base de Données & Pipeline IA (Backend)
├─ Setup PostgreSQL + extension pgvector
├─ Script d'extraction d'images & Ingestion initiale (5000 items)
└─ Pipeline d'embeddings CLIP sur CPU FastAPI
│
JALON 2 (Mois 2) : Application Mobile & Swipe UI (Frontend)
├─ Init React Native / Expo
├─ Intégration Swipe Deck (react-native-deck-swiper)
└─ Connexion API (Auth + Réception des cartes)
│
JALON 3 (Mois 3) : Recommandations IA & Dressing (Intégration)
├─ Algorithme de moyenne vectorielle dynamique sur FastAPI
├─ Module de composition de tenues (Haut + Bas + Chaussures)
└─ Lancement Beta Privée (TestFlight / Google Play Beta)
│
JALON 4 (Mois 4) : Acquisition Organique & Lancement Public
├─ Création de contenu "Build in Public" sur TikTok/Reels
├─ Suivi des KPIs de conversion & corrections de bugs
└─ Lancement sur les App Stores
```

---

## 2. Détail des Jalons

### 📅 Mois 1 : Pipeline de Données et IA (Backend)
*   **Objectif :** Disposer d'une API capable de renvoyer des articles similaires à partir d'un vecteur d'entrée.
*   **Tâches :**
    *   Installation de PostgreSQL avec l'extension `pgvector` sur un serveur de développement local.
    *   Écriture du script Python d'aspiration d'annonces de mode (Vinted/Depop) pour constituer la base de données initiale (5 000 articles avec marque, taille, prix et URL de l'image).
    *   Déploiement du modèle CLIP (`clip-ViT-B-32`) sur le serveur FastAPI.
    *   Génération des embeddings pour les 5 000 images et indexation HNSW dans PostgreSQL.

### 📅 Mois 2 : Interface de Swipe Mobile (Frontend)
*   **Objectif :** Obtenir une application mobile fluide sur simulateur et appareil physique.
*   **Tâches :**
    *   Initialisation du projet avec Expo CLI.
    *   Création de l'interface de swipe des cartes (animations, réactivité tactile).
    *   Développement des pages secondaires : Dressing Virtuel et Profil Utilisateur.
    *   Mise en place de l'authentification Firebase Auth ou Supabase Auth.
    *   Connexion du swipe avec le serveur FastAPI (appels `/like` et `/dislike` asynchrones).

### 📅 Mois 3 : Recommandations en Direct et Beta Test
*   **Objectif :** Lancer une version d'essai auprès d'un panel de 50 testeurs.
*   **Tâches :**
    *   Implémentation sur FastAPI du calcul de style vectoriel de l'utilisateur à partir de son historique de likes.
    *   Développement de l'algorithme d'association d'outfits (composition de looks).
    *   Déploiement de l'API et de la base de données sur une infrastructure cloud souveraine (ex: Scaleway).
    *   Distribution de l'application via TestFlight (iOS) et Google Play Console (Android) à 50 utilisateurs cibles (étudiants de l'entourage) pour corriger les bugs d'UX et tester la fluidité.

### 📅 Mois 4 : Lancement Public et Marketing Viral
*   **Objectif :** Atteindre les 2 000 utilisateurs actifs sans budget publicitaire.
*   **Tâches :**
    *   Publication de l'application sur les stores officiels (App Store et Google Play Store).
    *   Lancement de la campagne de création de contenu organique sur TikTok et Instagram (publication de 3 vidéos courtes par semaine documentant le projet et montrant des tenues trouvées).
    *   Suivi quotidien des métriques de clics vers Vinted et de rétention.

---

## 3. Planification en Période d'Examens (Gestion des Risques de Temps)
*   **Mois 2 (Semaines 6-8) :** Période classique de partiels/examens. Le rythme de développement est réduit à **2 heures par semaine** (uniquement maintenance de base). Les jalons du Mois 2 sont étalés pour intégrer cette pause réglementaire personnelle.
*   **Buffer de temps :** Une marge de 2 semaines est conservée à la fin du Mois 3 pour absorber les retards de validation des App Stores (processus de review Apple parfois long).
