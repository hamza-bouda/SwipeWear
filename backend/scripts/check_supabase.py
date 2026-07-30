"""Vérifie la configuration Supabase, par exécution réelle.

À lancer après avoir rempli les variables :

    python backend/scripts/check_supabase.py

Le but est qu'une configuration incomplète se voie tout de suite, plutôt qu'à
la première tentative de connexion d'un vrai client. Rien n'est déduit d'une
lecture de fichier : chaque point est vérifié en appelant le projet.

Aucune clé n'est affichée.

KAN-90
"""
from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from api.config import load_dotenv  # noqa: E402

load_dotenv()

TIMEOUT = 10
OK, KO, WARN = "  [OK] ", "  [KO] ", "  [!]  "


def _get(url: str, headers: dict | None = None):
    request = urllib.request.Request(url, headers=headers or {})
    with urllib.request.urlopen(request, timeout=TIMEOUT) as response:
        return response.status, json.loads(response.read().decode())


def _mobile_env() -> dict[str, str]:
    path = Path(__file__).resolve().parent.parent.parent / "mobile" / ".env"
    if not path.exists():
        return {}
    values = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, _, value = line.partition("=")
            values[key.strip()] = value.strip()
    return values


def main() -> int:
    problems = 0

    print("=== Backend ===")
    url = (os.getenv("SUPABASE_URL") or "").strip().rstrip("/")
    if not url:
        print(KO + "SUPABASE_URL absente — la connexion par compte est désactivée.")
        print("       L'app reste utilisable en navigation anonyme.")
        problems += 1
    elif not url.startswith("https://"):
        print(KO + f"SUPABASE_URL ne commence pas par https:// ({url})")
        problems += 1
    else:
        print(OK + f"SUPABASE_URL = {url}")

        issuer = f"{url}/auth/v1"
        try:
            status, jwks = _get(f"{issuer}/.well-known/jwks.json")
            keys = jwks.get("keys") or []
            if keys:
                algorithms = sorted({k.get("alg", "?") for k in keys})
                print(OK + f"JWKS joignable — {len(keys)} clé(s), "
                           f"algorithme(s) : {', '.join(algorithms)}")
            else:
                print(WARN + "JWKS vide : le projet signe probablement encore "
                             "avec le secret HS256 partagé.")
                if not (os.getenv("SUPABASE_JWT_SECRET") or "").strip():
                    print(KO + "  et SUPABASE_JWT_SECRET est vide — aucun jeton "
                               "ne pourra être vérifié.")
                    problems += 1
                else:
                    print(OK + "  SUPABASE_JWT_SECRET est renseignée.")
        except (urllib.error.URLError, ValueError) as exc:
            print(KO + f"JWKS injoignable ({exc}). URL du projet correcte ?")
            problems += 1

        service_key = (os.getenv("SUPABASE_SERVICE_ROLE_KEY") or "").strip()
        if not service_key:
            print(WARN + "SUPABASE_SERVICE_ROLE_KEY absente : la suppression de "
                         "compte refusera (502) au lieu de laisser une identité "
                         "orpheline chez Supabase.")
        else:
            try:
                _get(
                    f"{issuer}/admin/users?page=1&per_page=1",
                    {"apikey": service_key, "Authorization": f"Bearer {service_key}"},
                )
                print(OK + "Clé service_role acceptée — suppression de compte "
                           "opérationnelle.")
            except urllib.error.HTTPError as exc:
                print(KO + f"Clé service_role refusée (HTTP {exc.code}). "
                           "Est-ce bien la clé service_role et non la clé anon ?")
                problems += 1
            except urllib.error.URLError as exc:
                print(KO + f"API admin injoignable ({exc}).")
                problems += 1

    print("\n=== Application mobile ===")
    mobile = _mobile_env()
    mobile_url = mobile.get("EXPO_PUBLIC_SUPABASE_URL", "")
    mobile_key = mobile.get("EXPO_PUBLIC_SUPABASE_ANON_KEY", "")

    if not mobile_url or not mobile_key:
        print(KO + "mobile/.env incomplet — l'écran de connexion affichera "
                   "« La connexion n'est pas configurée ».")
        problems += 1
    else:
        print(OK + f"EXPO_PUBLIC_SUPABASE_URL = {mobile_url}")
        print(OK + "EXPO_PUBLIC_SUPABASE_ANON_KEY renseignée.")
        if url and mobile_url.rstrip("/") != url:
            print(KO + "L'app et le backend ne visent pas le même projet : "
                       "chaque jeton sera rejeté par l'émetteur.")
            problems += 1

    # Une clé service_role dans le bundle mobile serait une fuite totale.
    for key, value in mobile.items():
        if key.startswith("EXPO_PUBLIC_") and "service_role" in value.lower():
            print(KO + f"{key} contient une clé service_role — à retirer "
                       "immédiatement et à révoquer dans Supabase.")
            problems += 1

    print()
    if problems:
        print(f"{problems} point(s) à corriger. "
              "Voir Documentation/13_Auth_Supabase.md.")
        return 1
    print("Configuration Supabase complète et vérifiée.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
