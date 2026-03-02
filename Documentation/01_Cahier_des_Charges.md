# 📋 Cahier des Charges — DetoxApp

**Version :** 1.0  
**Date :** 01 Mars 2026  
**Auteur :** Chef de Projet  
**Statut :** Document initial  

---

## 1. Présentation Générale du Projet

### 1.1 Contexte

L'utilisation excessive des réseaux sociaux, en particulier le **doom scrolling** sur des plateformes comme TikTok et Instagram Reels, est devenue un problème de société majeur. Des études montrent que :

- L'utilisateur moyen passe **2h30 à 4h par jour** sur les réseaux sociaux
- Le doom scrolling est associé à une **augmentation de l'anxiété**, de la dépression et de la perte de productivité
- **73% des utilisateurs** déclarent passer plus de temps que prévu sur ces plateformes (Source : études Digital Wellbeing 2024-2025)
- Les algorithmes de recommandation sont conçus pour **maximiser le temps d'écran**, pas le bien-être de l'utilisateur

### 1.2 Problématique

> Comment transformer le temps passé sur les écrans en une expérience **éducative, stimulante et bénéfique** pour le développement personnel de l'utilisateur, tout en conservant le format engageant du contenu court (reels) ?

### 1.3 Vision du Projet

**DetoxApp** est une application mobile qui propose une **alternative saine au doom scrolling** en remplaçant le contenu addictif et improductif par :

- Un **feed personnalisé de contenu éducatif et stimulant** sous format court (reels)
- Des **défis quotidiens** poussant les utilisateurs à sortir de leur zone de confort
- Un **système de communication communautaire** entre personnes partageant les mêmes intérêts

### 1.4 Objectifs du Projet

| # | Objectif | Mesure de Succès |
|---|----------|------------------|
| O1 | Réduire le temps de doom scrolling des utilisateurs | Réduction de 30% du temps sur TikTok/Instagram en 30 jours |
| O2 | Proposer du contenu éducatif personnalisé | Score de satisfaction utilisateur > 4/5 |
| O3 | Encourager l'activité sociale réelle | 50% des utilisateurs complètent au moins 3 défis/semaine |
| O4 | Créer une communauté active | Taux de rétention à 30 jours > 40% |

---

## 2. Périmètre du Projet

### 2.1 Dans le périmètre (In Scope)

- Application mobile **Android et iOS** développée avec **Flutter**
- Système de **personnalisation** basé sur un questionnaire initial (cold start)
- **Feed de reels** personnalisés (contenu IA et/ou contenu utilisateur)
- Module de **défis quotidiens** avec système de récompenses
- **Messagerie** privée et de groupe
- **Système de gamification** (points, badges, niveaux)
- **Backend** avec API RESTful
- Système de **recommandation** personnalisé

### 2.2 Hors périmètre (Out of Scope) — Version 1

- Application web / version desktop
- Intégration avec des smartwatches
- Système de paiement intégré (avant validation du modèle économique)
- Support multilingue (français uniquement pour le MVP)
- Fonctionnalités de live streaming

---

## 3. Public Cible

### 3.1 Personas Utilisateurs

#### Persona 1 : « L'Étudiant Conscient » — Karim, 21 ans
- **Profil :** Étudiant en informatique, passe 3h/jour sur TikTok
- **Frustration :** Se sent improductif, veut apprendre des choses utiles
- **Besoin :** Du contenu tech/éducatif en format court + motivation quotidienne
- **Comportement :** Utilise son téléphone principalement le soir et pendant les pauses

#### Persona 2 : « Le Jeune Professionnel » — Amina, 27 ans
- **Profil :** Marketeur digital, accro aux Reels Instagram
- **Frustration :** Veut du contenu de développement personnel de qualité
- **Besoin :** Défis sociaux pour sortir de sa routine + communauté motivante
- **Comportement :** Scrolle pendant les transports et avant de dormir

#### Persona 3 : « L'Introverti Motivé » — Yassine, 24 ans
- **Profil :** Développeur freelance, peu de vie sociale
- **Frustration :** Sait qu'il perd son temps mais n'arrive pas à s'arrêter
- **Besoin :** Défis pour confronter ses peurs sociales + groupe de soutien
- **Comportement :** Utilise Reddit et YouTube Shorts de manière compulsive

### 3.2 Segmentation du Marché

| Segment | Âge | Caractéristique | Priorité |
|---------|-----|-----------------|----------|
| Étudiants | 18-25 | Fort usage mobile, budget limité | Haute |
| Jeunes professionnels | 25-35 | Revenu disponible, quête de productivité | Haute |
| Adolescents | 15-18 | Usage intensif, contrôle parental souhaité | Moyenne |
| Adultes 35+ | 35-50 | Prise de conscience tardive, moins technophiles | Basse |

---

## 4. Exigences Fonctionnelles

### 4.1 Module d'Inscription & Onboarding

| ID | Fonctionnalité | Priorité | Description |
|----|---------------|----------|-------------|
| F01 | Inscription | Haute | Inscription par email, Google, ou Apple ID |
| F02 | Questionnaire Cold Start | Haute | Formulaire de 8-12 questions pour cerner les intérêts, objectifs, et habitudes de l'utilisateur |
| F03 | Sélection des centres d'intérêt | Haute | Choix parmi des catégories (Science, Tech, Business, Santé, Sport, Art, Langues, etc.) |
| F04 | Tutoriel interactif | Moyenne | Guide de première utilisation |

### 4.2 Module Feed de Reels Personnalisés

| ID | Fonctionnalité | Priorité | Description |
|----|---------------|----------|-------------|
| F05 | Feed vertical swipeable | Haute | Interface de scrolling vertical similaire à TikTok |
| F06 | Algorithme de recommandation | Haute | Suggestions basées sur les intérêts, interactions et historique |
| F07 | Interaction (like, save, partager) | Haute | Actions sur chaque reel |
| F08 | Signalement de contenu | Moyenne | Possibilité de signaler du contenu inapproprié |
| F09 | Catégorisation du contenu | Haute | Tags et catégories pour chaque reel |
| F10 | Timer de session | Moyenne | Rappel configurable pour limiter le temps d'utilisation |

### 4.3 Module Défis Quotidiens (Daily Challenges)

| ID | Fonctionnalité | Priorité | Description |
|----|---------------|----------|-------------|
| F11 | Génération de défis personnalisés | Haute | Défis adaptés au profil et niveau de l'utilisateur |
| F12 | Catégories de défis | Haute | Social, Bien-être, Productivité, Créativité, Sport |
| F13 | Système de validation | Haute | Photo/vidéo preuve + validation communautaire |
| F14 | Système de récompenses | Haute | Points XP, badges, niveaux, streaks |
| F15 | Classement (Leaderboard) | Moyenne | Classement hebdomadaire/mensuel |
| F16 | Historique des défis | Moyenne | Journal de bord des défis accomplis |

### 4.4 Module Communication

| ID | Fonctionnalité | Priorité | Description |
|----|---------------|----------|-------------|
| F17 | Messagerie privée | Moyenne | Chat 1-to-1 entre utilisateurs |
| F18 | Groupes thématiques | Moyenne | Groupes basés sur les centres d'intérêt |
| F19 | Partage de progrès | Moyenne | Partager ses réalisations de défis dans les groupes |
| F20 | Notifications push | Haute | Rappels de défis, messages, contenu recommandé |

### 4.5 Module Profil & Gamification

| ID | Fonctionnalité | Priorité | Description |
|----|---------------|----------|-------------|
| F21 | Profil utilisateur | Haute | Infos, avatar, statistiques, badges |
| F22 | Dashboard de progression | Haute | Visualisation du temps économisé, défis complétés, etc. |
| F23 | Système de niveaux | Haute | Progression par paliers avec récompenses |
| F24 | Badges & Trophées | Moyenne | Récompenses visuelles pour les accomplissements |
| F25 | Paramètres de confidentialité | Haute | Contrôle de la visibilité du profil |

---

## 5. Exigences Non-Fonctionnelles

### 5.1 Performance

| Exigence | Spécification |
|----------|---------------|
| Temps de chargement initial | < 3 secondes |
| Temps de chargement d'un reel | < 1 seconde (avec préchargement) |
| Temps de réponse API | < 500ms (p95) |
| Disponibilité | 99.5% uptime |

### 5.2 Sécurité

| Exigence | Spécification |
|----------|---------------|
| Authentification | JWT + OAuth 2.0 |
| Chiffrement des données | TLS 1.3 en transit, AES-256 au repos |
| Conformité RGPD | Obligatoire (données personnelles) |
| Stockage des mots de passe | Hashing bcrypt/scrypt |

### 5.3 Scalabilité

| Exigence | Spécification |
|----------|---------------|
| Utilisateurs simultanés (MVP) | Jusqu'à 1 000 |
| Utilisateurs simultanés (V2) | Jusqu'à 50 000 |
| Stockage vidéo | Cloud scalable (CDN) |

### 5.4 Compatibilité

| Exigence | Spécification |
|----------|---------------|
| Android | Version 8.0 (API 26) et supérieur |
| iOS | Version 14.0 et supérieur |
| Flutter SDK | Dernière version stable |

---

## 6. Architecture Technique Prévisionnelle

### 6.1 Stack Technologique

| Couche | Technologie |
|--------|-------------|
| **Frontend Mobile** | Flutter (Dart) |
| **Backend API** | Node.js (Express) ou Python (FastAPI) — *à décider* |
| **Base de données** | PostgreSQL (données relationnelles) + Redis (cache) |
| **Base de données temps réel** | Firebase Firestore (chat) |
| **Stockage médias** | AWS S3 / Firebase Storage + CDN |
| **IA / Recommandation** | Python (TensorFlow/PyTorch) ou API OpenAI |
| **Notifications** | Firebase Cloud Messaging (FCM) |
| **Analytics** | Firebase Analytics + Mixpanel |
| **CI/CD** | GitHub Actions |

### 6.2 Schéma d'Architecture Simplifié

```
┌─────────────────────────────────────────────────┐
│                  APPLICATION MOBILE               │
│                   (Flutter/Dart)                   │
│  ┌──────────┐  ┌──────────┐  ┌──────────────┐   │
│  │   Feed    │  │ Challenges│  │  Messagerie  │   │
│  │  Reels    │  │  Module   │  │    Module    │   │
│  └────┬─────┘  └─────┬────┘  └──────┬───────┘   │
└───────┼──────────────┼──────────────┼────────────┘
        │              │              │
        ▼              ▼              ▼
┌─────────────────────────────────────────────────┐
│                    API GATEWAY                     │
│              (REST API + WebSocket)                │
└───────┬──────────────┬──────────────┬────────────┘
        │              │              │
   ┌────▼────┐   ┌─────▼────┐  ┌─────▼─────┐
   │ Service  │   │ Service  │  │  Service  │
   │ Contenu  │   │  Défis   │  │   Chat    │
   └────┬────┘   └─────┬────┘  └─────┬─────┘
        │              │              │
   ┌────▼────┐   ┌─────▼────┐  ┌─────▼─────┐
   │PostgreSQL│   │PostgreSQL│  │ Firestore │
   │ + Redis  │   │          │  │           │
   └─────────┘   └──────────┘  └───────────┘
        │
   ┌────▼──────────┐
   │  Moteur IA    │
   │ Recommandation│
   └───────────────┘
```

---

## 7. Contraintes du Projet

| Contrainte | Description |
|------------|-------------|
| Développeur unique | Projet réalisé par une seule personne |
| Budget limité | Utilisation de services gratuits/freemium en priorité |
| Contenu initial | Nécessité de constituer une base de contenu au lancement |
| Modération | Besoin d'un système de modération même automatisé |

---

## 8. Livrables Attendus

| # | Livrable | Format |
|---|----------|--------|
| L1 | Documentation d'analyse complète | Markdown / PDF |
| L2 | Maquettes UI/UX (wireframes + mockups) | Figma |
| L3 | MVP fonctionnel (Android + iOS) | APK / IPA |
| L4 | Backend déployé | Cloud (Heroku / Railway / AWS) |
| L5 | Code source versionné | Repository GitHub |
| L6 | Documentation technique (API) | Swagger / Markdown |

---

## 9. Critères d'Acceptation du MVP

Pour que le MVP soit considéré comme valide, il doit inclure :

- [ ] Inscription et onboarding fonctionnels avec questionnaire
- [ ] Feed de reels personnalisé avec au moins 50 contenus initiaux
- [ ] Au moins 20 défis quotidiens différents
- [ ] Système de points et de streaks fonctionnel
- [ ] Profil utilisateur avec statistiques de base
- [ ] Notifications push pour les défis quotidiens
- [ ] Performance acceptable (< 3s de chargement)
- [ ] Testé sur au moins 2 appareils Android et 1 iOS

---

*Document généré dans le cadre de l'analyse du projet DetoxApp*
