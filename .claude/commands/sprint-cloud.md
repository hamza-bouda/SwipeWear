---
description: Cycle SwipeWear autonome, destiné aux exécutions cloud sans utilisateur présent pour valider
---

Cycle de travail **autonome** sur SwipeWear. Personne ne peut te répondre pendant cette exécution : tu ne poses pas de question, tu ne demandes pas de validation, et tu t'arrêtes proprement plutôt que de deviner.

## 0. Garde-fou anti-doublon — à faire en premier

Cette routine tourne toutes les heures et chaque exécution démarre sans mémoire des précédentes. Avant tout travail :

```bash
gh pr list --state open --json number,title,headRefName,createdAt
```

- S'il existe déjà une PR ouverte issue d'un cycle automatique (branche `KAN-*` ou `chore-*` créée par une exécution précédente) et qu'elle n'est pas fusionnée : **n'ouvre aucune nouvelle PR**. Fais uniquement l'audit (étape 1), mets à jour le plan, et termine ton rapport en disant que le cycle a été volontairement réduit à un audit parce qu'une PR attend une revue humaine.
- Sinon, continue.

Ceci évite d'empiler 24 PRs par jour qui se marchent dessus.

## 1. Audit

Appelle l'agent `chef-de-projet` (`Agent`, `subagent_type: "chef-de-projet"`, en synchrone). Il établit l'état réel du projet, détecte les écarts, et réécrit `.claude/orchestration/PLAN.md`.

Contexte à lui transmettre : **aucun connecteur Jira n'est disponible dans une exécution cloud.** Il doit donc s'appuyer sur `Backlog/PRODUCT_BACKLOG.md` (miroir, potentiellement périmé), l'historique git et l'état du code — et le dire explicitement dans son rapport au lieu de supposer l'état des tickets.

## 2. Exécution — une seule tâche par cycle

Prends **la tâche la plus prioritaire du plan, et elle seule.** Une exécution horaire n'est pas un sprint : mieux vaut une tâche terminée et prouvée que trois à moitié faites.

Ne prends pas la tâche, et passe à la suivante du plan, si elle :

- touche `contracts/` ou `evaluation/fixtures/` (zones protégées — accord humain obligatoire) ;
- change un modèle IA, un seuil validé ou le prix 4,99 € ;
- concerne une feature gelée (E12/E13 avant les gates, Icebox E14) ou le watcher Vinted ;
- exige une décision produit qui n'est écrite dans aucune source.

Si toutes les tâches du plan sont bloquées par un de ces motifs, ne fais rien d'autre que l'audit et dis-le.

Puis délègue à l'agent compétent (`backend-dev`, `mobile-dev`, `qa-test`, `deploy-redaction`) avec le ticket, les critères d'acceptation, les chemins concernés et les commandes de validation exactes.

## 3. Livraison

- Branche depuis `main` à jour, une branche pour la tâche, commits en anglais, **pas de co-auteur IA**.
- Ouvre une PR décrivant le problème constaté, la preuve, et ce que la PR change. Inclus la sortie réelle des commandes de validation dans le corps de la PR.
- **Jamais** de push sur `main`, jamais de `--force`, jamais de fusion — même si la CI est verte. La fusion reste une décision humaine.
- Aucun secret dans le code ni les commits.

## 4. Rapport final

En français, court et factuel :

1. Ce que l'audit a trouvé (les écarts, avec leur preuve).
2. La tâche prise, et la sortie réelle des commandes de validation. Si tu n'as pas pu exécuter quelque chose (base indisponible, dépendances `ai` absentes, modèle non téléchargé), dis-le — ne présente jamais un test sauté comme un test passé.
3. Le lien de la PR ouverte, s'il y en a une.
4. Ce qui a été volontairement écarté, et pourquoi.
5. Les questions qui attendent une réponse humaine.

Une tâche n'est « faite » que si une sortie de commande le prouve. Sans preuve, écris « non vérifié ».
