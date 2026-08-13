# 📊 Business Model Canvas — SwipeWear

Ce document présente les 9 blocs stratégiques du modèle d'affaires de **SwipeWear** appliqué au marché mondial et européen.

---

```
┌────────────────────────┬────────────────────────┬────────────────────────┬────────────────────────┬────────────────────────┐
│   Partenaires Clés     │    Activités Clés      │ Proposition de Valeur  │   Relations Clients    │  Segments de Clientèle │
|                        │                        │                        │                        │                        |
│ - Vinted / Depop       │ - Dev & UX mobile      │ - Découverte de mode   │ - Onboarding auto      │ - Gen Z & Millennials  │
│ - Hébergeurs Cloud     │ - Ingestion & IA CLIP  │   seconde main par     │ - Communauté TikTok    │   éco-responsables     │
│ - Influenceurs Vintage │ - Marketing de contenu │   swipe ludique.       │ - Respect strict du    │ - Passionnés de style  │
│ - Hugging Face / Models│                        │ - Recommandation       │   RGPD (anonymat)      │   vintage unique       │
|                        │                        │   esthétique par IA.   │                        │ - Acheteurs de fripes  │
|                        │                        │ - Générateur de tenues │                        │   à petit budget       │
│                        │                        │   (outfit matching).   │                        │                        │
├────────────────────────┼────────────────────────┤                        ├────────────────────────┤                        │
│    Ressources Clés     │        Canaux          │                        │                        │                        │
|                        │                        │                        │                        │                        |
│ - Compétences Dev/IA   │ - App Store (Apple)    │                        │ - App Stores           │                        │
│ - CLIP model (open)    │ - Play Store (Google)  │                        │ - Réseaux (TikTok/Reels│                        │
│ - BDD pgvector         │ - TikTok/Reels/Shorts  │                        │ - Bouche-à-oreille     │                        │
├────────────────────────┴────────────────────────┴────────────────────────┴────────────────────────┴────────────────────────┤
│                    Structure de Coûts                                   │                 Sources de Revenus                   │
|                                                                         │                                                      |
│ - Hébergement Cloud API & BDD (15€ - 30€/mois)                          │ - Freemium : Swipe illimité, mais tenues limitées    │
│ - Licences Apple (99€/an) & Google (25$ unique)                         │   à 3 compositions par jour.                         │
│ - Proxy / Scraper rotation IP (10€/mois)                                │ - Abonnement Premium (SwipeWear Gold) : 2,99€/mois   │
│ - Marketing (0€ - uniquement organique)                                 │   pour tenues illimitées et filtres avancés.         │
└─────────────────────────────────────────────────────────────────────────┴──────────────────────────────────────────────────────┘
```

---

## 1. Description Détaillée des 9 Blocs

### 1.1 Partenaires Clés (Key Partners)
*   **Vinted & Depop :** En tant que sources de données (agrégation) et plateformes de finalisation des achats (redirection).
*   **Hébergeurs Cloud (Railway / Render / Scaleway) :** Fournisseurs d'infrastructure cloud abordables et hébergés en Europe pour la base de données PostgreSQL et l'API FastAPI.
*   **Créateurs de Contenu & Micro-Influenceurs Mode :** Relais de croissance essentiels pour tester l'application et la faire connaître organiquement.
*   **Hugging Face :** Dépôt d'hébergement open-source pour le modèle CLIP utilisé pour l'indexation.

### 1.2 Activités Clés (Key Activities)
*   **Développement Logiciel :** Amélioration continue de l'application React Native et optimisation de la fluidité des cartes de swipe.
*   **Ingénierie IA :** Optimisation du pipeline d'indexation vectorielle des images de vêtements et ajustement de l'algorithme d'association d'outfits.
*   **Maintenance du Scraper :** Mise à jour continue du robot d'aspiration des annonces pour s'adapter aux changements de design des plateformes sources.
*   **Marketing de Contenu :** Création hebdomadaire de vidéos TikTok/Reels démontrant l'usage de l'application et les tenues trouvées.

### 1.3 Ressources Clés (Key Resources)
*   **Compétences Techniques (Solopreneur) :** Maîtrise de React Native, Python, FastAPI, et de l'ingénierie des embeddings.
*   **Modèle CLIP d'OpenAI :** Ressource IA gratuite de base permettant la compréhension visuelle de haut niveau des vêtements.
*   **Base de Données Vectorielle PostgreSQL :** Stockage performant et structuré de l'historique et des vecteurs de similarité.

### 1.4 Proposition de Valeur (Value Proposition)
*   **Découverte Ludique :** Transforme la recherche fastidieuse de vêtements de seconde main en un jeu addictif (le swipe).
*   **Recommandation Stylistique :** L'IA comprend le style visuel de l'utilisateur (grunge, streetwear, minimaliste) sans saisie de texte.
*   **Coordination de Tenues (Outfits) :** L'application compose automatiquement des looks complets à partir de pièces d'occasion réelles disponibles à l'achat immédiat.

### 1.5 Relations Clients (Customer Relationships)
*   **Onboarding Automatisé :** Parcours utilisateur sans friction (création de compte et questionnaire de style en 1 minute).
*   **Confiance & Transparence (RGPD) :** Aucune revente de données personnelles. Traitement de style vectoriel anonymisé.
*   **Communauté Active :** Interaction avec les utilisateurs sur les réseaux sociaux (TikTok/Instagram) pour co-construire l'application (Build in Public).

### 1.6 Canaux (Channels)
*   **Magasins d'Applications (App Store & Google Play) :** Canal de téléchargement direct.
*   **Réseaux Sociaux Organiques :** Publication de vidéos courtes (TikTok, Reels, Shorts) montrant l'application en action et des tenues dénichées.
*   **Bouche-à-oreille numérique :** Partage facile d'outfits générés sur les stories des utilisateurs.

### 1.7 Segments de Clientèle (Customer Segments)
*   **Les Étudiants et Jeunes Actifs (15-30 ans) :** Consommateurs de seconde main, sensibles aux prix, cherchant des marques de qualité.
*   **Les Chercheurs de Style Unique (Vintage/Y2K) :** Personnes voulant se démarquer et s'habiller de manière singulière sans le prix du neuf.
*   **Les Consommateurs Éco-Sensibles :** Personnes refusant d'acheter du neuf par conviction écologique.

### 1.8 Structure de Coûts (Cost Structure)
*   **Hébergement API & Base de données :** ~15€ à 30€/mois pour un serveur PostgreSQL + FastAPI de base.
*   **Licences Développeur :** 99€/an pour Apple Developer et 25$ (paiement unique) pour Google Play Console.
*   **Proxies pour Scraper :** ~10€/mois pour des adresses IP tournantes afin d'éviter le blocage de l'aspiration d'annonces.
*   **Acquisition Client :** 0€ (entièrement basée sur le contenu organique).

### 1.9 Sources de Revenus (Revenue Streams)
*   **Abonnement Premium (Freemium) :** L'usage du swipe et du dressing virtuel est gratuit. Cependant, la génération de tenues complètes est limitée à 3 par jour dans la version gratuite. L'abonnement Premium à **2,99€/mois** (ou 19,99€/an) offre des tenues illimitées et des filtres de marques/tailles exclusifs.
*   **Affiliation (Futur) :** Négociation de liens d'affiliation avec des plateformes d'upcycling ou des friperies en ligne partenaires.
