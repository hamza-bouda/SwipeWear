# 📅 Planning & Roadmap — DetoxApp

**Version :** 1.0  
**Date :** 01 Mars 2026  
**Auteur :** Chef de Projet  

---

## 1. Phases du Projet

### Vue d'Ensemble

```
Phase 0        Phase 1          Phase 2          Phase 3         Phase 4
PRÉPARATION    MVP DEV          BETA & LAUNCH    CROISSANCE      SCALE
(4 sem)        (16-20 sem)      (4-6 sem)        (12-16 sem)     (continu)
───────────────────────────────────────────────────────────────────────▶
Mars  Avr      Avr - Août       Sep - Oct        Nov - Fév       Mars+
2026           2026             2026             2026-2027       2027
```

---

## 2. Phase 0 — Préparation (Semaines 1-4)

**Objectif :** Tout préparer avant de coder.

| Sem. | Tâche | Livrable | Effort |
|------|-------|----------|--------|
| S1 | Finaliser la documentation projet | Ce dossier complet ✅ | 15h |
| S1 | Créer le repository GitHub + structure projet | Repo initialisé | 2h |
| S1-S2 | **Constituer la base de contenu initial** (min 100 reels curés) | Base de données de contenus | 20h |
| S2 | Design UI/UX — Wireframes (Figma) | Wireframes de tous les écrans | 15h |
| S2-S3 | Design UI/UX — Mockups haute fidélité | Mockups Figma | 20h |
| S3 | Définir l'architecture technique finale | Document d'architecture | 5h |
| S3 | Configurer Firebase (Auth, Firestore, FCM, Storage) | Projet Firebase configuré | 3h |
| S3-S4 | **Landing page + waitlist** pour valider l'intérêt | Page web live | 8h |
| S4 | Configurer CI/CD (GitHub Actions) | Pipeline fonctionnel | 4h |
| S4 | Finaliser le backlog MVP dans un outil de suivi | Backlog priorisé (GitHub Projects / Notion) | 4h |

**Total Phase 0 : ~96 heures (~4 semaines à 24h/semaine)**

### Critères de passage à Phase 1 :
- [x] Documentation complète
- [ ] Base de 100+ contenus curés
- [ ] Wireframes validés
- [ ] Infra Firebase configurée
- [ ] Au moins 30 inscriptions waitlist

---

## 3. Phase 1 — Développement MVP (Semaines 5-24)

### Sprint 1 (S5-S6) — Fondations
| Tâche | Détail | Effort |
|-------|--------|--------|
| Setup projet Flutter | Architecture clean, packages de base | 8h |
| Système de navigation | GoRouter, bottom nav bar | 6h |
| Thème & Design system | Couleurs, typographie, composants de base | 8h |
| Écrans d'onboarding (splash + 3 slides) | UI + animations | 8h |
| **TOTAL** | | **30h** |

### Sprint 2 (S7-S8) — Auth & Questionnaire
| Tâche | Détail | Effort |
|-------|--------|--------|
| Inscription/Connexion (Email) | Firebase Auth + formulaires | 10h |
| OAuth Google + Apple | Intégration packages | 8h |
| Questionnaire Cold Start (10 questions) | UI stepper + logique | 12h |
| Stockage profil utilisateur | Modèle + API | 6h |
| **TOTAL** | | **36h** |

### Sprint 3-4 (S9-S12) — Feed de Reels ⭐ (Feature critique)
| Tâche | Détail | Effort |
|-------|--------|--------|
| Architecture du feed vertical | PageView + video_player | 12h |
| Lecteur vidéo (play/pause/boucle) | Contrôles + UI overlay | 10h |
| Préchargement des vidéos (buffer) | Cache + performance | 12h |
| Upload et gestion du contenu curé | Admin panel basique / script | 10h |
| Boutons d'interaction (like, save, share) | UI + backend | 8h |
| Algorithme de recommandation V1 | Filtrage par tags + scoring basique | 16h |
| Pagination infinie | Scroll infini + API | 6h |
| Tests & optimisation performance | Profiling, fix lags | 8h |
| **TOTAL** | | **82h** |

### Sprint 5-6 (S13-S16) — Défis & Gamification
| Tâche | Détail | Effort |
|-------|--------|--------|
| Écran de défi quotidien | UI + animation reveal | 10h |
| Base de données de défis (50+ défis) | Création + catégorisation | 8h |
| Sélection personnalisée du défi | Algorithme basé sur profil | 8h |
| Système de validation (auto + photo) | UI upload + stockage | 10h |
| Système de points XP | Calcul + affichage + animations | 8h |
| Système de niveaux (6 niveaux) | Logique de progression + UI | 6h |
| Streaks quotidiens | Tracking + fire animation | 8h |
| Notifications défi quotidien | FCM + scheduling | 6h |
| **TOTAL** | | **64h** |

### Sprint 7-8 (S17-S20) — Profil, Stats & Polish
| Tâche | Détail | Effort |
|-------|--------|--------|
| Écran de profil complet | UI avec stats, badges, paramètres | 12h |
| Dashboard de statistiques | Graphiques (bar chart, progression) | 10h |
| Badges (10 badges MVP) | Design + conditions + unlock | 10h |
| Timer de session | Configuration + rappels in-app | 6h |
| Paramètres (notifs, confidentialité, profil) | UI + logique | 8h |
| Favoris / Reels sauvegardés | Écran de liste + sync | 6h |
| **TOTAL** | | **52h** |

### Sprint 9-10 (S21-S24) — Backend, Tests & Stabilisation
| Tâche | Détail | Effort |
|-------|--------|--------|
| Développement backend API complète | Tous les endpoints | 20h |
| Tests unitaires (couverture > 60%) | Flutter tests + backend tests | 16h |
| Tests d'intégration | Scénarios end-to-end | 10h |
| Optimisation performance globale | Profiling, chargement, mémoire | 10h |
| Bug fixing & stabilisation | Correction des bugs critiques | 12h |
| Préparation assets stores (icône, screenshots) | Design + textes | 6h |
| **TOTAL** | | **74h** |

### Récapitulatif Phase 1

| Sprint | Thème | Heures | Semaines |
|--------|-------|--------|----------|
| Sprint 1 | Fondations | 30h | S5-S6 |
| Sprint 2 | Auth & Questionnaire | 36h | S7-S8 |
| Sprint 3-4 | Feed de Reels | 82h | S9-S12 |
| Sprint 5-6 | Défis & Gamification | 64h | S13-S16 |
| Sprint 7-8 | Profil, Stats & Polish | 52h | S17-S20 |
| Sprint 9-10 | Backend, Tests & Stabilisation | 74h | S21-S24 |
| **TOTAL Phase 1** | | **338h** | **~20 semaines** |

**Rythme : ~17h/semaine** (soutenable pour un développeur solo)

---

## 4. Phase 2 — Beta Testing & Lancement (Semaines 25-30)

| Sem. | Tâche | Détail |
|------|-------|--------|
| S25 | Déploiement beta fermée | TestFlight (iOS) + Google Play Internal Testing |
| S25-S26 | Recrutement beta testeurs | 30-50 personnes (amis, communautés, waitlist) |
| S26-S27 | Collecte de feedback | Formulaire + entretiens + analytics |
| S27-S28 | Itérations sur le feedback | Bug fixes, ajustements UX, contenu |
| S28-S29 | Beta ouverte | Élargir à 100-200 testeurs |
| S29 | Préparation lancement | ASO, description stores, marketing material |
| S30 | **LANCEMENT PUBLIC** 🚀 | Publication App Store + Google Play |
| S30 | Lancement Product Hunt | Post + engagement communauté |

**Total Phase 2 : ~80-100 heures**

---

## 5. Phase 3 — Post-Lancement & Croissance (Semaines 31-46)

### Version 1.1 (Should Have)

| Fonctionnalité | Effort | Priorité |
|----------------|--------|----------|
| Badges avancés (20+ badges) | 15h | P1 |
| Leaderboard hebdomadaire | 15h | P1 |
| Groupes thématiques + chat | 30h | P2 |
| Catégories de défis étendues | 10h | P1 |
| Historique complet des défis | 8h | P2 |
| Dashboard statistiques avancé | 12h | P2 |
| Améliorations algorithme recommandation | 20h | P1 |

### Activités Continues

| Activité | Fréquence | Heures/sem |
|----------|-----------|-----------|
| Curation de contenu (nouveaux reels) | Quotidien | 3-5h |
| Création de nouveaux défis | Hebdomadaire | 2h |
| Bug fixes & maintenance | Continue | 3-5h |
| Analyse métriques & itérations | Hebdomadaire | 2h |
| Community management | Quotidien | 2-3h |
| Marketing organique (réseaux sociaux, ASO) | 3x/semaine | 3h |

**Total Phase 3 : ~15-20h/semaine**

---

## 6. Phase 4 — Scale (Année 2+)

### Version 2.0 (Could Have)

| Fonctionnalité | Effort |
|----------------|--------|
| Messagerie privée 1-to-1 | 25h |
| Contenu généré par les utilisateurs (UGC) | 60h |
| Défis de groupe collaboratifs | 30h |
| Algorithme IA avancé (ML personnalisé) | 50h |
| Multi-langue (anglais) | 20h |
| Intégration Screen Time / Digital Wellbeing | 25h |
| Modèle premium complet | 20h |
| Thèmes personnalisables | 10h |

### Exploration B2B
| Initiative | Description |
|-----------|-------------|
| Programme entreprise | Offre de bien-être numérique pour les employés |
| Partenariats éducation | Intégration dans les universités |
| API contenu | Permettre à d'autres apps d'utiliser le contenu curé |

---

## 7. Diagramme de Gantt Simplifié

```
                    Mar  Avr  Mai  Jun  Jul  Aoû  Sep  Oct  Nov  Déc  Jan  Fév  Mar
                    2026 ──────────────────────────────────────────────────────── 2027

Phase 0: Prép.     ████
  Documentation     ██
  Design UI/UX       ████
  Base contenu       ███
  Landing page        ██

Phase 1: MVP Dev         ████████████████████████████████████████
  Fondations             ████
  Auth & Onboarding          ████
  Feed de Reels                  ████████████
  Défis & Gamification                       ████████
  Profil & Stats                                     ████████
  Backend & Tests                                            ████████

Phase 2: Beta & Launch                                               ████████████
  Beta fermée                                                        ████
  Beta ouverte                                                           ████
  LANCEMENT 🚀                                                              ██

Phase 3: Croissance                                                          ████████████████
  V1.1 features                                                              ████████
  Marketing & Growth                                                         ████████████████

Phase 4: Scale                                                                               ▶▶▶
```

---

## 8. Jalons Clés (Milestones)

| # | Jalon | Date Estimée | Critère de Succès |
|---|-------|-------------|-------------------|
| M0 | Documentation & Prep complètes | Fin Mars 2026 | Tous les docs créés, 100+ contenus curés |
| M1 | Auth + Questionnaire fonctionnel | Mi-Mai 2026 | Un utilisateur peut s'inscrire et remplir le questionnaire |
| M2 | Feed de Reels fonctionnel | Fin Juin 2026 | L'utilisateur peut scroller un feed de reels personnalisé |
| M3 | Défis + Gamification fonctionnels | Mi-Juillet 2026 | L'utilisateur peut voir/compléter des défis, gagner des XP |
| M4 | MVP complet | Fin Août 2026 | Toutes les fonctionnalités MVP intégrées et testées |
| M5 | Beta fermée lancée | Mi-Septembre 2026 | 30-50 beta testeurs actifs |
| M6 | **LANCEMENT PUBLIC** 🚀 | Fin Octobre 2026 | App publiée sur App Store + Google Play |
| M7 | 1 000 utilisateurs | Fin Décembre 2026 | 1K users actifs |
| M8 | Version 1.1 | Février 2027 | Groupes, leaderboard, badges avancés |
| M9 | Monétisation | Mars 2027 | Lancement offre Premium |

---

## 9. Métriques de Suivi du Projet

### Métriques de Développement

| Métrique | Cible | Fréquence |
|----------|-------|-----------|
| Vélocité (heures/semaine) | 15-20h | Hebdomadaire |
| Tâches complétées/sprint | 80%+ du plannifié | Par sprint |
| Couverture de tests | > 60% | Par sprint |
| Bugs ouverts critiques | < 3 | Continue |
| Retard par rapport au planning | < 1 semaine | Hebdomadaire |

### Métriques Produit (Post-Lancement)

| Métrique | Cible MVP | Cible 6 mois |
|----------|-----------|-------------|
| Téléchargements | 500 | 5 000 |
| DAU (Daily Active Users) | 100 | 1 000 |
| Rétention D1 | > 60% | > 60% |
| Rétention D7 | > 30% | > 35% |
| Rétention D30 | > 15% | > 20% |
| Défis complétés/jour/user | 0.5 | 0.8 |
| Reels vus/session | 10 | 15 |
| Temps moyen/session | 8 min | 12 min |
| NPS | > 30 | > 50 |
| Note App Store | > 4.0 | > 4.3 |

---

## 10. Outils de Gestion de Projet Recommandés

| Outil | Usage | Coût |
|-------|-------|------|
| **GitHub Projects** | Backlog, Kanban, sprints | Gratuit |
| **Notion** | Documentation, notes, décisions | Gratuit |
| **Figma** | Design UI/UX | Gratuit (starter) |
| **Firebase Console** | Monitoring, analytics | Gratuit (Spark) |
| **Sentry** | Monitoring erreurs en production | Gratuit (5K events/mois) |
| **Mixpanel** | Analytics produit avancées | Gratuit (< 100K events/mois) |

---

*Document généré dans le cadre de l'analyse du projet DetoxApp*
