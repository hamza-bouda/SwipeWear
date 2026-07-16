# 📋 Cahier des Charges — SwipeWear 2.0

**Nom du Projet :** SwipeWear — *"L'IA qui chine pour toi 24h/24"*
**Version :** 2.0 (pivot stratégique majeur — remplace la v1.0)
**Date :** 15 Juillet 2026
**Équipe :** 2 étudiants ingénieurs (1 profil Développement Full-Stack, 1 profil Ingénierie IA)
**Statut :** Spécifications validées en interne — en attente de validation marché (Gate 1)

---

## 0. Note de version — Ce qui change par rapport à la v1.0

La v1.0 ("le Tinder de la fripe") présentait trois défauts structurels identifiés lors de l'analyse critique :

| Défaut v1.0 | Correction v2.0 |
| :--- | :--- |
| Catalogue basé sur le scraping massif de Vinted/Depop (illégal, instable, non monétisable) | Sources légales avec API et affiliation officielles (eBay, Etsy, Vestiaire Collective, flux produits neufs Awin/CJ) + surveillance Vinted **initiée par l'utilisateur** uniquement |
| Positionnement "divertissement" (le swipe pour s'amuser) → churn structurel | Positionnement "outil de chasse" : le swipe entraîne l'IA, les **alertes** et l'**échelle de prix** créent la valeur récurrente |
| Monétisation improbable (2,99€/mois pour des tenues générées par un algorithme conceptuellement erroné) | Double moteur : **affiliation** (1-10% par vente, neuf et occasion) + **Premium 4,99€/mois** vendant la *priorité* (alertes instantanées) |
| Générateur de tenues par similarité vectorielle (erreur conceptuelle : similarité ≠ compatibilité) | Retiré du MVP. Reporté en V2 avec une approche de compatibilité (règles catégorielles + dataset Polyvore) |
| Solopreneur, 60h estimées (sous-estimation ×3-5) | Équipe de 2, budget temps réaliste de 200-250h sur 4-5 mois, avec gates de validation |

---

## 1. Présentation Générale du Projet

### 1.1 Contexte
Le marché de la mode de seconde main dépasse 7 milliards d'euros en France et croît de 15-18% par an en Europe — quatre fois plus vite que le neuf. Vinted compte 23 millions d'utilisateurs en France. Ce marché possède une propriété économique unique que personne n'exploite côté acheteur grand public :

> **Chaque article d'occasion est une pièce unique qui disparaît en quelques heures.** La rareté n'y est pas marketing, elle est réelle.

Il en découle deux douleurs authentiques et chiffrables :

1. **La douleur du raté ("j'arrive trop tard") :** la pièce parfaite, à sa taille, à bon prix, apparaît à 14h32 et est vendue à 15h10. Les revendeurs professionnels paient déjà 10-30€/mois pour des outils d'alerte Vinted afin de "sniper" les bonnes affaires — la disposition à payer pour la *vitesse* est prouvée, mais aucune offre grand public, mobile et esthétique n'existe.
2. **La douleur du surpaiement ("est-ce que ça existe moins cher ?") :** face à un article neuf à 89€ ou une annonce d'occasion à 45€, l'acheteur n'a aucun moyen simple de savoir si la même pièce (ou une équivalente) existe ailleurs pour moins cher. La comparaison croisée neuf/occasion n'existe qu'en extension navigateur desktop (Faircado, Beni), pas là où la Gen Z achète : le mobile.

### 1.2 Problématique
> Comment garantir à un acheteur de mode qu'il ne ratera plus jamais la pièce unique qui correspond à son style, et qu'il ne la paiera jamais plus cher que nécessaire — sur l'ensemble du marché, neuf et occasion confondus ?

### 1.3 Vision du Projet
**SwipeWear** est un **sniper de pépites personnel** : une application mobile B2C où l'utilisateur entraîne une IA visuelle à comprendre son style en swipant des vêtements, puis délègue la chasse à l'application, qui :

1. **Apprend le style** de l'utilisateur par ses swipes (embeddings visuels CLIP, sans saisie de texte).
2. Présente pour chaque coup de cœur une **échelle de prix** : toutes les façons d'obtenir cette pièce (ou ses équivalentes), triées **du moins cher au plus cher, occasion et neuf confondus**, avec le pourcentage d'économie affiché.
3. **Chine 24h/24** en arrière-plan et notifie l'utilisateur dès qu'une pièce correspondant à son style, sa taille et son budget apparaît — avant les autres.
4. Rythme l'usage par un **Drop quotidien** : chaque jour à 19h, une sélection limitée de 15 pépites personnalisées.

Le swipe reste l'interface d'entraînement (et le format viral TikTok) ; les alertes et l'échelle de prix sont le moteur de rétention et de revenu.

---

## 2. Périmètre du Projet

### 2.1 Dans le périmètre — MVP (V1)
* **Application mobile** React Native / Expo (iOS + Android).
* **Swipe Deck d'entraînement :** deck de cartes (Droite = J'aime, Gauche = Je rejette, Haut = Créer une alerte sur cette pièce).
* **Moteur de style vectoriel :** embeddings CLIP + recherche de similarité pgvector, profil de goût mis à jour à chaque swipe.
* **Échelle de Prix (niveau "même style") :** pour chaque article aimé, liste d'articles visuellement similaires triés par prix croissant, toutes sources confondues (occasion + neuf), avec badges de provenance et calcul d'économie vs le neuf.
* **Moteur d'alertes :** l'utilisateur définit des alertes (style + taille + budget max) ; un worker survole les sources et envoie une notification push à l'apparition d'une correspondance. Gratuit : 1 alerte, délai 30 min. Premium : illimité, instantané.
* **Drop quotidien :** sélection algorithmique de 15 articles/jour, notifiée à 19h.
* **Catalogue multi-sources légal :** eBay (Browse API + affiliation), Etsy (API + affiliation), Vestiaire Collective (flux Awin), flux produits neufs (Zalando, ASOS via Awin/CJ). Objectif initial : 30 000 articles indexés.
* **Surveillance Vinted user-initiated :** l'utilisateur colle l'URL d'une recherche ou d'un article Vinted ; l'app la surveille pour lui (fréquence limitée, par utilisateur).
* **Redirection d'achat** avec liens affiliés lorsque le programme existe.

### 2.2 Dans le périmètre — V1.5 (post-validation)
* **Échelle de prix niveau "la même pièce" :** matching exact sur un catalogue de référence de 100-200 produits iconiques (Air Force 1, Levi's 501, Carhartt Detroit Jacket, Stan Smith…), construit et vérifié manuellement, étendu progressivement. Détection par marque + modèle (logo, OCR d'étiquette, parsing de titres) + vérification visuelle.
* **Alerte de baisse de prix** sur un article précis ("préviens-moi si elle passe sous 30€").

### 2.3 Hors périmètre (V1 et V1.5)
* Générateur de tenues (reporté V2, avec algorithme de *compatibilité* et non de similarité).
* Numérisation de la garde-robe personnelle (V2).
* Transactions, paiements, messagerie, comptes vendeurs : **jamais** — SwipeWear est un moteur de découverte et de comparaison, pas une marketplace.
* Scraping massif du catalogue Vinted : **exclu par principe d'architecture** (voir §5.2).

---

## 3. Public Cible & Personas

### 3.1 Cœur de cible
* **Gen Z (16-25 ans) :** natifs Vinted, sensibles au prix, à la recherche de pièces de marque uniques ; culture du "fit check" et de la bonne affaire revendiquée.
* **Millennials (25-35 ans) :** acheteurs raisonnés, éco-sensibles, prêts à payer pour gagner du temps et de l'argent.

### 3.2 Personas

#### Persona 1 : Chloé, 20 ans — La chineuse frustrée
* Étudiante à Lyon, budget serré, 2h/jour sur TikTok, chine sur Vinted plusieurs fois par semaine.
* **Douleur principale :** a raté trois fois "la" veste vintage à sa taille — vendue avant qu'elle ne la voie. Finit par acheter Shein par dépit.
* **Usage SwipeWear :** swipe 5 min le soir, reçoit le Drop à 19h, a une alerte "veste en cuir noir vintage, taille S, < 35€". Convertit en Premium après avoir raté une pépite notifiée avec 30 min de retard.

#### Persona 2 : Thomas, 28 ans — L'acheteur rationnel
* Développeur à Berlin, achète des marques durables (Patagonia, Carhartt), déteste chercher.
* **Douleur principale :** ne sait jamais s'il paie le bon prix. Compare manuellement 4 sites pendant 40 minutes avant chaque achat.
* **Usage SwipeWear :** photographie ou like une pièce, consulte l'échelle de prix, achète au meilleur rapport état/prix. Utilise l'alerte de baisse de prix.

#### Persona 3 : Léa, 23 ans — La revendeuse amateur (segment secondaire)
* Achète pour revendre à petite échelle. Utilise déjà un outil d'alerte payant rudimentaire.
* **Usage SwipeWear :** version grand public plus agréable de son outil de snipe ; convertit en Premium immédiatement pour l'instantanéité.

---

## 4. Exigences Fonctionnelles (MVP)

### 4.1 Onboarding & Profiling
* **F01 — Inscription :** Email / Apple ID / Google. Durée cible < 60 secondes.
* **F02 — Calibrage de style (Cold Start) :** sélection genre + tailles + swipe de calibration sur 30 images archétypales (streetwear, minimaliste, Y2K, workwear, grunge…) pour initialiser le vecteur de goût avant le premier feed réel.

### 4.2 Swipe Deck (entraînement)
* **F03 — Carte article :** photo plein écran, prix, taille, marque, badge source (eBay/Etsy/VC/neuf), badge état.
* **F04 — Gestes :** Droite = Like (dressing + met à jour le vecteur), Gauche = Rejet, Haut = **Créer une alerte** sur ce type de pièce.
* **F05 — Pre-fetching :** 10 cartes préchargées, latence perçue nulle.

### 4.3 Échelle de Prix
* **F06 — Vue "échelle" :** au tap sur un article aimé, liste triée par prix croissant : section *"Dans le même style"* (similarité CLIP, toutes sources), chaque ligne = photo, prix, source, état, taille. Bandeau d'économie : *"Jusqu'à −72% vs le neuf"*.
* **F07 — Liens sortants affiliés :** ouverture de la fiche d'origine (app ou navigateur), lien affilié injecté quand le programme existe, mention transparente "lien partenaire".
* **F08 — Carte de partage :** génération d'une image partageable (la pièce + l'échelle de prix + le % d'économie) pour stories/TikTok.

### 4.4 Alertes (moteur de rétention et de revenu)
* **F09 — Création d'alerte :** style (à partir d'un article ou du profil), taille(s), budget max, sources.
* **F10 — Worker de surveillance :** scan périodique des sources API ; matching vectoriel + filtres ; file de notifications.
* **F11 — Notification push :** *"🎯 Ta pépite est apparue : Carhartt Detroit, M, 24€ (−80% vs neuf) — 3 personnes la regardent"*. Gratuit = délai 30 min ; Premium = instantané.
* **F12 — Surveillance Vinted user-initiated :** champ "colle un lien Vinted" ; vérification à fréquence plafonnée par utilisateur ; aucune donnée Vinted stockée au-delà des métadonnées de l'alerte de l'utilisateur.

### 4.5 Drop Quotidien
* **F13 — Sélection quotidienne :** 15 articles maximisant (proximité de style × fraîcheur × rapport qualité/prix), notifiés à 19h. Épuisable — pas de feed infini.

---

## 5. Contraintes Techniques & Réglementaires

### 5.1 Contraintes Techniques
* **Latence :** échelle de prix < 400 ms (recherche pgvector HNSW pré-indexée) ; carte de swipe < 200 ms.
* **Fraîcheur :** re-scan des sources API toutes les 15-60 min selon quota ; purge des annonces mortes par vérification différée + signalement communautaire.
* **Coût d'inférence :** CLIP `ViT-B-32` sur CPU (≈100 ms/image à l'ingestion) ; aucun GPU requis au MVP.
* **Push :** Expo Notifications ; file de priorité stricte Premium > Gratuit.

### 5.2 Principe d'architecture non négociable : survivre sans Vinted
Aucun composant critique (catalogue, échelle de prix, drop, revenus) ne dépend de Vinted. Vinted n'apparaît que dans la surveillance user-initiated (F12), conçue pour être coupée sans casser le produit. **Tout développement qui violerait ce principe est refusé en revue de code.**

### 5.3 Contraintes Réglementaires
* **RGPD :** données stockées limitées à l'email (haché), tailles, et vecteur de style (512 flottants, anonyme par nature). Suppression de compte et d'historique en un tap. Pas de tracker publicitaire tiers au MVP.
* **Transparence affiliation :** mention "lien partenaire" conforme aux obligations d'information (pratiques commerciales trompeuses, DGCCRF).
* **CGU des sources :** usage exclusif des API et flux officiels dans les limites de leurs conditions ; quotas respectés programmatiquement.

---

## 6. Critères de Succès du MVP (réalistes)

| Métrique | Seuil de succès | Seuil d'alerte | Mesure |
| :--- | :--- | :--- | :--- |
| **Gate 1 — Demande** (avant code) | 300 inscrits liste d'attente OU 1 vidéo > 50K vues | < 100 inscrits après 8 vidéos | Landing + TikTok |
| **Gate 2 — Rétention beta** | ≥ 30% des beta-testeurs créent ≥ 2 alertes ET reviennent en semaine 2 | < 15% | Analytics cohortes (100 testeurs) |
| Rétention D30 (post-lancement) | > 12% | < 6% | Cohortes |
| Conversion Premium | 2-4% des MAU | < 1% | Abonnements / MAU |
| CTR sortant (échelle de prix) | > 8% des vues d'échelle | < 3% | Clics affiliés / vues |
| Alerte → ouverture app | > 40% | < 20% | Push analytics |

**Règle de décision :** Gate 1 échouée → itérer le format 2 semaines puis pivoter (l'échec coûte 0€). Gate 2 échouée → la boucle alerte ne prend pas : réduire au comparateur de prix pur ou arrêter. Les gates existent pour économiser des mois, pas pour rassurer.
