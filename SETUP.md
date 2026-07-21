# Setup — Programmes d'affiliation

Ce guide explique comment obtenir les identifiants d'affiliation et les configurer dans le `.env`.

---

## 1. eBay Partner Network (EPN)

EPN couvre les produits d'occasion sur eBay. Commission : 1 a 4 %.

### Etapes

1. Aller sur https://partnernetwork.ebay.com
2. Creer un compte avec l'email du projet
3. Ajouter un site/app ("New Media") avec les infos de SwipeWear
4. Attendre l'approbation (generalement 1 a 5 jours)
5. Une fois approuve, recuperer :
   - **Program ID** : visible dans le dashboard, section "Account" (nombre a 4-5 chiffres)
   - **Campaign ID** : creer une campagne dans "Campaigns" > "Create Campaign" (nombre a 10 chiffres)

### Configuration .env

```
EPN_PROGRAM_ID=5338
EPN_CAMPAIGN_ID=1234567890
```

### Test de tracking

1. Generer une URL affiliee avec `build_affiliate_url()` (module `ingestion.affiliate`)
2. Cliquer sur le lien
3. Verifier dans le dashboard EPN > "Reports" > "Clicks" que le clic apparait (delai : jusqu'a 24 h)

### Format de l'URL

```
https://rover.ebay.com/rover/1/{PROGRAM_ID}/1?campid={CAMPAIGN_ID}&toolid=10001&customid=sw-{context}-{product_id}&mpre={destination_url}
```

---

## 2. Awin

Awin couvre les produits neufs via des marchands partenaires. Commission : 5 a 10 %.

### Etapes

1. Aller sur https://www.awin.com/fr/affilies
2. Creer un compte editeur (publisher)
3. Ajouter le site/app SwipeWear
4. Attendre l'approbation (2 a 4 semaines)
5. Une fois approuve, recuperer :
   - **API Token** : "Account" > "API Credentials"
   - **Publisher ID** : visible dans l'URL du dashboard (`/publisher/{ID}/...`)

### Configuration .env

```
AWIN_API_TOKEN=abc123def456
AWIN_PUBLISHER_ID=999888
```

### Format de l'URL

```
https://www.awin1.com/cread.php?awinmid=&awinaffid={PUBLISHER_ID}&clickref=sw-{context}-{product_id}&ued={destination_url}
```

---

## 3. CJ Affiliate (alternative)

CJ est une alternative a Awin si l'approbation Awin est refusee.

### Etapes

1. Aller sur https://www.cj.com
2. Creer un compte publisher
3. Ajouter le site SwipeWear
4. Attendre l'approbation
5. Recuperer le **Publisher ID** dans "Account" > "Network Profile"

### Configuration .env

```
CJ_PUBLISHER_ID=7654321
```

### Format de l'URL

```
https://www.anrdoezrs.net/links/{PUBLISHER_ID}/type/dlg/sid/sw-{context}-{product_id}/{encoded_destination_url}
```

---

## 4. Plan B — Amazon Associates

Si Awin ET CJ sont refuses, Amazon Associates peut couvrir les produits neufs :

1. Aller sur https://affiliate-program.amazon.fr
2. Creer un compte
3. Ajouter un nouveau tag d'affiliation
4. L'approbation est quasi-immediate mais conditionnee a 3 ventes dans les 180 jours

---

## 5. Variables .env completes (affiliation)

```env
# eBay Partner Network
EPN_PROGRAM_ID=your-epn-program-id
EPN_CAMPAIGN_ID=your-epn-campaign-id

# Awin
AWIN_API_TOKEN=your-awin-api-token
AWIN_PUBLISHER_ID=your-awin-publisher-id

# CJ (si Awin refuse)
CJ_PUBLISHER_ID=your-cj-publisher-id
```

Toutes les variables sont lues par `ingestion/affiliate.py` via `os.environ`. Si une variable est absente, le module retourne l'URL brute sans tracking (pas de crash, mais pas de commission).

---

## 6. Contextes de tracking (custom_id)

Le `custom_id` encode la source du clic pour mesurer quel ecran convertit :

| Contexte | Prefixe | Exemple |
|----------|---------|---------|
| Feed (swipe right) | `sw-feed-` | `sw-feed-prod-42` |
| Echelle de prix | `sw-ladder-` | `sw-ladder-prod-42` |
| Fiche produit | `sw-detail-` | `sw-detail-prod-42` |

Visible dans les rapports EPN / Awin sous "Custom ID" ou "Sub ID".
