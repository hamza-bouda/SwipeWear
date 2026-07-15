# 📋 Spécifications Fonctionnelles — SwipeWear

Ce document liste de manière exhaustive les exigences fonctionnelles de la version 1 (MVP) et des évolutions futures (V2) de **SwipeWear**, et modélise le parcours utilisateur (User Flow).

---

## 1. Liste des Fonctionnalités

### 1.1 Fonctionnalités du MVP (V1)
Les fonctionnalités suivantes constituent le cœur du produit minimum viable nécessaire pour valider l'adéquation au marché (product-market fit).

*   **F01 - Authentification Simple :**
    *   Création de compte et connexion sécurisée via e-mail/mot de passe ou identifiants tiers (Google, Apple).
*   **F02 - Formulaire d'Onboarding Style (Cold Start) :**
    *   Questionnaire rapide à la première connexion : choix du genre de vêtements (Homme, Femme, Mixte), des tailles standards (hauts, bas, pointures) et sélection visuelle de 3 à 5 inspirations esthétiques (ex: photo streetwear, photo minimaliste) pour pré-remplir le profil de style initial.
*   **F03 - Le Swipe Deck :**
    *   Affichage d'une pile de cartes de vêtements avec : photo principale, prix, taille, marque, plateforme d'origine (logo Vinted ou Depop).
    *   *Gestes :* Swipe Droite = Like (sauvegardé), Swipe Gauche = Dislike (masqué définitivement), Swipe Haut = Ajout de la pièce à la tenue en cours de création.
*   **F05 - Le Dressing Virtuel :**
    *   Espace de stockage listant tous les articles aimés par l'utilisateur, triables par catégories (Hauts, Bas, Chaussures, Accessoires).
*   **F06 - Le Générateur de Tenues Initiale (Outfits) :**
    *   Onglet dédié proposant 3 suggestions de tenues complètes par jour, assemblées par similarité vectorielle (un haut, un bas et une paire de chaussures qui partagent une esthétique visuelle proche).
*   **F07 - Redirection d'Achat Directe :**
    *   Bouton d'appel à l'action "Acheter sur Vinted/Depop" ouvrant la fiche produit d'origine dans un navigateur web interne ou directement dans l'application tierce installée sur le smartphone.

### 1.2 Évolutions futures (V2)
Ces fonctionnalités seront implémentées après validation de la traction du MVP.

*   **F08 - L'Éditeur Interactif de Tenues :**
    *   Possibilité pour l'utilisateur de glisser/déposer ses vêtements aimés pour composer ses propres tenues et les partager.
*   **F09 - Numérisation de sa Garde-Robe existante (Edge-AI) :**
    *   Permettre à l'utilisateur de prendre en photo ses propres vêtements. L'IA supprime automatiquement l'arrière-plan en local et génère l'embedding du vêtement pour l'associer aux vêtements d'occasion de l'application.
*   **F10 - Alertes Push "Bonnes Affaires" :**
    *   Notification immédiate lorsque le scraper indexe un article correspondant à 95% au profil de style de l'utilisateur avec un prix inférieur de 20% à la moyenne du marché.
*   **F11 - Cabine d'Essayage Virtuelle 2D :**
    *   Superposition par IA du vêtement sélectionné sur une silhouette type ou sur une photo de l'utilisateur pour visualiser le rendu des proportions.

---

## 2. Parcours Utilisateur Principal (User Flow)

Le schéma ci-dessous modélise l'expérience utilisateur depuis le téléchargement de l'application jusqu'à l'achat final.

```
                  ┌─────────────────────────────┐
                  │   Téléchargement & Launch   │
                  └──────────────┬──────────────┘
                                 │
                                 ▼
                  ┌─────────────────────────────┐
                  │    Inscription / Connexion  │
                  └──────────────┬──────────────┘
                                 │
                                 ▼
                  ┌─────────────────────────────┐
                  │   Onboarding (Tailles/Style)│
                  └──────────────┬──────────────┘
                                 │
                                 ▼
                  ┌─────────────────────────────┐
        ┌────────►│     Écran de Swipe (Feed)   │◄────────┐
        │         └──────────────┬──────────────┘         │
        │                        │                        │
  Swipe Gauche              Swipe Droite              Swipe Haut
 (Dislike/Masquer)        (Like/Dressing)         (Ajouter à Tenue)
        │                        │                        │
        │                        ▼                        │
        └───────────────── [Dressing Virtuel]             │
                                 │                        │
                                 ▼                        │
                  ┌─────────────────────────────┐         │
                  │    Générateur d'Outfits     ├─────────┘
                  └──────────────┬──────────────┘
                                 │
                                 ▼
                  ┌─────────────────────────────┐
                  │ Bouton "Acheter sur Vinted" │
                  └──────────────┬──────────────┘
                                 │
                                 ▼
                  ┌─────────────────────────────┐
                  │ Redirection App Externe &   │
                  │    Transaction Finale       │
                  └─────────────────────────────┘
```

---

## 3. Spécifications des Interfaces Clés (Wireframes Conceptuels)

### 3.1 Écran de Swipe
*   **Zone Supérieure :** Header minimaliste avec logo SwipeWear, sélecteur rapide de filtres (Homme/Femme) et icône du Dressing.
*   **Zone Centrale :** La carte de vêtement (90% de la hauteur de l'écran). L'image occupe tout l'espace de la carte. En superposition semi-transparente en bas : Titre du produit, Marque, Taille, Prix en surbrillance (vert).
*   **Zone Inférieure :** Trois boutons d'action physiques pour les utilisateurs réfractaires aux gestes de swipe (Rejeter, Ajouter à la tenue, Aimer).

### 3.2 Écran Outfits (Mes Tenues)
*   Affichage en grille verticale de silhouettes de tenues composées de 3 vignettes d'images alignées (un Haut, un Bas, des Chaussures).
*   Sous chaque tenue : Prix total accumulé des pièces d'occasion (ex: "Tenue complète à 48,00 €").
*   Bouton "Acheter la tenue" ouvrant un menu avec les liens de redirection individuels pour chaque vêtement.
