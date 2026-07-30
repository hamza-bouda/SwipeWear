-- Migration 018 — l'identité vient de Firebase (KAN-91)
--
-- Firebase n'émet pas d'UUID : son claim `sub` est une chaîne opaque de 28
-- caractères. Or `user_id` est de type UUID dans dix colonnes de cette base
-- et dans quatre modèles de `contracts/` — une zone protégée qui ne se
-- modifie pas sans l'accord des deux lanes (CLAUDE.md §4 et §8).
--
-- Plutôt que de migrer tout cela, `user_id` est dérivé de l'identifiant
-- Firebase par UUIDv5, avec l'émetteur du projet comme espace de noms. C'est
-- déterministe (la même personne retombe toujours sur la même ligne) et
-- cloisonné par projet (deux projets Firebase ne peuvent pas entrer en
-- collision). Aucune colonne UUID ni aucun contrat n'est touché.
--
-- `provider_uid` conserve l'identifiant d'origine, car la suppression du
-- compte chez Firebase l'exige : l'UUID dérivé ne se calcule que dans un
-- sens.
--
-- `phone_number` devient nécessaire : l'authentification par téléphone crée
-- des comptes sans aucune adresse email. Jusqu'ici, `email` était la seule
-- façon de reconnaître un compte humainement.

ALTER TABLE users
    ADD COLUMN IF NOT EXISTS provider_uid TEXT;

ALTER TABLE users
    ADD COLUMN IF NOT EXISTS phone_number TEXT;

-- Deux comptes locaux ne peuvent pas pointer sur la même identité amont.
-- Index partiel : les lignes créées avant cette migration ont provider_uid
-- NULL et ne doivent pas se gêner entre elles.
CREATE UNIQUE INDEX IF NOT EXISTS users_provider_uid_idx
    ON users (provider_uid)
    WHERE provider_uid IS NOT NULL;

COMMENT ON COLUMN users.provider_uid IS
    'Identifiant brut chez le fournisseur d''identité (Firebase uid). user_id en est la dérivation UUIDv5.';
COMMENT ON COLUMN users.phone_number IS
    'Numéro vérifié, pour les comptes créés par authentification téléphone (sans email).';
