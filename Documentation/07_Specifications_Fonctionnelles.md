# 📐 Spécifications Fonctionnelles Détaillées — DetoxApp

**Version :** 1.0  
**Date :** 01 Mars 2026  
**Auteur :** Chef de Projet  

---

## 1. Priorisation MoSCoW

### Must Have (MVP — Version 1.0)
> Fonctionnalités **indispensables** pour le lancement. Sans elles, l'app n'a pas de sens.

### Should Have (Version 1.1)
> Fonctionnalités **importantes** qui enrichissent fortement l'expérience mais ne bloquent pas le lancement.

### Could Have (Version 2.0)
> Fonctionnalités **souhaitables** qui améliorent le produit si le temps le permet.

### Won't Have (Hors périmètre)
> Fonctionnalités **exclues** pour le moment.

---

## 2. Parcours Utilisateur Principal (User Flow)

```
┌─────────────┐    ┌──────────────┐    ┌───────────────────┐
│  Télécharge  │───▶│  Inscription │───▶│   Questionnaire   │
│    l'app     │    │ (Email/OAuth)│    │   Cold Start      │
└─────────────┘    └──────────────┘    │ (8-12 questions)  │
                                        └────────┬──────────┘
                                                 │
                   ┌─────────────────────────────▼──────────┐
                   │          ÉCRAN PRINCIPAL                │
                   │  ┌──────┬──────────┬─────────┬──────┐  │
                   │  │ Feed │ Défis    │ Groupes │Profil│  │
                   │  │      │          │         │      │  │
                   │  └──┬───┘──┬───────┘──┬──────┘──┬───┘  │
                   └─────┼──────┼──────────┼─────────┼──────┘
                         │      │          │         │
                    ┌────▼─┐ ┌──▼────┐ ┌───▼───┐ ┌──▼─────┐
                    │Scroll│ │Voir   │ │Rejoindre│ │Stats  │
                    │Reels │ │Défi du│ │Groupe  │ │Badges │
                    │      │ │jour   │ │Chat    │ │Params │
                    │Like  │ │Accept.│ │        │ │       │
                    │Save  │ │Preuve │ │        │ │       │
                    │Share │ │Reward │ │        │ │       │
                    └──────┘ └───────┘ └───────┘ └───────┘
```

---

## 3. Spécifications par Module

### 3.1 Module Inscription & Onboarding — 🟢 MUST HAVE

#### F01 — Écran de Bienvenue (Splash/Onboarding)

| Attribut | Spécification |
|----------|---------------|
| **Description** | 3-4 écrans de présentation de l'app (swipeable) |
| **Contenu** | Écran 1: "Marre du doom scrolling?" / Écran 2: "Contenu éducatif personnalisé" / Écran 3: "Défis pour grandir" / Écran 4: "Rejoins la communauté" |
| **Action** | Bouton "Commencer" → inscription |
| **Fréquence** | Affiché uniquement à la première ouverture |

#### F02 — Inscription / Connexion

| Attribut | Spécification |
|----------|---------------|
| **Méthodes** | Email + mot de passe, Google OAuth, Apple Sign-In |
| **Validation email** | Format valide, vérification par lien (Firebase Auth) |
| **Mot de passe** | Min 8 caractères, 1 majuscule, 1 chiffre |
| **Erreurs** | Messages clairs en français |
| **Stockage** | Firebase Auth (gestion sécurisée) |

#### F03 — Questionnaire Cold Start

| Attribut | Spécification |
|----------|---------------|
| **Nombre de questions** | 8-10 questions |
| **Format** | Choix multiples, sliders, sélection de tags |
| **Étapes** | Barre de progression visible |
| **Possibilité de skip** | Non (obligatoire pour personnalisation) |
| **Stockage** | Profil utilisateur en BDD |

**Questions du questionnaire :**

| # | Question | Type | Options |
|---|----------|------|---------|
| Q1 | Quel âge as-tu ? | Slider | 15-50+ |
| Q2 | Combien de temps passes-tu sur ton téléphone par jour ? | Choix unique | < 1h, 1-2h, 2-4h, 4-6h, 6h+ |
| Q3 | Quelles apps utilises-tu le plus ? | Choix multiple | TikTok, Instagram, YouTube, Twitter/X, Reddit, Facebook, Snapchat |
| Q4 | Qu'est-ce qui t'énerve dans ton usage actuel ? | Choix multiple | Perte de temps, contenu négatif, addiction, isolement, anxiété |
| Q5 | Quels sujets t'intéressent ? | Tags (min 3) | Science, Tech, Business, Santé, Sport, Art, Histoire, Langues, Psychologie, Finance, Cuisine, Musique, Voyage, Nature |
| Q6 | Quel est ton objectif principal ? | Choix unique | Apprendre, Être productif, Améliorer ma vie sociale, Développement personnel, Me sentir mieux |
| Q7 | Es-tu prêt(e) à sortir de ta zone de confort ? | Slider | 1 (Pas du tout) à 5 (Absolument) |
| Q8 | Préfères-tu les défis... | Choix unique | Seul(e), En groupe, Les deux |
| Q9 | À quelle heure utilises-tu le plus ton téléphone ? | Choix multiple | Matin, Midi, Après-midi, Soirée, Nuit |
| Q10 | Qu'est-ce qui te motiverait le plus ? | Choix unique | Points & récompenses, Progression visible, Communauté, Défis personnels |

---

### 3.2 Module Feed de Reels — 🟢 MUST HAVE

#### F05 — Feed Vertical de Reels

| Attribut | Spécification |
|----------|---------------|
| **Interface** | Scroll vertical plein écran (style TikTok) |
| **Préchargement** | Buffer 2 vidéos en avance |
| **Durée des reels** | 15 sec à 3 min (optimal: 30-90 sec) |
| **Format vidéo** | MP4, H.264, résolution 1080×1920 (9:16) |
| **Autoplay** | Oui (avec son coupé par défaut, tap pour activer) |
| **Boucle** | La vidéo boucle en fin de lecture |
| **Overlay** | Titre, auteur/source, catégorie, boutons d'action |

**Maquette textuelle du Feed :**

```
┌─────────────────────────────┐
│  ┌─logo─┐    DetoxApp   🔔 │  ← Header
│  └──────┘                   │
├─────────────────────────────┤
│                             │
│                             │
│      [   VIDÉO REEL   ]    │
│      [  PLEIN ÉCRAN   ]    │
│      [               ]     │
│      [               ]     │
│                             │
│                     ❤️ 234  │  ← Like
│                     🔖 56   │  ← Save
│                     ↗️ 12   │  ← Share
│                     💬 8    │  ← Commentaire(V2)
│                             │
│  📚 Science                 │  ← Catégorie
│  "Comment fonctionne        │  ← Titre
│   la mémoire musculaire"    │
│  @ScienceEtVie             │  ← Source
│                             │
│  ▶️ ━━━━━━━━━━━━━━━━━━ 1:23│  ← Progress bar
├─────────────────────────────┤
│  🏠    🎯    💬    👤      │  ← Navigation bar
│  Feed  Défis  Groupes Profil│
└─────────────────────────────┘
```

#### F06 — Algorithme de Recommandation (MVP)

| Attribut | Spécification |
|----------|---------------|
| **Phase 1 (Cold Start)** | Basé sur les réponses du questionnaire (tags d'intérêt) |
| **Phase 2 (Apprentissage)** | Pondération par likes, saves, temps de visionnage, skips |
| **Diversité** | 70% contenus dans les centres d'intérêt, 30% découverte |
| **Anti-bulle** | Injection régulière de contenu hors des intérêts principaux |
| **Rafraîchissement** | Nouveau contenu à chaque ouverture de l'app |

**Signal de scoring :**
```
score_reel = (
    0.35 × match_intérêts +
    0.25 × fraîcheur +
    0.20 × popularité_normalisée +
    0.10 × diversité_bonus +
    0.10 × random_discovery
)
```

#### F07 — Interactions avec les Reels

| Action | Comportement | Impact Algorithme |
|--------|-------------|-------------------|
| **Like (❤️)** | Animation cœur, compteur +1 | +0.3 score catégorie |
| **Save (🔖)** | Ajouté aux favoris | +0.5 score catégorie |
| **Share (↗️)** | Partage via lien/app externe | +0.2 score catégorie |
| **Skip rapide (<2s)** | Passe au suivant | -0.2 score catégorie |
| **Watch complet** | Vidéo vue à 100% | +0.4 score catégorie |
| **Rewatch** | Vidéo revue | +0.3 score catégorie |

#### F10 — Timer de Session

| Attribut | Spécification |
|----------|---------------|
| **Configuration** | L'utilisateur choisit un temps max (15, 30, 45, 60 min) |
| **Rappel doux** | À 80% du temps → notification in-app non bloquante |
| **Rappel fort** | À 100% → overlay "Tu as atteint ta limite !" avec option de continuer |
| **Statistiques** | Temps total quotidien affiché dans le profil |
| **Tonalité** | Bienveillante, jamais culpabilisante |

---

### 3.3 Module Défis Quotidiens — 🟢 MUST HAVE

#### F11 — Système de Défis

| Attribut | Spécification |
|----------|---------------|
| **Fréquence** | 1 défi principal/jour (gratuit), jusqu'à 3/jour (premium) |
| **Heure de publication** | Configurable (défaut: 8h00 matin) |
| **Durée de validité** | 24h pour compléter le défi |
| **Niveau de difficulté** | 1-5 étoiles, progressif selon le profil |
| **Personnalisation** | Adapté aux intérêts et au niveau de "zone de confort" (Q7) |

#### F12 — Catégories de Défis

| Catégorie | Exemples | Icône |
|-----------|----------|-------|
| **Social** | "Parle à un inconnu", "Appelle un ami que tu n'as pas vu depuis longtemps" | 👥 |
| **Bien-être** | "Médite 5 minutes", "Pas de téléphone 1h avant de dormir" | 🧘 |
| **Productivité** | "Lis 10 pages d'un livre", "Apprends 5 mots dans une nouvelle langue" | 📚 |
| **Créativité** | "Dessine quelque chose", "Écris un poème de 4 lignes" | 🎨 |
| **Sport** | "Fais 20 pompes", "Marche 30 minutes dehors" | 🏃 |
| **Courage** | "Confronte une peur aujourd'hui", "Fais quelque chose que tu repousses" | 🦁 |

**Exemples de défis détaillés :**

| Niveau | Défi | Catégorie | Points |
|--------|------|-----------|--------|
| ⭐ | "Souris à 3 personnes aujourd'hui" | Social | 10 XP |
| ⭐⭐ | "Envoie un message positif à quelqu'un" | Social | 20 XP |
| ⭐⭐⭐ | "Parle à un inconnu dans un café" | Courage | 40 XP |
| ⭐⭐⭐⭐ | "Présente-toi devant un groupe" | Courage | 60 XP |
| ⭐⭐⭐⭐⭐ | "Organise une sortie avec 5+ personnes" | Social | 100 XP |

#### F13 — Validation des Défis

| Méthode | Description | Fiabilité |
|---------|-------------|-----------|
| **Auto-déclaration** | L'utilisateur confirme avoir fait le défi | ⭐ |
| **Photo preuve** | L'utilisateur prend une photo comme preuve | ⭐⭐⭐ |
| **Timer intégré** | Pour les défis chronométrés (méditation, lecture) | ⭐⭐⭐⭐ |
| **Validation communautaire** | Les membres du groupe valident (V2) | ⭐⭐⭐ |

#### F14 — Système de Récompenses

```
                    SYSTÈME DE GAMIFICATION
                    
    ┌──────────────────────────────────────────┐
    │                                          │
    │  Points XP                               │
    │  ━━━━━━━━━━━                             │
    │  • Défi complété : 10-100 XP             │
    │  • Reel vu entièrement : 2 XP            │
    │  • Like donné : 1 XP                     │
    │  • Connexion quotidienne : 5 XP          │
    │                                          │
    │  Niveaux                                 │
    │  ━━━━━━━                                 │
    │  Niveau 1 : Débutant (0-100 XP)         │
    │  Niveau 2 : Éveillé (100-300 XP)        │
    │  Niveau 3 : Explorateur (300-700 XP)    │
    │  Niveau 4 : Challenger (700-1500 XP)    │
    │  Niveau 5 : Maître (1500-3000 XP)       │
    │  Niveau 6 : Légende (3000+ XP)          │
    │                                          │
    │  Streaks 🔥                              │
    │  ━━━━━━━━                                │
    │  • Connexion consécutive quotidienne     │
    │  • Bonus streak : +5 XP par jour consec. │
    │  • Streak perdu = retour à 0             │
    │  • Shield (Premium) : protège 1 jour     │
    │                                          │
    │  Badges 🏆                               │
    │  ━━━━━━━━                                │
    │  • "Premier Pas" : 1er défi complété     │
    │  • "Semaine de Feu" : 7 jours streak     │
    │  • "Social Butterfly" : 10 défis sociaux │
    │  • "Bookworm" : 50 reels éducatifs vus   │
    │  • "Fearless" : 5 défis courage complétés│
    │  • etc. (20+ badges prévus)              │
    │                                          │
    └──────────────────────────────────────────┘
```

---

### 3.4 Module Communication — 🟡 SHOULD HAVE (V1.1)

#### F17 — Messagerie Privée

| Attribut | Spécification |
|----------|---------------|
| **Type** | Chat texte 1-to-1 |
| **Médias** | Texte + emoji (images en V2) |
| **Temps réel** | Firebase Firestore (real-time sync) |
| **Notifications** | Push notification pour nouveaux messages |
| **Confidentialité** | Possibilité de bloquer un utilisateur |

#### F18 — Groupes Thématiques

| Attribut | Spécification |
|----------|---------------|
| **Création** | Automatique par centre d'intérêt + création manuelle (premium) |
| **Taille max** | 50 membres (MVP) |
| **Fonctionnalités** | Messages texte, partage de défis accomplis, réactions |
| **Modération** | Créateur du groupe + signalement |
| **Groupes par défaut** | 1 groupe par catégorie d'intérêt (Science, Tech, Sport, etc.) |

---

### 3.5 Module Profil & Statistiques — 🟢 MUST HAVE

#### F21 — Profil Utilisateur

**Maquette du profil :**

```
┌─────────────────────────────┐
│  ←  Mon Profil        ⚙️    │
├─────────────────────────────┤
│         ┌───────┐           │
│         │ Avatar│           │
│         └───────┘           │
│       Pseudo_User           │
│    Niveau 3 · Explorateur   │
│    🔥 12 jours streak       │
│                             │
│  ┌────────┬────────┬──────┐ │
│  │ 47     │ 12     │ 156  │ │
│  │ Défis  │ Badges │ Reels│ │
│  │complétés│       │ likés│ │
│  └────────┴────────┴──────┘ │
│                             │
│  📊 Mes Statistiques        │
│  ┌─────────────────────────┐│
│  │ Cette semaine:          ││
│  │ ⏱ 3h20 sur DetoxApp    ││
│  │ 📈 -45% TikTok (estimé)││
│  │ ✅ 5/7 défis complétés  ││
│  │ 🎯 42 XP gagnés         ││
│  └─────────────────────────┘│
│                             │
│  🏆 Mes Badges              │
│  [🏅][🏅][🏅][🏅][🔒][🔒] │
│                             │
│  📚 Mes Centres d'Intérêt   │
│  [Science] [Tech] [Sport]   │
│                             │
│  ⚙️ Paramètres              │
│  ▸ Modifier le profil       │
│  ▸ Notifications            │
│  ▸ Confidentialité          │
│  ▸ Timer de session         │
│  ▸ Déconnexion              │
└─────────────────────────────┘
```

#### F22 — Dashboard de Progression

| Statistique | Visualisation | Période |
|-------------|---------------|---------|
| Temps sur DetoxApp | Graphique en barres | Jour / Semaine / Mois |
| Défis complétés | Compteur + streak calendar | Semaine / Mois |
| XP gagnés | Courbe de progression | Semaine / Mois |
| Reels vus | Compteur par catégorie | Semaine / Mois |
| Niveau de progression | Barre de progression | Cumulé |

---

### 3.6 Module Notifications — 🟢 MUST HAVE

#### F20 — Notifications Push

| Type | Contenu | Fréquence | Horaire |
|------|---------|-----------|---------|
| **Défi quotidien** | "Ton défi du jour est prêt ! 🎯" | 1x/jour | Configurable (défaut 8h) |
| **Rappel streak** | "🔥 Ton streak de X jours est en danger !" | 1x/jour | 20h si pas connecté |
| **Nouveau contenu** | "Du nouveau contenu sur [intérêt] t'attend" | 2-3x/semaine | Variable |
| **Social** | "X a complété un défi !" | Selon activité | Temps réel |
| **Message** | "Tu as un nouveau message" | Selon activité | Temps réel |
| **Milestone** | "Félicitations ! Tu as atteint le niveau X !" | Selon progression | Immédiat |

**Règles :**
- Max 3 notifications/jour
- L'utilisateur peut configurer chaque type ON/OFF
- Tonalité toujours bienveillante et motivante
- Jamais culpabilisante ("Tu n'as pas ouvert l'app..." ❌)

---

## 4. Résumé MoSCoW

### 🟢 MUST HAVE (MVP — Version 1.0)

| # | Fonctionnalité | Effort |
|---|----------------|--------|
| 1 | Inscription (Email + OAuth) | S |
| 2 | Questionnaire Cold Start | M |
| 3 | Feed vertical de reels | XL |
| 4 | Algorithme de recommandation simple | L |
| 5 | Like, Save, Share sur reels | S |
| 6 | 1 Défi quotidien personnalisé | L |
| 7 | Validation de défi (auto-déclaration + photo) | M |
| 8 | Système de points XP + niveaux | M |
| 9 | Streaks quotidiens | S |
| 10 | Profil utilisateur + statistiques de base | M |
| 11 | Notifications push (défis + streak) | S |
| 12 | Timer de session | S |

### 🟡 SHOULD HAVE (Version 1.1)

| # | Fonctionnalité | Effort |
|---|----------------|--------|
| 13 | Badges & trophées (20+ badges) | M |
| 14 | Classement hebdomadaire (Leaderboard) | M |
| 15 | Groupes thématiques (chat) | L |
| 16 | Catégories de défis étendues | M |
| 17 | Historique des défis | S |
| 18 | Dashboard de progression avancé | M |

### 🔵 COULD HAVE (Version 2.0)

| # | Fonctionnalité | Effort |
|---|----------------|--------|
| 19 | Messagerie privée 1-to-1 | L |
| 20 | Contenu généré par les utilisateurs (UGC) | XL |
| 21 | Défis de groupe collaboratifs | L |
| 22 | Algorithme de recommandation IA avancé | XL |
| 23 | Thèmes personnalisables (premium) | S |
| 24 | Multi-langue | L |
| 25 | Intégration Screen Time iOS / Digital Wellbeing Android | L |

### 🔴 WON'T HAVE (Exclues)

| # | Fonctionnalité | Raison d'exclusion |
|---|----------------|-------------------|
| 26 | Live streaming | Trop complexe, hors scope |
| 27 | E-commerce / marketplace | Hors vision produit |
| 28 | Application web | Focus mobile uniquement |
| 29 | Smartwatch | Trop niche |
| 30 | Monétisation par publicité classique | Contradictoire avec la mission |

---

## 5. Modèle de Données (Simplifié)

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│    Users      │     │    Reels      │     │  Challenges  │
├──────────────┤     ├──────────────┤     ├──────────────┤
│ id (PK)      │     │ id (PK)      │     │ id (PK)      │
│ email        │     │ title        │     │ title        │
│ pseudo       │     │ description  │     │ description  │
│ avatar_url   │     │ video_url    │     │ category     │
│ level        │     │ thumbnail_url│     │ difficulty   │
│ xp_total     │     │ category     │     │ xp_reward    │
│ streak_count │     │ tags[]       │     │ type         │
│ interests[]  │     │ source       │     │ created_at   │
│ preferences  │     │ duration_sec │     └──────┬───────┘
│ created_at   │     │ likes_count  │            │
└──────┬───────┘     │ saves_count  │     ┌──────▼───────┐
       │             │ created_at   │     │UserChallenges│
       │             └──────┬───────┘     ├──────────────┤
       │                    │             │ id (PK)      │
  ┌────▼──────────┐  ┌─────▼──────┐     │ user_id (FK) │
  │ UserInterests │  │UserReelInter│     │ challenge_id │
  ├───────────────┤  ├────────────┤     │ status       │
  │ user_id (FK)  │  │ user_id    │     │ proof_url    │
  │ interest_tag  │  │ reel_id    │     │ completed_at │
  │ score (0-1)   │  │ action     │     │ xp_earned    │
  └───────────────┘  │ (like/save │     └──────────────┘
                     │  /skip/view)│
                     │ timestamp  │     ┌──────────────┐
                     └────────────┘     │   Badges     │
                                        ├──────────────┤
  ┌───────────────┐                     │ id (PK)      │
  │   Groups      │                     │ name         │
  ├───────────────┤                     │ description  │
  │ id (PK)       │                     │ icon_url     │
  │ name          │                     │ condition    │
  │ category      │                     └──────────────┘
  │ members_count │
  │ created_by    │                     ┌──────────────┐
  └───────────────┘                     │  UserBadges  │
                                        ├──────────────┤
                                        │ user_id (FK) │
                                        │ badge_id (FK)│
                                        │ earned_at    │
                                        └──────────────┘
```

---

## 6. API Endpoints Prévisionnels (MVP)

### Auth
| Méthode | Endpoint | Description |
|---------|----------|-------------|
| POST | `/api/auth/register` | Inscription |
| POST | `/api/auth/login` | Connexion |
| POST | `/api/auth/google` | OAuth Google |
| POST | `/api/auth/apple` | OAuth Apple |

### Users
| Méthode | Endpoint | Description |
|---------|----------|-------------|
| GET | `/api/users/me` | Profil courant |
| PUT | `/api/users/me` | Modifier profil |
| POST | `/api/users/me/interests` | Sauvegarder intérêts (questionnaire) |
| GET | `/api/users/me/stats` | Statistiques |

### Reels
| Méthode | Endpoint | Description |
|---------|----------|-------------|
| GET | `/api/reels/feed` | Feed personnalisé (paginated) |
| POST | `/api/reels/:id/like` | Liker un reel |
| POST | `/api/reels/:id/save` | Sauvegarder un reel |
| POST | `/api/reels/:id/skip` | Signaler skip (tracking) |
| GET | `/api/reels/saved` | Mes reels sauvegardés |

### Challenges
| Méthode | Endpoint | Description |
|---------|----------|-------------|
| GET | `/api/challenges/daily` | Défi(s) du jour |
| POST | `/api/challenges/:id/complete` | Marquer comme complété |
| POST | `/api/challenges/:id/proof` | Upload preuve (photo) |
| GET | `/api/challenges/history` | Historique des défis |

### Gamification
| Méthode | Endpoint | Description |
|---------|----------|-------------|
| GET | `/api/gamification/progress` | XP, niveau, streak |
| GET | `/api/gamification/badges` | Badges obtenus |
| GET | `/api/gamification/leaderboard` | Classement |

---

*Document généré dans le cadre de l'analyse du projet DetoxApp*
