# 💼 Business Model Canvas — DetoxApp

**Version :** 1.0  
**Date :** 01 Mars 2026  
**Auteur :** Chef de Projet  

---

## Business Model Canvas (Vue Globale)

```
┌──────────────────┬──────────────────┬──────────────────┬──────────────────┬──────────────────┐
│                  │                  │                  │                  │                  │
│  8. PARTENAIRES  │ 7. ACTIVITÉS     │ 2. PROPOSITION   │ 4. RELATION      │ 1. SEGMENTS      │
│     CLÉS         │    CLÉS          │    DE VALEUR     │    CLIENT        │    CLIENTS       │
│                  │                  │                  │                  │                  │
│ • Créateurs de   │ • Dév. & maint.  │                  │ • Onboarding     │ • Étudiants      │
│   contenu éduc.  │   de l'app       │ "Transformez     │   personnalisé   │   (18-25)        │
│ • API IA (OpenAI)│ • Curation de    │  votre temps     │ • Défis quotid.  │ • Jeunes pro     │
│ • Services Cloud │   contenu        │  d'écran en      │   (engagement)   │   (25-35)        │
│   (Firebase,AWS) │ • Animation      │  temps de        │ • Communauté     │ • Ados conscients│
│ • Influenceurs   │   communauté     │  croissance      │   de soutien     │   (15-18)        │
│   bien-être      │ • Amélioration   │  personnelle"    │ • Notifications  │                  │
│ • Universités /  │   algorithme IA  │                  │   intelligentes  │                  │
│   écoles         │ • Marketing &    │ • Feed éducatif  │ • Support        │                  │
│                  │   acquisition    │   personnalisé   │   in-app         │                  │
│                  │                  │ • Défis quotid.  │                  │                  │
│                  │                  │ • Gamification   │                  │                  │
│                  │                  │ • Communauté     │                  │                  │
│                  ├──────────────────┤                  ├──────────────────┤                  │
│                  │                  │                  │                  │                  │
│                  │ 6. RESSOURCES    │                  │ 3. CANAUX DE     │                  │
│                  │    CLÉS          │                  │    DISTRIBUTION  │                  │
│                  │                  │                  │                  │                  │
│                  │ • Code source    │                  │ • App Store      │                  │
│                  │ • Base de        │                  │ • Google Play    │                  │
│                  │   contenu curé   │                  │ • Réseaux sociaux│                  │
│                  │ • Algorithme IA  │                  │ • Bouche-à-      │                  │
│                  │ • Communauté     │                  │   oreille        │                  │
│                  │   d'utilisateurs │                  │ • Product Hunt   │                  │
│                  │ • Données        │                  │ • SEO/ASO        │                  │
│                  │   utilisateurs   │                  │ • Partenariats   │                  │
│                  │                  │                  │                  │                  │
├──────────────────┴──────────────────┴──────────┬───────┴──────────────────┴──────────────────┤
│                                                │                                            │
│ 9. STRUCTURE DE COÛTS                          │ 5. SOURCES DE REVENUS                      │
│                                                │                                            │
│ • Infrastructure cloud (hébergement, CDN)      │ • Abonnement Premium (4,99€/mois)          │
│ • API IA (OpenAI, coût par requête)            │ • Contenu sponsorisé éducatif               │
│ • Comptes développeur (Apple + Google)         │ • Partenariats B2B (entreprises)            │
│ • Stockage et bande passante vidéo              │ • Achat in-app (badges, thèmes)             │
│ • Outils de développement                       │ • Programme d'affiliation                    │
│ • Marketing (si budget disponible)              │                                            │
│                                                │                                            │
└────────────────────────────────────────────────┴────────────────────────────────────────────┘
```

---

## Détail de Chaque Bloc

### 1. Segments de Clients

#### Segment Principal : Jeunes adultes (18-35 ans) conscients du doom scrolling

| Sous-segment | Taille estimée | Disposition à payer | Priorité |
|-------------|---------------|-------------------|----------|
| **Étudiants (18-25)** | Grande | Faible (budget limité) | ⭐⭐⭐⭐⭐ (volume) |
| **Jeunes professionnels (25-35)** | Moyenne | Moyenne-Haute | ⭐⭐⭐⭐⭐ (valeur) |
| **Adolescents conscients (15-18)** | Moyenne | Très faible (parents paient) | ⭐⭐⭐ |
| **Parents inquiets** | Petite | Haute | ⭐⭐ (V2) |
| **Entreprises (B2B)** | Petite | Très haute | ⭐⭐ (V3) |

#### Jobs-to-be-Done (Travaux à Accomplir)

| Job | Type | Priorité |
|-----|------|----------|
| "Je veux arrêter de perdre mon temps sur TikTok" | Fonctionnel | ⭐⭐⭐⭐⭐ |
| "Je veux apprendre des choses intéressantes facilement" | Fonctionnel | ⭐⭐⭐⭐⭐ |
| "Je veux sortir de ma zone de confort" | Émotionnel | ⭐⭐⭐⭐ |
| "Je veux me sentir productif et fier de moi" | Émotionnel | ⭐⭐⭐⭐⭐ |
| "Je veux rencontrer des gens qui partagent mes objectifs" | Social | ⭐⭐⭐ |

---

### 2. Proposition de Valeur

#### Value Proposition Canvas

```
┌─────────────────────────────────────────────────┐
│              PROPOSITION DE VALEUR               │
├─────────────────────────────────────────────────┤
│                                                  │
│  Créateurs de Gains :                           │
│  ✦ Contenu éducatif format TikTok               │
│  ✦ Défis quotidiens motivants                   │
│  ✦ Progression visible (gamification)           │
│  ✦ Communauté de soutien                        │
│  ✦ IA qui comprend tes intérêts                 │
│                                                  │
│  Soulageurs de Douleurs :                       │
│  ✦ Remplace le doom scrolling (pas bloque)      │
│  ✦ Pas besoin de volonté surhumaine             │
│  ✦ Rappels bienveillants (pas culpabilisants)   │
│  ✦ Contenu pré-filtré (pas de déchets)          │
│                                                  │
│  Produits & Services :                          │
│  ✦ App mobile (Android + iOS)                   │
│  ✦ Feed de reels personnalisé                   │
│  ✦ Système de défis journaliers                 │
│  ✦ Messagerie & groupes thématiques             │
│  ✦ Dashboard de progression                     │
│                                                  │
└─────────────────────────────────────────────────┘
          ⬍  FIT  ⬍
┌─────────────────────────────────────────────────┐
│               PROFIL CLIENT                      │
├─────────────────────────────────────────────────┤
│                                                  │
│  Gains Recherchés :                             │
│  ✦ Se sentir productif                          │
│  ✦ Apprendre chaque jour                        │
│  ✦ Avoir plus de confiance en soi               │
│  ✦ Vie sociale plus riche                       │
│  ✦ Fierté personnelle                           │
│                                                  │
│  Douleurs :                                     │
│  ✦ Perte de temps incontrôlée                   │
│  ✦ Culpabilité après le scrolling               │
│  ✦ Contenu toxique / inutile                    │
│  ✦ Isolement social                             │
│  ✦ Manque de motivation                         │
│                                                  │
│  Tâches du Client :                             │
│  ✦ Utiliser son téléphone pendant les pauses    │
│  ✦ S'occuper pendant les transports             │
│  ✦ Se détendre avant de dormir                  │
│  ✦ Apprendre de nouvelles compétences           │
│                                                  │
└─────────────────────────────────────────────────┘
```

---

### 3. Canaux de Distribution

| Canal | Phase | Coût | Efficacité Attendue |
|-------|-------|------|---------------------|
| **Google Play Store** | MVP | 25€ (unique) | ⭐⭐⭐⭐ |
| **Apple App Store** | MVP | 99€/an | ⭐⭐⭐⭐ |
| **Bouche-à-oreille** | MVP | Gratuit | ⭐⭐⭐⭐ |
| **Product Hunt** | Lancement | Gratuit | ⭐⭐⭐⭐⭐ |
| **Reddit (r/nosurf, r/digitalminimalism)** | MVP | Gratuit | ⭐⭐⭐⭐⭐ |
| **Instagram/TikTok (ironie marketing)** | Lancement | Gratuit-$$ | ⭐⭐⭐⭐ |
| **ASO (App Store Optimization)** | Continu | Gratuit | ⭐⭐⭐⭐ |
| **Blog / SEO** | Post-lancement | Gratuit (temps) | ⭐⭐⭐ |
| **Partenariats influenceurs** | Croissance | Variable | ⭐⭐⭐ |
| **Presse tech** | Lancement | Gratuit (PR) | ⭐⭐⭐ |

---

### 4. Relation Client

| Type de Relation | Description | Phase |
|-----------------|-------------|-------|
| **Self-service** | L'app fonctionne de manière autonome | MVP |
| **Communauté** | Groupes thématiques, entraide entre utilisateurs | MVP |
| **Automatisée** | Notifications personnalisées, recommandations IA | MVP |
| **Support** | FAQ, email support | MVP |
| **Co-création** | Les utilisateurs créent et partagent du contenu et des défis | V2 |

---

### 5. Sources de Revenus

#### Modèle recommandé : FREEMIUM

##### Offre Gratuite (Free)
| Fonctionnalité | Limitation |
|----------------|-----------|
| Feed de reels éducatifs | Limité à 30 reels/jour |
| Défis quotidiens | 1 défi/jour |
| Profil & statistiques de base | Basique |
| 1 groupe thématique | Max 1 groupe |

##### Offre Premium (4,99€/mois ou 39,99€/an)
| Fonctionnalité | Détail |
|----------------|--------|
| Feed illimité | Pas de limite quotidienne |
| Défis illimités | Multiples défis/jour + personnalisés IA |
| Statistiques avancées | Graphiques détaillés, exportation |
| Groupes illimités | Créer et rejoindre sans limite |
| Messagerie privée | Conversations individuelles |
| Badges exclusifs | Collection premium |
| Thèmes de l'app | Personnalisation visuelle |
| Contenu premium | Accès à des reels exclusifs |
| Sans publicité | Aucune publicité |

##### Revenus Additionnels Potentiels

| Source | Description | Revenus Estimés |
|--------|-------------|-----------------|
| **Contenu sponsorisé éducatif** | Marques/universités sponsorisent des reels | 500-2000€/mois (à 10K users) |
| **Partenariats B2B** | Programme bien-être en entreprise | 200-1000€/entreprise/mois |
| **Achats in-app** | Badges spéciaux, boosters de défis | Variable |
| **Données anonymisées** | Insights sur les habitudes numériques | Potentiel V3 |

##### Projection de Revenus (Scénario Réaliste)

| Mois | Utilisateurs | % Premium | Revenus Abonnement | Revenus Sponsoring | Total |
|------|-------------|-----------|--------------------|--------------------|-------|
| M6 | 1 000 | 3% | 150€ | 0€ | 150€ |
| M12 | 5 000 | 5% | 1 250€ | 500€ | 1 750€ |
| M18 | 15 000 | 6% | 4 500€ | 1 500€ | 6 000€ |
| M24 | 30 000 | 7% | 10 500€ | 3 000€ | 13 500€ |
| M36 | 100 000 | 8% | 40 000€ | 10 000€ | 50 000€ |

---

### 6. Ressources Clés

| Ressource | Type | Criticité |
|-----------|------|-----------|
| **Code source Flutter** | Intellectuelle | ⭐⭐⭐⭐⭐ |
| **Base de contenu curé** | Intellectuelle | ⭐⭐⭐⭐⭐ |
| **Algorithme de recommandation** | Intellectuelle | ⭐⭐⭐⭐ |
| **Données utilisateurs** | Data | ⭐⭐⭐⭐ |
| **Communauté d'utilisateurs** | Humaine | ⭐⭐⭐⭐ |
| **Infrastructure cloud** | Physique | ⭐⭐⭐⭐ |
| **Compétences du développeur** | Humaine | ⭐⭐⭐⭐⭐ |

---

### 7. Activités Clés

| Activité | Fréquence | Importance |
|----------|-----------|------------|
| Développement & maintenance de l'app | Continue | ⭐⭐⭐⭐⭐ |
| Curation/création de contenu | Quotidienne | ⭐⭐⭐⭐⭐ |
| Amélioration de l'algorithme | Hebdomadaire | ⭐⭐⭐⭐ |
| Animation de la communauté | Quotidienne | ⭐⭐⭐⭐ |
| Marketing & acquisition | Continue | ⭐⭐⭐⭐ |
| Support utilisateur | Continue | ⭐⭐⭐ |
| Création de nouveaux défis | Hebdomadaire | ⭐⭐⭐⭐ |
| Analyse des métriques | Hebdomadaire | ⭐⭐⭐⭐ |

---

### 8. Partenaires Clés

| Partenaire | Rôle | Phase |
|-----------|------|-------|
| **Google (Firebase)** | Infrastructure, auth, analytics | MVP |
| **OpenAI / Google (Gemini)** | Moteur IA pour recommandations et contenu | MVP |
| **Créateurs de contenu éducatif** | Production de reels de qualité | V1-V2 |
| **Influenceurs bien-être / productivité** | Distribution, crédibilité | Lancement |
| **Universités / Écoles** | Partenariats éducatifs, distribution | V2 |
| **Entreprises (RH / Bien-être)** | Programme B2B | V3 |
| **Psychologues / Coachs** | Crédibilité scientifique, contenu expert | V2 |

---

### 9. Structure de Coûts

#### Coûts Fixes

| Poste | Mensuel | Annuel |
|-------|---------|--------|
| Compte développeur Apple | 8,25€ | 99€ |
| Domaine web | 1€ | 12€ |
| Outils de design (Figma Free) | 0€ | 0€ |
| **Total fixe** | **~10€** | **~111€** |

#### Coûts Variables (selon usage)

| Poste | 1K users | 10K users | 100K users |
|-------|----------|-----------|------------|
| Hébergement backend | 7€ | 50€ | 300€ |
| Base de données | 0-25€ | 50€ | 200€ |
| Stockage vidéo + CDN | 5€ | 50€ | 500€ |
| API IA | 10€ | 100€ | 1 000€ |
| Firebase (messages, notifications) | 0€ | 25€ | 200€ |
| **Total variable** | **~22-47€** | **~275€** | **~2 200€** |

#### Ratio Coûts/Revenus Cible

| Phase | Coûts | Revenus | Marge |
|-------|-------|---------|-------|
| MVP (0-1K users) | ~50€/mois | 0-150€ | -50 à +100€ |
| Croissance (1-10K) | ~300€/mois | 1 000-5 000€ | +700 à +4 700€ |
| Scale (10K-100K) | ~2 500€/mois | 10 000-50 000€ | +7 500 à +47 500€ |

---

## Analyse de Viabilité du Business Model

### Points Forts du Modèle
1. **Coûts d'entrée très faibles** : < 500€ pour le MVP
2. **Économie d'échelle** : les coûts croissent lentement vs. les revenus
3. **Multiple sources de revenus** : pas de dépendance unique
4. **Network effects** : plus d'utilisateurs = plus de contenu = plus de valeur

### Points de Vigilance
1. **Conversion gratuit → premium** : le taux de 5% est optimiste, la moyenne des apps est 2-3%
2. **Rétention** : la clé du modèle freemium
3. **Contenu** : coût de production/curation en continu
4. **Time-to-revenue** : 6-12 mois avant les premiers revenus significatifs

### Verdict

> **Le business model est viable.** Le modèle freemium avec contenu sponsorisé offre un bon équilibre entre accessibilité et monétisation. Le point de break-even est atteignable à ~3 000 utilisateurs actifs, ce qui est réaliste dans les 12 premiers mois.

---

*Document généré dans le cadre de l'analyse du projet DetoxApp*
