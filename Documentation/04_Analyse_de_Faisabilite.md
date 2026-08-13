# 📊 Analyse de Faisabilité — SwipeWear

Ce document évalue la faisabilité technique et opérationnelle du projet **SwipeWear**, en prenant en compte le profil de développeur solo/ingénieur IA en parallèle d'études.

---

## 1. Faisabilité Technique

Le projet est hautement réalisable par une personne seule grâce à l'utilisation de technologies modernes "out-of-the-box" et d'une architecture décentralisée.

### 1.1 Stack Technologique Réfractée (Solo-Friendly)
*   **Frontend (React Native & Expo) :** L'écosystème Expo simplifie la compilation, les tests sur appareil réel et la soumission aux App Stores. L'utilisation de packages de swipe éprouvés (`react-native-deck-swiper`) réduit le temps de développement de l'interface à quelques jours.
*   **Backend (FastAPI) :** Ce framework Python est asynchrone, extrêmement rapide, et permet d'importer directement les bibliothèques d'IA Hugging Face sans avoir besoin de faire des appels réseau vers des services externes coûteux.
*   **Base de données (PostgreSQL + pgvector) :** L'utilisation de `pgvector` permet de stocker les embeddings de 512 dimensions sous forme de type `vector` et d'effectuer des recherches de similarité cosinus avec un simple index HNSW (Hierarchical Navigable Small World). Cela évite de devoir déployer et payer un service de base de données vectorielle dédié (comme Pinecone).

### 1.2 Utilisation et Coût de l'IA
*   **Modèle CLIP (OpenAI / Hugging Face) :** Le modèle `sentence-transformers/clip-ViT-B-32` est open-source et pèse environ 350 Mo. Il peut s'exécuter sur un CPU standard sans nécessiter de serveur GPU coûteux.
*   **Processus d'inférence :** 
    1.  *Ingestion :* Lorsqu'un vêtement est importé en base, le backend génère son embedding visuel en ~100 ms (sur CPU) et le stocke.
    2.  *Profiling utilisateur :* Les calculs de moyenne vectorielle pour mettre à jour le profil de style de l'utilisateur sont de simples opérations mathématiques dans PostgreSQL, prenant moins de 5 ms.
    3.  *Recommandation :* La recherche de similarité vectorielle avec index HNSW s'exécute en moins de 15 ms pour 10 000 articles.

### 1.3 Architecture Simplifiée du Système

```
┌────────────────────────────────────────────────────────┐
│                   MOBILE APP (Expo)                    │
│   - Swipe UI (deck swiper)                             │
│   - Dressing virtuel / Outfits (tenues)                │
└───────────────────────────┬────────────────────────────┘
                            │ (API HTTPS)
                            ▼
┌────────────────────────────────────────────────────────┐
│                   BACKEND (FastAPI)                    │
│   - Gestion du flux de cartes (/feed, /like)           │
│   - Génération d'embeddings (CLIP local sur CPU)       │
│   - Algorithme d'assemblage de tenues (Outfits)        │
└───────────────────────────┬────────────────────────────┘
                            │ (SQL Query)
                            ▼
┌────────────────────────────────────────────────────────┐
│             DATABASE (PostgreSQL + pgvector)           │
│   - Tables utilisateurs et interactions                │
│   - Index HNSW pour similarité cosinus                 │
└───────────────────────────▲────────────────────────────┘
                            │ (Bulk Insert)
                            │
┌───────────────────────────┴────────────────────────────┐
│               SCRAPER / AGGREGATOR SCRIPT              │
│   - Script Python s'exécutant localement               │
│   - Extraction périodique d'annonces Vinted/Depop      │
└────────────────────────────────────────────────────────┘
```

---

## 2. Faisabilité Opérationnelle (Gestion du Temps & Études)

Le plus grand défi d'un projet étudiant est le manque de temps. SwipeWear est conçu pour minimiser la maintenance opérationnelle grâce à 3 principes cardinaux.

### 2.1 La Stratégie du "Stateless" (Sans base de données lourde)
*   **Aucun stockage d'images :** L'application ne stocke pas les fichiers images des vêtements sur ses serveurs (ce qui coûterait cher en stockage S3 et bande passante). Elle stocke uniquement les URLs d'origine des images Vinted/Depop.
*   **Zéro gestion financière :** En redirigeant l'utilisateur sur Vinted/Depop pour l'achat, l'application élimine le service client lié aux livraisons, remboursements et fraudes bancaires.

### 2.2 Exploitation des Assistants de Codage par IA
*   En tant qu'ingénieur IA, l'utilisation systématique d'assistants de code (Cursor, Github Copilot, Gemini) pour générer le code boilerplate, les requêtes SQL complexes et les composants UI de React Native permet d'accélérer le développement par un facteur de 3.
*   Le développement du MVP est estimé à **60 heures de travail effectif**, facilement répartibles sur 6 semaines à raison de 10 heures par semaine (principalement le week-end).

### 2.3 Stratégie de Lancement "Build in Public"
*   La validation du marché s'effectue en parallèle du codage. En documentant le développement sur TikTok ("Jour 1 de la création du Tinder de la fripe"), l'étudiant crée sa propre audience d'acquisition sans dépenser 1€ en publicité, réduisant l'effort marketing de lancement à zéro.
