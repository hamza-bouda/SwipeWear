# Vinted Watcher — Legal Review Checklist

**Required before any production activation of `_fetch_listings` in `vinted_watcher.py`.**

## Status: PENDING — do not activate in production

---

## Checklist

- [ ] **CGU Vinted review**: Vinted's Terms of Service explicitly forbid automated access (scraping). Confirm current CGU status and whether a data partnership agreement is feasible.
- [ ] **GDPR / CNIL**: All data collected must be limited to public listing fields (title, price, images, link). No seller profile IDs, ratings, or location beyond country. Document the legal basis for processing.
- [ ] **robots.txt compliance**: Confirm that the endpoints used by the watcher are not disallowed in Vinted's robots.txt.
- [ ] **Rate-limiting commitment**: Document the agreed crawl rate (default: 20 listings / 5 min / keyword) and confirm it is respectful of Vinted's infrastructure.
- [ ] **IP ban risk assessment**: Confirm that Vinted's anti-bot measures have been evaluated and that the watcher uses a fixed, identifiable User-Agent (see `config.py`).
- [ ] **Legal counsel sign-off**: Written confirmation from a lawyer (or Vinted partnership team) that automated access is permitted under the agreed conditions.
- [ ] **Kill-switch test in staging**: Confirm that disabling the source via `POST /admin/watcher/vinted/disable` removes all Vinted products from the feed within 5 minutes.

---

## Data Minimisation Log

Fields collected per listing:

| Field | Source | Personal data? |
|---|---|---|
| listing_id | Vinted API | No (listing identifier) |
| title | Vinted API | No |
| price_eur | Vinted API | No |
| condition | Vinted API | No |
| size_label | Vinted API | No |
| brand | Vinted API | No |
| category | Vinted API | No |
| image_urls | Vinted API | No (product photos) |
| listing_url | Vinted API | No (public URL) |

Fields explicitly NOT collected: seller user ID, seller username, seller rating,
seller location (city/address), seller phone, sold count, buyer messages.
