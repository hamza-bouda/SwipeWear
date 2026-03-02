# ⚙️ Analyse de Faisabilité — DetoxApp

**Version :** 1.0  
**Date :** 01 Mars 2026  
**Auteur :** Chef de Projet  

---

## 1. Faisabilité Technique

### 1.1 Évaluation par Module

| Module | Complexité | Faisabilité Solo | Technologies | Durée Estimée |
|--------|-----------|------------------|--------------|---------------|
| **Onboarding & Auth** | 🟢 Faible | ✅ Facile | Flutter + Firebase Auth | 1-2 semaines |
| **Feed de Reels** | 🔴 Élevée | ⚠️ Ambitieux | Flutter video_player + Backend streaming | 4-6 semaines |
| **Algorithme de recommandation** | 🔴 Élevée | ⚠️ Ambitieux | Python ML / API OpenAI | 3-5 semaines |
| **Système de défis** | 🟡 Moyenne | ✅ Faisable | Flutter + Backend CRUD | 2-3 semaines |
| **Gamification** | 🟡 Moyenne | ✅ Faisable | Flutter + Backend | 2-3 semaines |
| **Messagerie** | 🟡 Moyenne | ✅ Faisable | Firebase Firestore / Stream | 2-4 semaines |
| **Profil & Stats** | 🟢 Faible | ✅ Facile | Flutter + Backend | 1-2 semaines |
| **Notifications Push** | 🟢 Faible | ✅ Facile | Firebase Cloud Messaging | 1 semaine |
| **Backend API** | 🟡 Moyenne | ✅ Faisable | Node.js/FastAPI + PostgreSQL | 3-4 semaines |
| **Infra & Déploiement** | 🟡 Moyenne | ✅ Faisable | Docker + Cloud | 1-2 semaines |

### 1.2 Défis Techniques Majeurs

#### Défi 1 : Feed Vidéo Performant
**Problème :** Créer un feed de vidéos courtes fluide comme TikTok est techniquement complexe.

**Solution :**
- Utiliser le package `video_player` Flutter avec préchargement (buffer 2-3 vidéos en avance)
- Compression vidéo côté serveur (FFmpeg) : format H.264, résolution adaptative
- CDN pour réduire la latence (CloudFront, Cloudflare R2)
- Pagination infinie avec chargement paresseux

**Verdict :** ✅ Faisable — Des packages Flutter matures existent. Le principal défi est l'optimisation de performance.

#### Défi 2 : Algorithme de Recommandation
**Problème :** Personnaliser le contenu pour chaque utilisateur nécessite un moteur de recommandation.

**Options :**

| Option | Avantages | Inconvénients | Recommandé ? |
|--------|-----------|---------------|--------------|
| **A) Filtrage collaboratif simple** | Simple, bien documenté | Nécessite beaucoup de données | ⚠️ V2 |
| **B) Filtrage basé contenu** | Fonctionne avec peu de données | Bulle de filtre | ✅ MVP |
| **C) API OpenAI / LLM** | Puissant, rapide à implémenter | Coût par requête, dépendance | ✅ MVP |
| **D) Système hybride** | Meilleur résultat | Complexe | ⚠️ V2 |

**Recommandation MVP :** Commencer avec **B + C** (filtrage basé contenu + enrichissement IA), puis évoluer vers D.

#### Défi 3 : Source du Contenu Vidéo
**Problème :** D'où viendra le contenu initial ?

| Source | Faisabilité | Qualité | Coût | Recommandation |
|--------|-------------|---------|------|----------------|
| **Contenu curé (YouTube/CC)** | 🟢 Haute | 🟡 Variable | Gratuit | ✅ Phase 1 |
| **Généré par IA (Synthesia, HeyGen)** | 🟡 Moyenne | 🟡 Moyenne | $-$$ | ⚠️ Phase 2 |
| **Créé manuellement** | 🔴 Faible (solo) | 🟢 Haute | Temps | ⚠️ Limité |
| **UGC (User Generated Content)** | 🔴 Faible (cold start) | 🟡 Variable | Gratuit | ✅ Phase 3 |
| **Partenariats créateurs** | 🟡 Moyenne | 🟢 Haute | Variable | ✅ Phase 2 |

**Recommandation :** Phase 1 = Contenu curé (vidéos Creative Commons + contenu éducatif libre). Phase 2 = Partenariats + IA. Phase 3 = UGC.

#### Défi 4 : Modération du Contenu
**Problème :** Si les utilisateurs peuvent poster du contenu, il faut modérer.

**Solution progressive :**
1. **Phase 1 (MVP)** : Contenu curé uniquement → pas de modération nécessaire
2. **Phase 2** : UGC avec modération automatique (Google Cloud Vision API / OpenAI Moderation API)
3. **Phase 3** : Modération communautaire (système de signalement + modérateurs bénévoles)

**Verdict :** ✅ Faisable en commençant sans UGC.

### 1.3 Stack Technique Recommandée

```
┌─────────────────────────────────────────────────┐
│                    FRONTEND                       │
│  Flutter 3.x (Dart)                               │
│  State Management: Riverpod / Bloc               │
│  Navigation: GoRouter                             │
│  Video: video_player + chewie                     │
│  UI: Material Design 3 + Custom widgets          │
└─────────────────────┬───────────────────────────┘
                      │ HTTPS / WebSocket
┌─────────────────────▼───────────────────────────┐
│                    BACKEND                        │
│  Option A: Node.js + Express + TypeScript         │
│  Option B: Python + FastAPI (meilleur pour IA)    │
│  ORM: Prisma (Node) / SQLAlchemy (Python)        │
│  Auth: JWT + Firebase Auth                        │
│  API: REST + WebSocket (chat)                     │
└─────────┬───────────┬───────────┬───────────────┘
          │           │           │
┌─────────▼──┐ ┌──────▼────┐ ┌───▼──────────────┐
│ PostgreSQL │ │  Redis    │ │ Firebase         │
│ (données   │ │ (cache,   │ │ (Auth, Firestore,│
│  principales│ │ sessions) │ │  FCM, Storage)   │
│)           │ │           │ │                  │
└────────────┘ └───────────┘ └──────────────────┘
          │
┌─────────▼───────────────────────────────────────┐
│           SERVICES EXTERNES                       │
│  • CDN: Cloudflare R2 / AWS CloudFront           │
│  • IA: OpenAI API / Gemini API                    │
│  • Vidéo Processing: FFmpeg (auto-hébergé)       │
│  • Analytics: Firebase Analytics + Mixpanel       │
│  • Monitoring: Sentry                             │
│  • CI/CD: GitHub Actions                          │
└─────────────────────────────────────────────────┘
```

### 1.4 Verdict Faisabilité Technique

| Critère | Score | Commentaire |
|---------|-------|-------------|
| Frontend Flutter | ⭐⭐⭐⭐⭐ | Excellent choix pour cross-platform solo |
| Backend API | ⭐⭐⭐⭐ | Standard, bien documenté |
| Feed vidéo | ⭐⭐⭐ | Ambitieux mais réalisable avec simplifications |
| Algo recommandation | ⭐⭐⭐ | Commencer simple, itérer |
| Messagerie | ⭐⭐⭐⭐ | Solutions clé-en-main disponibles (Firebase, Stream) |
| Infrastructure | ⭐⭐⭐⭐ | Tiers gratuits suffisants pour le MVP |

**Score technique global : 3.8/5 — Projet techniquement réalisable, mais nécessite des simplifications stratégiques pour le MVP.**

---

## 2. Faisabilité Économique

### 2.1 Coûts Estimés — Phase MVP (6-8 mois)

| Poste | Service | Coût Mensuel | Coût Total (8 mois) |
|-------|---------|-------------|---------------------|
| **Hébergement Backend** | Railway / Render (tier gratuit → starter) | 0-7€ | 0-56€ |
| **Base de données** | Supabase Free → Pro | 0-25€ | 0-200€ |
| **Firebase** | Spark (gratuit) | 0€ | 0€ |
| **Stockage vidéo** | Cloudflare R2 (10GB gratuit) | 0-5€ | 0-40€ |
| **CDN** | Cloudflare (gratuit) | 0€ | 0€ |
| **IA/API** | OpenAI API (usage modéré) | 5-20€ | 40-160€ |
| **Domaine** | .com ou .app | 1€/mois | 12€ |
| **Compte développeur** | Google Play (25€ unique) + Apple (99€/an) | — | 124€ |
| **Outils Design** | Figma (gratuit) | 0€ | 0€ |
| **Divers** | Certificats, services annexes | 5€ | 40€ |

| | **TOTAL ESTIMATION** | | **~220€ - 630€** |

### 2.2 Coûts Estimés — Phase Croissance (1000+ utilisateurs)

| Poste | Coût Mensuel |
|-------|-------------|
| Hébergement Backend | 25-50€ |
| Base de données | 25-50€ |
| Stockage + CDN vidéo | 30-100€ |
| Firebase (Blaze) | 20-50€ |
| API IA | 50-200€ |
| **TOTAL** | **150-450€/mois** |

### 2.3 Modèle de Rentabilité

| Scénario | Utilisateurs Actifs | Conversion Premium (5%) | Revenu Mensuel | Marge |
|----------|--------------------|-----------------------|---------------|-------|
| **Pessimiste** | 1 000 | 50 | 250€ (à 4,99€/mois) | ~0€ |
| **Réaliste** | 5 000 | 250 | 1 250€ | +800€ |
| **Optimiste** | 20 000 | 1 000 | 4 990€ | +4 500€ |

### 2.4 Verdict Faisabilité Économique

**Score : 4/5 — Très faible investissement initial.** Le projet peut être lancé avec moins de 500€ et devenir rentable à partir de ~3 000 utilisateurs actifs avec un modèle freemium.

---

## 3. Faisabilité Opérationnelle

### 3.1 Compétences Requises vs. Disponibles

| Compétence | Requise | Disponible | Gap | Solution |
|------------|---------|------------|-----|----------|
| Développement Flutter | ✅ | ✅ | Aucun | — |
| Backend Development | ✅ | À confirmer | Faible | Tutoriels, Firebase |
| UI/UX Design | ✅ | ⚠️ Basique | Moyen | Templates, Figma community |
| Machine Learning/IA | ✅ | ⚠️ Basique | Moyen | APIs clé-en-main (OpenAI) |
| DevOps/Infrastructure | ✅ | ⚠️ Basique | Faible | Services managés |
| Marketing/Growth | ✅ | ❌ Non | Élevé | Communautés, ASO, contenu organique |
| Création de contenu | ✅ | ⚠️ Basique | Élevé | Curation + IA + partenariats |

### 3.2 Charge de Travail Estimée

En tant que développeur solo travaillant à temps partiel (~20h/semaine) :

| Phase | Durée | Effort |
|-------|-------|--------|
| Analyse & Design | 3-4 semaines | 60-80h |
| Développement MVP | 16-24 semaines | 320-480h |
| Tests & QA | 3-4 semaines | 60-80h |
| Lancement & Itérations | Continu | 10-15h/semaine |

**Total jusqu'au MVP : ~440-640 heures (~5-8 mois à 20h/semaine)**

### 3.3 Verdict Faisabilité Opérationnelle

**Score : 3.5/5 — Faisable en solo** mais il faudra être très discipliné, prioriser impitoyablement, et utiliser des solutions clé-en-main autant que possible. Le gap le plus important est la création de contenu et le marketing.

---

## 4. Faisabilité Légale (RGPD & Réglementaire)

### 4.1 Obligations RGPD

| Obligation | Nécessaire | Effort |
|------------|-----------|--------|
| Politique de confidentialité | ✅ Obligatoire | Faible (générateurs en ligne) |
| Consentement cookies/tracking | ✅ Obligatoire | Faible |
| Droit de suppression des données | ✅ Obligatoire | Moyen |
| Droit de portabilité | ✅ Obligatoire | Moyen |
| Registre des traitements | ✅ Si +250 employés ou données sensibles | Faible |
| DPO (Data Protection Officer) | ❌ Non requis (petite structure) | — |

### 4.2 Considérations Spécifiques

| Sujet | Risque | Mitigation |
|-------|--------|-----------|
| Données de mineurs (< 16 ans) | 🔴 Élevé | Vérification d'âge à l'inscription, consentement parental |
| Données de santé mentale | 🟡 Moyen | Ne pas collecter de données médicales directement |
| Contenu généré par les utilisateurs | 🟡 Moyen | CGU claires, système de signalement |
| Propriété intellectuelle du contenu | 🟡 Moyen | Utiliser du contenu CC, obtenir les droits |

### 4.3 Verdict Faisabilité Légale

**Score : 4/5 — Aucun obstacle légal majeur** à condition de respecter le RGPD et d'être transparent avec les utilisateurs. Un générateur de politique de confidentialité et des CGU bien rédigés suffisent pour le MVP.

---

## 5. Synthèse Globale de Faisabilité

| Dimension | Score | Verdict |
|-----------|-------|---------|
| **Technique** | 3.8/5 | ✅ Faisable avec simplifications |
| **Économique** | 4.0/5 | ✅ Très faible investissement requis |
| **Opérationnelle** | 3.5/5 | ⚠️ Faisable mais ambitieux en solo |
| **Légale** | 4.0/5 | ✅ Pas de blocage |
| **GLOBAL** | **3.8/5** | **✅ PROJET FAISABLE** |

### Recommandation Finale

> **Le projet DetoxApp est faisable.** Les principaux risques sont liés à l'exécution en solo (charge de travail, diversité des compétences requises) et au contenu initial. Il est fortement recommandé de :
> 1. **Commencer par un MVP très ciblé** (feed + défis, sans messagerie)
> 2. **Utiliser des services managés** pour minimiser l'effort DevOps
> 3. **Résoudre le problème du contenu initial** avant de coder (curation)
> 4. **Itérer rapidement** grâce au hot reload Flutter

---

*Document généré dans le cadre de l'analyse du projet DetoxApp*
