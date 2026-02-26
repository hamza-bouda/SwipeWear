# Équipe d'agents SwipeWear

| Agent | Modèle | Rôle | Périmètre |
|---|---|---|---|
| `chef-de-projet` | Opus | Orchestrateur : confronte code / doc / Jira / git, détecte les écarts, priorise, délègue | Ne code pas. Écrit `.claude/orchestration/PLAN.md` et `AMELIORATIONS.md` |
| `backend-dev` | Sonnet | FastAPI, Pydantic, Postgres + pgvector, modules IA, migrations | `backend/` |
| `mobile-dev` | Sonnet | React Native / Expo, écrans, navigation, appels API, vérif dans le preview | `mobile/` |
| `qa-test` | Sonnet | pytest, golden scenario, typecheck, traque des replis silencieux, budgets de latence | Tests seulement — ne corrige pas la feature |
| `deploy-redaction` | Sonnet | CI, Docker, Railway, landing + toute la documentation | `.github/`, `railway.toml`, `Documentation/`, journaux |

## Utilisation

- `/sprint` — cycle complet : point projet, plan, validation, exécution, compte rendu.
- `/sprint backend` — cycle limité à un périmètre.
- Ou en langage naturel : « fais un point projet », « quoi faire maintenant », « lance le chef de projet ».
- Pour une tâche déjà cadrée, on peut appeler directement l'agent d'exécution concerné.

## Règles communes encodées dans chaque agent

Elles viennent de `CLAUDE.md`, qui prime en cas de doute :

- `git pull origin main` **avant** de créer une branche ; une branche par ticket `KAN-<num>-...` ; jamais de commit sur `main` ; **pas de co-auteur IA dans les commits**.
- Contracts first ; `contracts/` et les fixtures du golden scenario sont des zones protégées (accord explicite requis).
- Vérification par **exécution réelle**, pas par suite verte : le projet a un historique de replis silencieux.
- Toute migration est journalisée dans `CLAUDE.md` §9 avant de clore la tâche.
- Doc et tickets en français, code et commits en anglais.
- Gels respectés : E12/E13 et Icebox E14 tant que les gates ne sont pas atteintes ; watcher Vinted désactivé.

## Note sur les modèles

Les agents d'exécution sont déclarés `model: sonnet`, qui résout vers le **dernier Sonnet disponible** (Claude Sonnet 5 dans cet environnement — il n'existe pas de « Sonnet 4.6 »). Pour épingler une version précise, remplacer l'alias par un identifiant complet dans le frontmatter de l'agent.

## Emplacement et versionnement

Cette copie est **versionnée dans le dépôt** (`.claude/agents/`, `.claude/commands/`, `.claude/orchestration/`), à l'inverse du reste de `.claude/` qui reste ignoré par git (voir `.gitignore`). C'est nécessaire pour deux raisons : un agent qui démarre sur une autre machine dispose de la même équipe, et une **routine cloud** qui clone le dépôt n'aurait sinon aucun agent à qui déléguer.

Tous les chemins de ces fichiers sont relatifs à la **racine du dépôt**. Une copie locale peut exister en dehors du dépôt (par exemple dans un dossier parent qui contient plusieurs projets) ; dans ce cas ses chemins sont préfixés autrement, et c'est cette copie-ci qui fait référence.

`.claude/orchestration/PLAN.md` est volontairement suivi par git : c'est ce qui rend le plan durable entre deux exécutions, y compris entre deux sessions cloud qui ne partagent aucune mémoire.
