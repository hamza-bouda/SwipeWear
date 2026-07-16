# 📊 Analyse SWOT — SwipeWear 2.0

Analyse stratégique de **SwipeWear 2.0** ("le sniper de pépites") sur le marché français et européen, horizon 2026-2027. Cette version remplace la SWOT v1.0, dont plusieurs faiblesses classées "moyennes" étaient en réalité fatales (dépendance au scraping Vinted, absence de modèle de revenu).

---

## 1. Forces (Strengths)

### 1.1 Une douleur avec urgence réelle et disposition à payer prouvée
* Sur le marché de l'occasion, chaque pièce est unique et disparaît en heures : le **FOMO est authentique**, pas fabriqué. C'est le seul segment de la mode où une notification push est un service rendu, pas du spam.
* La preuve de marché existe déjà : des outils d'alerte Vinted payants (10-30€/mois) sont utilisés par les revendeurs. SwipeWear en est la version grand public, mobile, esthétique et pilotée par IA visuelle — un marché prouvé, une exécution absente.

### 1.2 Double moteur de monétisation aligné avec la valeur
* **Affiliation neuf + occasion :** les flux produits neufs (Zalando, ASOS via Awin/CJ) paient 5-10% par vente ; eBay/Etsy/Vestiaire Collective 1-4%. Chaque échelle de prix consultée est une surface de revenu.
* **Premium 4,99€/mois vendant la priorité :** sur des pièces uniques, être notifié 30 minutes après les autres = perdre la pièce. On ne vend pas du confort (faible valeur perçue) mais un **avantage compétitif entre acheteurs** — le même ressort psychologique qui fait payer dans les sneakers, la billetterie et l'immobilier locatif.

### 1.3 Actif de données propriétaire : le graphe de goût
* Chaque swipe est un jugement esthétique humain horodaté sur un vêtement réel. À l'échelle, cette base (le "taste graph") n'existe nulle part ailleurs — Vinted a des recherches par mots-clés, pas des préférences visuelles. C'est le moat de Pinterest appliqué à la seconde main.
* S'y ajoute le **catalogue de référence des produits iconiques** (V1.5), construit et vérifié manuellement : un actif lent à copier.

### 1.4 Position structurellement incopiables par les plateformes elles-mêmes
* Le cœur de la proposition — **comparer les prix entre plateformes concurrentes, neuf et occasion confondus** — est précisément ce qu'aucune plateforme ne fera jamais : Vinted ne montrera pas eBay, Zalando ne montrera pas Vinted. La neutralité multi-sources est un avantage que les géants ne peuvent pas répliquer sans se cannibaliser.

### 1.5 Modèle asset-light et équipe adaptée
* Pas de stock, pas de logistique, pas de paiement, pas de litiges. Coûts fixes < 50€/mois au MVP.
* Équipe de 2 profils complémentaires (full-stack + IA) : le produit est à l'intersection exacte des compétences disponibles (vision, embeddings, mobile, pipelines de données).

### 1.6 Format nativement viral
* L'échelle de prix produit un contenu partageable à chaque usage : *"Vue chez Zara à 89€, trouvée à 22€ — −75%"*. Le chiffre d'économie est le hook TikTok parfait, et chaque utilisateur en génère.

---

## 2. Faiblesses (Weaknesses)

### 2.1 Qualité de l'inventaire occasion hors Vinted
* Vinted détient l'inventaire d'occasion que la cible française préfère, et n'offre ni API publique ni affiliation. Le catalogue MVP (eBay, Etsy, Vestiaire Collective) est plus fort sur le vintage de marque et le milieu/haut de gamme que sur "la fripe à 5€". **Conséquence assumée :** le positionnement de lancement est "pépites de marque et vintage", pas "tout Vinted en mieux".

### 2.2 Difficulté technique du matching exact
* Distinguer "la même pièce" de "une pièce similaire" est un problème dur : photos amateur, titres sans référence produit, contrefaçons. Une seule erreur affichée comme "identique" détruit la confiance — l'actif unique d'un comparateur.
* Mitigation structurelle : architecture à deux étages ("la même pièce" limité au catalogue de référence vérifié ; "dans le même style" pour tout le reste), étiquetage honnête systématique.

### 2.3 Dépendance aux programmes d'affiliation
* Les commissions, quotas d'API et conditions des programmes (Awin, CJ, eBay Partner Network) peuvent changer unilatéralement. Moins brutal qu'un blocage de scraping, mais réel. Mitigation : diversification des sources dès le MVP (aucune source > 40% du catalogue), et le Premium comme second pilier de revenu indépendant.

### 2.4 Ressources limitées (2 étudiants)
* ~20h/semaine à deux, en parallèle des études. Le périmètre MVP est calibré en conséquence, mais toute dérive de scope (générateur de tenues, garde-robe, marketplace) est fatale au calendrier. La discipline de scope est une compétence critique du projet.

### 2.5 Cold start du profil de style
* L'IA a besoin de ~30-50 swipes pour un profil fiable. Le calibrage visuel d'onboarding (30 images archétypales) réduit le problème sans l'éliminer. Les premiers Drops peuvent décevoir → risque de churn précoce, surveillé via Gate 2.

---

## 3. Opportunités (Opportunities)

### 3.1 Vent réglementaire et générationnel
* Lois anti-fast-fashion françaises (pénalités sur le neuf jetable importé), directives européennes sur la durabilité : le prix relatif de l'occasion s'améliore structurellement chaque année.
* Plus de 80% des 15-25 ans français achètent ou vendent d'occasion : la seconde main est la norme, pas la niche.

### 3.2 Case "comparaison neuf/occasion mobile" encore vide en Europe
* Faircado (Berlin) et Beni (US) ont validé le concept du comparateur occasion — mais en **extension navigateur desktop**. Personne ne l'a exécuté en app mobile avec IA de style et alertes, là où la Gen Z passe 4h/jour. La fenêtre est ouverte ; elle ne le restera pas indéfiniment.

### 3.3 L'inflation comme meilleur commercial
* Chaque point d'inflation renforce le pitch "ne surpaie plus jamais". L'échelle de prix transforme l'app en outil d'économie du quotidien — une catégorie qui prospère précisément quand le pouvoir d'achat baisse.

### 3.4 Extension naturelle du produit (optionnalité)
* Le graphe de goût ouvre des V2 défendables : recommandations de tenues par compatibilité, personal shopping IA, données de tendances agrégées (anonymisées) valorisables en B2B auprès des marques — sans jamais dévier du cœur B2C.

---

## 4. Menaces (Threats)

### 4.1 Réplication par un acteur financé
* La surface du produit (swipe + comparateur + alertes) est copiable en quelques mois par une startup financée ou par Faircado pivotant sur mobile. Défense : vitesse d'exécution, marque TikTok, graphe de goût qui se creuse avec l'usage. Fenêtre critique : les 12 premiers mois.

### 4.2 Fermeture ou dégradation des API sources
* eBay/Etsy peuvent durcir quotas ou conditions. Probabilité modérée (ces API existent pour générer du trafic d'affiliation — l'intérêt est aligné), impact élevé. Mitigation : multi-sources + cache local des métadonnées + le Premium ne dépend d'aucune source unique.

### 4.3 Vinted ferme la surveillance user-initiated
* Vinted peut durcir ses protections au point de rendre la F12 inopérante. **Par conception, le produit y survit** (principe d'architecture §5.2 du cahier des charges) — mais une partie de l'attractivité marketing ("surveille aussi Vinted") serait perdue.

### 4.4 Fatigue du format swipe
* L'historique du swipe-shopping (Mallzee, Grabble : morts) montre que le swipe seul ne retient pas. La v2.0 ne parie plus dessus (rétention = alertes + drop), mais si les utilisateurs ne créent pas d'alertes (Gate 2 < 15%), le produit retombe dans le piège de la v1. C'est LE risque produit central, d'où le gate dédié.

### 4.5 Réglementation IA/profilage
* EU AI Act et RGPD encadrent le profilage comportemental. Le profil vectoriel anonyme et l'absence de données sensibles placent SwipeWear en risque faible, sous réserve d'une gestion propre des consentements de notification.

---

## 5. Matrice de Synthèse

| | Forces | Faiblesses |
| :--- | :--- | :--- |
| **Interne** | - FOMO authentique + disposition à payer prouvée<br>- Double revenu : affiliation (5-10% neuf) + Premium "priorité"<br>- Taste graph + catalogue de référence propriétaires<br>- Neutralité multi-plateformes incopiables par les géants<br>- Asset-light, équipe alignée sur la tech | - Inventaire occasion sans Vinted (positionnement "marques/vintage" imposé)<br>- Matching exact difficile (confiance en jeu)<br>- Dépendance aux programmes d'affiliation<br>- 2 étudiants, ~20h/sem — zéro tolérance à la dérive de scope<br>- Cold start du profil |
| **Externe** | **Opportunités**<br>- Régulations anti-fast-fashion + norme générationnelle<br>- Case mobile neuf/occasion vide en Europe<br>- Inflation = meilleur argument de vente<br>- Optionnalité V2 (tenues, tendances B2B) | **Menaces**<br>- Copie par acteur financé (fenêtre 12 mois)<br>- Durcissement des API/affiliation<br>- Fermeture de la surveillance Vinted (survivable par design)<br>- Fatigue du swipe si la boucle alerte ne prend pas (Gate 2)<br>- Cadre EU AI Act (risque faible) |

---

## 6. Lecture stratégique

La v1.0 avait ses forces à l'intérieur (une belle UX) et sa survie à l'extérieur (les données de Vinted). La v2.0 inverse la structure : **les actifs critiques sont internes** (graphe de goût, catalogue de référence, marque) et **les dépendances externes sont diversifiées et alignées par l'intérêt économique** (les API d'affiliation existent pour recevoir du trafic). C'est cette inversion qui fait passer le projet d'un pari toléré par un tiers à un business défendable.

Le point de fragilité restant n'est plus juridique ni technique : il est **comportemental** — les utilisateurs créeront-ils des alertes et reviendront-ils ? C'est exactement ce que Gate 2 mesure avant tout investissement lourd.
