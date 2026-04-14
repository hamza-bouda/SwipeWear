# KAN-83 — Déploiement backend FastAPI sur Railway

## Architecture
- **Backend** : FastAPI (uvicorn) → Railway service (Docker)
- **Base de données** : PostgreSQL + pgvector → Railway PostgreSQL add-on
- **Migrations** : `scripts/run_migrations.py` (lancé automatiquement au démarrage)

---

## 1. Prérequis

- Compte Railway : https://railway.app
- CLI Railway : `npm install -g @railway/cli && railway login`
- Repo GitHub connecté à Railway

---

## 2. Créer le projet Railway

```bash
railway init          # crée un nouveau projet
railway link          # lie au repo GitHub (recommandé pour auto-deploy)
```

## 3. Ajouter PostgreSQL + pgvector

Dans le dashboard Railway :
1. **New Service → Database → PostgreSQL**
2. Récupérer `DATABASE_URL` dans les variables du service PostgreSQL
3. **IMPORTANT** : Railway fournit PostgreSQL standard. Pour pgvector :
   - Soit utiliser l'image `pgvector/pgvector:pg16` via un service custom
   - Soit passer par Supabase (qui inclut pgvector nativement) — recommandé pour le MVP

### Option A — Supabase (recommandé MVP)
1. Créer un projet sur https://supabase.com (plan gratuit ok pour Gate 1)
2. Récupérer la `DATABASE_URL` dans Settings → Database
3. pgvector est pré-installé (`CREATE EXTENSION IF NOT EXISTS vector;` s'exécute proprement)

### Option B — Railway PostgreSQL + custom image
```bash
railway add --plugin postgresql
# Puis dans le service DB, changer l'image pour pgvector/pgvector:pg16
```

## 4. Variables d'environnement

Configurer dans Railway → Service Backend → Variables :

| Variable | Valeur | Description |
|----------|--------|-------------|
| `DATABASE_URL` | (depuis DB service) | Connection string PostgreSQL |
| `SECRET_KEY` | (générer : `openssl rand -hex 32`) | Clé JWT pour les tokens |
| `EBAY_APP_ID` | (eBay developer) | eBay Browse API |
| `AWIN_PUBLISHER_ID` | (Awin) | Affiliation Awin |
| `CJ_WEBSITE_ID` | (CJ) | Affiliation CJ |
| `PORT` | 8000 | (Railway l'injecte automatiquement) |

## 5. Déploiement

```bash
# Via CLI
railway up

# Via GitHub (recommandé) : auto-deploy sur push main
# Configurer dans Railway → Settings → Source → main branch
```

## 6. Vérification

```bash
# Health check
curl https://<votre-app>.railway.app/health
# → {"status": "ok"}

# Docs API
# https://<votre-app>.railway.app/docs
```

## 7. Migrations

`scripts/run_migrations.py` s'exécute automatiquement **avant** `uvicorn` au démarrage (via le CMD du Dockerfile). En cas d'échec migration, le déploiement échoue (visible dans les logs Railway).

Pour appliquer manuellement :
```bash
railway run python scripts/run_migrations.py
```

## 8. Seed initial du catalogue

Après le premier déploiement réussi :
```bash
railway run python scripts/seed_catalogue.py --count 500
```

## 9. Domaine custom (optionnel, post-Gate 1)

Dans Railway → Settings → Networking → Custom Domain : `api.swipewear.fr`
→ Ajouter CNAME chez votre registrar.

---

## Checklist déploiement

- [ ] Service Railway créé et lié au repo GitHub
- [ ] PostgreSQL avec pgvector disponible
- [ ] `DATABASE_URL` configuré dans les variables Railway
- [ ] `SECRET_KEY` généré et configuré
- [ ] Premier déploiement vert (health check `/health` = 200)
- [ ] Migrations appliquées (vérifier les logs au démarrage)
- [ ] `seed_catalogue.py` lancé (500+ produits)
- [ ] Endpoint `/feed` testé avec un token
