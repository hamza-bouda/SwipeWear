# ⚠️ Analyse des Risques — DetoxApp

**Version :** 1.0  
**Date :** 01 Mars 2026  
**Auteur :** Chef de Projet  

---

## 1. Méthodologie

Chaque risque est évalué selon :
- **Probabilité (P)** : 1 (Très faible) à 5 (Très élevée)
- **Impact (I)** : 1 (Négligeable) à 5 (Critique)
- **Score de risque** = P × I (1-25)
- **Niveau** : 🟢 Faible (1-6) | 🟡 Moyen (7-12) | 🔴 Élevé (13-25)

---

## 2. Registre des Risques

### 2.1 Risques Techniques

| ID | Risque | P | I | Score | Niveau | Plan de Mitigation |
|----|--------|---|---|-------|--------|---------------------|
| RT01 | **Performance du feed vidéo insuffisante** — Lag, temps de chargement excessif, consommation mémoire | 3 | 5 | 15 | 🔴 | Préchargement, compression H.264, CDN, tests performance réguliers, fallback sur images si nécessaire |
| RT02 | **Algorithme de recommandation imprécis** — Contenu non pertinent pour l'utilisateur | 3 | 4 | 12 | 🟡 | MVP avec filtrage simple par tags, collecte de feedback utilisateur, itération fréquente |
| RT03 | **Scalabilité de l'infrastructure** — Le backend ne tient pas la charge en cas de croissance | 2 | 4 | 8 | 🟡 | Architecture serverless, auto-scaling cloud, load testing préventif |
| RT04 | **Bugs critiques en production** — Crash, perte de données, fonctionnalités cassées | 3 | 4 | 12 | 🟡 | CI/CD avec tests automatisés, Sentry pour monitoring, programme beta testing |
| RT05 | **Dépendance à des services tiers** — Firebase, OpenAI, CDN en panne ou changement de pricing | 2 | 4 | 8 | 🟡 | Architecture modulaire, abstractions, avoir un plan B pour chaque service |
| RT06 | **Compatibilité multi-appareils** — L'app ne fonctionne pas bien sur certains appareils | 3 | 3 | 9 | 🟡 | Tests sur émulateurs variés, Firebase Test Lab, beta testing multi-appareils |
| RT07 | **Sécurité des données** — Fuite de données, vulnérabilités | 2 | 5 | 10 | 🟡 | HTTPS partout, JWT sécurisé, audits de sécurité basiques, OWASP guidelines |

### 2.2 Risques Business / Marché

| ID | Risque | P | I | Score | Niveau | Plan de Mitigation |
|----|--------|---|---|-------|--------|---------------------|
| RB01 | **Manque d'adoption utilisateur** — Les gens ne téléchargent pas l'app | 3 | 5 | 15 | 🔴 | Validation du concept avant développement (landing page, sondage), beta fermée, communauté r/nosurf |
| RB02 | **Rétention faible** — Les utilisateurs partent après quelques jours | 4 | 5 | 20 | 🔴 | Gamification forte (streaks, récompenses), onboarding soigné, notifications intelligentes, contenu de qualité |
| RB03 | **Concurrence — Un géant copie le concept** (TikTok, Instagram) | 2 | 4 | 8 | 🟡 | Aller vite, créer une communauté fidèle, features avancées que les géants ne feront pas (défis off-screen) |
| RB04 | **Problème du contenu initial (cold start)** — Pas assez de contenu au lancement | 4 | 4 | 16 | 🔴 | Curer du contenu CC avant le lancement (min 200 reels), partenariats avec créateurs |
| RB05 | **Monétisation insuffisante** — Pas assez de conversions premium | 3 | 3 | 9 | 🟡 | Tester différentes offres, A/B testing du paywall, modèle "value-first" |
| RB06 | **Mauvais timing de marché** — La tendance bien-être numérique s'essouffle | 1 | 4 | 4 | 🟢 | Le problème du doom scrolling empire, pas de signe d'essoufflement |

### 2.3 Risques Opérationnels / Humains

| ID | Risque | P | I | Score | Niveau | Plan de Mitigation |
|----|--------|---|---|-------|--------|---------------------|
| RO01 | **Burnout du développeur solo** — Surcharge de travail, démotivation | 4 | 5 | 20 | 🔴 | Planning réaliste, 20h/semaine max, milestones courtes, prendre des pauses, célébrer les victoires |
| RO02 | **Scope creep** — Le projet grossit au-delà du réalisable | 4 | 4 | 16 | 🔴 | MVP strict, backlog priorisé (MoSCoW), dire NON aux features non essentielles |
| RO03 | **Manque de compétences spécifiques** — Design UI/UX, marketing, IA | 3 | 3 | 9 | 🟡 | Templates UI, communautés, tutoriels, API clé-en-main |
| RO04 | **Perte de données / Code** — Crash disque, perte du code source | 1 | 5 | 5 | 🟢 | Git (GitHub), sauvegardes automatiques, branches protégées |
| RO05 | **Modération du contenu insuffisante** — Contenu inapproprié, harcèlement | 3 | 4 | 12 | 🟡 | Phase 1 sans UGC, puis modération IA + signalement communautaire |

### 2.4 Risques Légaux / Réglementaires

| ID | Risque | P | I | Score | Niveau | Plan de Mitigation |
|----|--------|---|---|-------|--------|---------------------|
| RL01 | **Non-conformité RGPD** — Amende en cas de violation | 2 | 5 | 10 | 🟡 | Politique de confidentialité conforme, consentement explicite, droit de suppression, minimisation des données |
| RL02 | **Violation de propriété intellectuelle** — Utilisation de contenu protégé | 2 | 4 | 8 | 🟡 | Vérifier les licences, utiliser uniquement du contenu CC/libre, obtenir les droits écrits |
| RL03 | **Responsabilité contenu utilisateur** — Contenu illégal posté par des utilisateurs | 2 | 4 | 8 | 🟡 | CGU claires, système de signalement, modération proactive, réponse < 24h |
| RL04 | **Protection des mineurs** — Non-respect des lois sur les mineurs | 2 | 5 | 10 | 🟡 | Vérification d'âge, paramètres parentaux (V2), conformité KOSA/DSA |

---

## 3. Matrice des Risques (Heat Map)

```
Impact
  5 │  RO04    RT01,RB01  RO01,RB02
    │   🟢       🔴          🔴
  4 │  RB06    RT03,RT05  RT02,RT04   RB04,RO02
    │   🟢     RB03,RL02   RT06       🔴 🔴
    │           🟡 🟡      RO03,RO05
    │                       🟡 🟡
  3 │          RB05         
    │           🟡         
  2 │                       
    │                       
  1 │                       
    └──────────────────────────────────
    1      2       3       4       5
                 Probabilité
```

---

## 4. Top 5 des Risques Critiques

### 🔴 #1 — Rétention Faible (RB02) — Score : 20/25

**Pourquoi c'est critique :** Sans rétention, tout le reste (monétisation, communauté, croissance) s'effondre. C'est LE risque existentiel.

**Plan d'action détaillé :**
1. **Semaine 1-2 de l'utilisateur :** Onboarding exceptionnel, premiers défis faciles, premières victoires
2. **Gamification profonde :** Streaks (comme Duolingo), points quotidiens, niveaux avec récompenses visibles
3. **Engagement social :** "Ton ami X a complété un défi", groupes actifs
4. **Contenu de qualité maximale :** Mieux vaut 50 très bons reels que 500 médiocres
5. **Notifications ciblées :** Rappels de streak, nouveaux défis correspondant aux intérêts
6. **Mesure :** Tracker D1, D7, D30 retention, itérer chaque semaine

---

### 🔴 #2 — Burnout du Développeur (RO01) — Score : 20/25

**Pourquoi c'est critique :** Si le développeur abandonne, le projet meurt.

**Plan d'action détaillé :**
1. **Rythme soutenable :** Max 20h/semaine, planning réaliste
2. **Milestones courtes :** Célébrer chaque livraison (même petite)
3. **Variété des tâches :** Alterner entre code, design, contenu
4. **Pauses planifiées :** 1 semaine de pause toutes les 6 semaines
5. **Communauté :** Rejoindre des groupes de développeurs indépendants pour le soutien moral
6. **MVP réaliste :** Réduire le scope impitoyablement

---

### 🔴 #3 — Problème du Cold Start (RB04) — Score : 16/25

**Pourquoi c'est critique :** Sans contenu, pas d'expérience utilisateur, pas de rétention.

**Plan d'action détaillé :**
1. **Avant tout développement :** Constituer une base de 200+ reels curés
2. **Sources de contenu :** YouTube Creative Commons, Khan Academy, TED-Ed, CrashCourse
3. **30-50 reels/catégorie** minimum au lancement
4. **Pipeline de curation automatisé :** Script pour télécharger et formater du contenu CC
5. **Partenariats early :** Contacter 10-20 créateurs de contenu éducatif
6. **IA comme accélérateur :** Utiliser l'IA pour résumer et adapter du contenu existant

---

### 🔴 #4 — Scope Creep (RO02) — Score : 16/25

**Pourquoi c'est critique :** En solo, chaque feature ajoutée repousse le lancement de semaines.

**Plan d'action détaillé :**
1. **MVP strict défini :** Feed + Défis + Gamification de base = SUFFISANT
2. **Backlog MoSCoW rigide :** Must, Should, Could, Won't
3. **Règle des 2 semaines :** Toute feature qui prend > 2 semaines à développer n'est pas dans le MVP
4. **"Ship early, ship often"** : Lancer rapidement, itérer avec le feedback réel
5. **Tableau Kanban :** Limiter le WIP (Work In Progress) à 2 tâches max

---

### 🔴 #5 — Manque d'Adoption (RB01) — Score : 15/25

**Pourquoi c'est critique :** Si personne ne télécharge l'app, tout l'effort est gaspillé.

**Plan d'action détaillé :**
1. **Validation pré-développement :** Landing page + waitlist pour mesurer l'intérêt
2. **Community building :** Construire une micro-communauté (Reddit, Discord) avant le lancement
3. **Beta testing ouvert :** 50-100 beta testeurs engagés pour les premiers retours
4. **Product Hunt launch :** Préparer un lancement Product Hunt bien exécuté
5. **ASO (App Store Optimization) :** Mots-clés ciblés (doom scrolling, digital detox, etc.)
6. **Contenu viral :** Créer du contenu sur l'ironie d'utiliser TikTok pour promouvoir une app anti-TikTok

---

## 5. Plan de Contingence

| Scénario | Action si le risque se matérialise |
|----------|-----------------------------------|
| Le feed vidéo est trop complexe | Pivoter vers un feed de **cards/articles courts** (texte + image) au lieu de vidéos |
| L'IA est trop chère | Revenir à un système de tags/catégories manuelles |
| Aucun utilisateur après 3 mois | Pivoter vers un **widget/extension** qui s'intègre dans les apps existantes |
| Burnout | Mettre le projet en pause 1 mois, réduire le scope, chercher un co-fondateur |
| Un concurrent lance un produit identique | Se différencier par les défis off-screen et la communauté |
| Firebase augmente ses prix | Migrer vers Supabase (open-source) |

---

## 6. Indicateurs de Suivi des Risques (KRI)

| Indicateur | Seuil d'Alerte 🟡 | Seuil Critique 🔴 | Fréquence de Suivi |
|------------|-------------------|-------------------|---------------------|
| Rétention D7 | < 30% | < 15% | Hebdomadaire |
| Rétention D30 | < 15% | < 8% | Mensuelle |
| Téléchargements/semaine | < 20 | < 5 | Hebdomadaire |
| Heures de travail/semaine | > 25h | > 35h | Hebdomadaire |
| Bugs critiques ouverts | > 3 | > 5 | Continue |
| Coûts infra/mois | > 2x prévision | > 3x prévision | Mensuelle |
| NPS (Net Promoter Score) | < 30 | < 10 | Mensuelle |

---

## 7. Conclusion

| Catégorie | Risques Élevés | Risques Moyens | Risques Faibles |
|-----------|---------------|----------------|-----------------|
| Technique | 1 | 5 | 0 |
| Business | 3 | 2 | 1 |
| Opérationnel | 2 | 2 | 1 |
| Légal | 0 | 4 | 0 |
| **TOTAL** | **6** | **13** | **2** |

> **Le projet présente 6 risques élevés, principalement liés à la rétention, au contenu initial, et à la gestion du développeur solo.** Tous ces risques sont **mitigables** avec une approche disciplinée : MVP minimal, contenu curé en amont, gamification forte, et rythme de travail soutenable. **Aucun risque n'est éliminatoire** — le projet reste viable.

---

*Document généré dans le cadre de l'analyse du projet DetoxApp*
