---
description: Lance un cycle de travail SwipeWear — le chef de projet fait le point, planifie et délègue aux agents d'exécution
argument-hint: [périmètre optionnel, ex. "backend" ou "KAN-93"]
---

Lance un cycle de travail sur SwipeWear.

Périmètre demandé : $ARGUMENTS (si vide : cycle complet, tout le projet).

Étapes :

1. Appelle l'agent `chef-de-projet` (`Agent` avec `subagent_type: "chef-de-projet"`, en synchrone) pour qu'il établisse l'état réel du projet, détecte les écarts, et écrive le plan dans `.claude/orchestration/PLAN.md`.
2. Présente-moi le plan avant toute exécution : tâches, agent assigné, et pourquoi maintenant. Si une tâche touche `contracts/`, les fixtures du golden scenario, ou une décision figée, signale-le explicitement — elle attend mon accord.
3. Une fois que j'ai validé, fais exécuter les tâches par les agents concernés (`backend-dev`, `mobile-dev`, `qa-test`, `deploy-redaction`). Deux tâches ne tournent en parallèle que si elles sont dans des lanes différentes et ne partagent aucun fichier.
4. Rends compte en français : ce qui a été fait avec la preuve d'exécution réelle rapportée, ce qui a échoué ou été laissé de côté, et les 3 prochaines tâches proposées.

Ne déclare aucune tâche terminée sans sortie de commande à l'appui.
