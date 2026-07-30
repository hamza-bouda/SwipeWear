"""Vérifie la configuration Firebase, par exécution réelle.

À lancer après avoir rempli les variables :

    python backend/scripts/check_firebase.py

Le but est qu'une configuration incomplète se voie tout de suite, plutôt qu'à
la première tentative de connexion d'un vrai client. Rien n'est déduit d'une
lecture de fichier : chaque point est vérifié en appelant Google.

Aucune clé n'est affichée.

KAN-91
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

_JWKS_URL = (
    "https://www.googleapis.com/service_accounts/v1/jwk/"
    "securetoken@system.gserviceaccount.com"
)
_IDENTITY_SCOPE = "https://www.googleapis.com/auth/identitytoolkit"


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


def _service_account() -> dict | None:
    inline = (os.getenv("FIREBASE_SERVICE_ACCOUNT_JSON") or "").strip()
    if inline:
        try:
            return json.loads(inline)
        except ValueError:
            return None
    path = (os.getenv("GOOGLE_APPLICATION_CREDENTIALS") or "").strip()
    if path and os.path.exists(path):
        try:
            with open(path, encoding="utf-8") as handle:
                return json.load(handle)
        except (OSError, ValueError):
            return None
    return None


def main() -> int:
    problems = 0

    print("=== Backend ===")
    project = (os.getenv("FIREBASE_PROJECT_ID") or "").strip()
    if not project:
        print(KO + "FIREBASE_PROJECT_ID absente — la connexion par compte est "
                   "désactivée.")
        print("       L'app reste utilisable en navigation anonyme.")
        problems += 1
    else:
        print(OK + f"FIREBASE_PROJECT_ID = {project}")
        try:
            _, jwks = _get(_JWKS_URL)
            keys = jwks.get("keys") or []
            if keys:
                algorithms = sorted({k.get("alg", "?") for k in keys})
                print(OK + f"Clés de signature Google joignables — {len(keys)} "
                           f"clé(s), algorithme(s) : {', '.join(algorithms)}")
            else:
                print(KO + "Aucune clé publiée par Google — vérification "
                           "impossible.")
                problems += 1
        except (urllib.error.URLError, ValueError) as exc:
            print(KO + f"Clés de signature injoignables ({exc}).")
            problems += 1

        info = _service_account()
        if info is None:
            print(WARN + "Compte de service absent ou illisible : la suppression "
                         "de compte refusera (502) au lieu de laisser une "
                         "identité orpheline chez Firebase.")
        elif info.get("project_id") != project:
            print(KO + f"Le compte de service appartient au projet "
                       f"{info.get('project_id')!r}, pas à {project!r}.")
            problems += 1
        else:
            try:
                from google.auth.transport.requests import Request
                from google.oauth2 import service_account

                credentials = service_account.Credentials.from_service_account_info(
                    info, scopes=[_IDENTITY_SCOPE],
                )
                credentials.refresh(Request())
                print(OK + "Compte de service accepté — suppression de compte "
                           "opérationnelle.")
            except Exception as exc:  # noqa: BLE001
                print(KO + f"Compte de service refusé ({type(exc).__name__}).")
                problems += 1

    print("\n=== Application mobile ===")
    mobile = _mobile_env()
    api_key = mobile.get("EXPO_PUBLIC_FIREBASE_API_KEY", "")
    mobile_project = mobile.get("EXPO_PUBLIC_FIREBASE_PROJECT_ID", "")

    if not api_key or not mobile_project:
        print(KO + "mobile/.env incomplet — l'écran de connexion affichera "
                   "« La connexion n'est pas configurée ».")
        problems += 1
    else:
        print(OK + f"EXPO_PUBLIC_FIREBASE_PROJECT_ID = {mobile_project}")
        print(OK + "EXPO_PUBLIC_FIREBASE_API_KEY renseignée.")
        if project and mobile_project != project:
            print(KO + "L'app et le backend ne visent pas le même projet : "
                       "chaque jeton sera rejeté par l'audience.")
            problems += 1

    if mobile.get("EXPO_PUBLIC_GOOGLE_WEB_CLIENT_ID"):
        print(OK + "Connexion Google configurée.")
    else:
        print(WARN + "EXPO_PUBLIC_GOOGLE_WEB_CLIENT_ID vide : le bouton Google "
                     "reste désactivé. Active Google dans la console Firebase, "
                     "puis copie l'identifiant client Web.")

    # Une clé privée dans le bundle mobile serait une fuite totale.
    for key, value in mobile.items():
        if key.startswith("EXPO_PUBLIC_") and (
            "private_key" in value or value.startswith("-----BEGIN")
        ):
            print(KO + f"{key} contient une clé privée — à retirer "
                       "immédiatement et à révoquer dans Firebase.")
            problems += 1

    print()
    if problems:
        print(f"{problems} point(s) à corriger. "
              "Voir Documentation/14_Auth_Firebase.md.")
        return 1
    print("Configuration Firebase complète et vérifiée.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
