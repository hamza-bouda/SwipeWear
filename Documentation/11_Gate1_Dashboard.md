# KAN-66 — Dashboard Gate 1 · Mesure et décision

**Objectif Gate 1 :** 300 inscrits waitlist confirmés **ET** 50 000 vues TikTok cumulées  
**Échéance :** S1 de publication TikTok + 6 semaines  
**Mise à jour :** chaque lundi matin (5 min)

---

## 1. Tableau hebdomadaire

Copier dans Google Sheets (une ligne par semaine).

| Semaine | Date | Vues cumulées | Inscrits confirmés | Taux conversion landing | Meilleure vidéo (angle) | Notes |
|---|---|---|---|---|---|---|
| S0 | 2026-07-28 | 0 | 0 | — | — | Lancement landing |
| S1 | 2026-08-04 | — | — | — | — | Vidéos 01–03 (Douleur) |
| S2 | 2026-08-11 | — | — | — | — | Vidéos 04–06 (Démo) |
| S3 | 2026-08-18 | — | — | — | — | Vidéos 07–08 (Économie) |
| S4 | 2026-08-25 | — | — | — | — | Vidéos 09–10 (Contrôle) |
| S5 | 2026-09-01 | — | — | — | — | Suivi post-10 vidéos |
| S6 | 2026-09-08 | — | — | — | — | **Décision Gate 1** |

**Taux de conversion landing** = inscrits_semaine / visites_landing × 100  
→ Lire dans Vercel Analytics ou Plausible (à configurer lors du déploiement)

---

## 2. Suivi par vidéo TikTok

| Vidéo | Angle | Date pub | Vues 24h | Vues totales | Likes | Partages | Clics bio | Inscriptions attribuées |
|---|---|---|---|---|---|---|---|---|
| 01 | Douleur | — | — | — | — | — | — | — |
| 02 | Douleur | — | — | — | — | — | — | — |
| 03 | Douleur | — | — | — | — | — | — | — |
| 04 | Démo | — | — | — | — | — | — | — |
| 05 | Démo | — | — | — | — | — | — | — |
| 06 | Démo | — | — | — | — | — | — | — |
| 07 | Économie | — | — | — | — | — | — | — |
| 08 | Économie | — | — | — | — | — | — | — |
| 09 | Contrôle | — | — | — | — | — | — | — |
| 10 | Contrôle | — | — | — | — | — | — | — |
| **TOTAL** | | | | | | | | |

**Inscriptions attribuées** = `SELECT COUNT(*) FROM waitlist WHERE utm_content = 'video_XX' AND confirmed = TRUE`  
(ou filtrer dans Vercel Analytics par `utm_content`)

---

## 3. Comment lire les métriques

### Signaux positifs
- Vues 24h > 500 → l'algo TikTok booste : répliquer l'angle immédiatement
- Taux conversion landing > 8 % → le message convertit bien
- Clics bio / Vues > 2 % → hook fort + bonne curiosité

### Signaux d'alerte
- Vues stagnent à < 200 malgré 3 vidéos → changer l'angle ou le format
- Clics bio élevés mais inscriptions faibles → la landing ne convainc pas

---

## 4. Décision Gate 1 — grille

**Réunion de décision à J+42 (6 semaines après la 1ère vidéo)**

### GO ✅
- Inscrits confirmés ≥ 300 **ET** vues cumulées ≥ 50 000
- Action : démarrer E6 (ranking), E7 (embeddings), E8 (affiliation), E9 (app mobile beta)

### PIVOT MESSAGE ⚠️
- Vues ≥ 50 000 **MAIS** inscrits < 300 (concept intrigue, promesse ne convertit pas)
- Action : identifier l'angle TikTok gagnant, retravailler le copy de la landing sur cet angle, refaire un cycle de 4 semaines
- Ne pas commencer E6-E9

### PIVOT PRODUIT 🔴
- Vues < 20 000 **ET** inscrits < 100 après 10 vidéos
- Action : organiser une session de discovery utilisateur (5 interviews), revoir la proposition de valeur avant toute ligne de code supplémentaire

---

## 5. Archive de la décision

À remplir le jour de la réunion Gate 1 et committer dans ce fichier.

```
Date de décision : YYYY-MM-DD
Décision : GO / PIVOT MESSAGE / PIVOT PRODUIT
Vues cumulées : X
Inscrits confirmés : X
Taux conversion global : X %
Meilleur angle TikTok : [angle] (vidéo XX — X vues, X inscriptions)
Raison de la décision : [3–5 lignes]
Prochaine étape : [action concrète]
```

---

## 6. Sources de données

| Donnée | Où la trouver |
|---|---|
| Vues TikTok | TikTok Studio → Analytics → chaque vidéo |
| Clics bio | TikTok Studio → Analytics → Profil → Clics site web |
| Visites landing | Vercel Analytics (à activer) ou `vercel analytics enable` |
| Inscriptions par UTM | `SELECT utm_content, COUNT(*) FROM waitlist WHERE confirmed=TRUE GROUP BY utm_content ORDER BY count DESC` |
| Inscriptions total | `GET /api/waitlist` → `{ count: N }` |
