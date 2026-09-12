import 'package:flutter/widgets.dart';

class AppLocalizations {
  AppLocalizations(this.locale);

  final Locale locale;

  static AppLocalizations of(BuildContext context) =>
      AppLocalizations(Localizations.localeOf(context));

  bool get isEnglish => locale.languageCode == 'en';

  String t(String french) => isEnglish ? _english[french] ?? french : french;

  String gender(String? value) => switch (value) {
    'women' => t('Femme'),
    'men' => t('Homme'),
    'unisex' => t('Tout me va'),
    _ => t('À renseigner'),
  };

  String savedPieces(int count) =>
      isEnglish
          ? '$count ${count == 1 ? 'saved item' : 'saved items'}'
          : '$count ${count == 1 ? 'pièce sauvegardée' : 'pièces sauvegardées'}';

  String discoveries(int count) =>
      isEnglish
          ? '$count ${count == 1 ? 'find' : 'finds'} to discover'
          : '$count pépites à découvrir';

  String price(double value) =>
      isEnglish
          ? '€${value.toStringAsFixed(0)}'
          : '${value.toStringAsFixed(0)} €';

  String maxPrice(double? value) =>
      value == null ? t('Sans limite') : price(value);

  static final _english = <String, String>{
    'Préparation de ton espace…': 'Preparing your space…',
    'Chargement de tes préférences…': 'Loading your preferences…',
    'Connexion impossible': 'Connection unavailable',
    'Vérifie le serveur puis réessaie.': 'Check the server and try again.',
    'Réessayer': 'Try again',
    'Swipe': 'Swipe',
    'Découvre. Swipe. Porte.': 'Discover. Swipe. Wear.',
    'Personnaliser mon feed': 'Personalize my feed',
    'Ton feed est personnalisé': 'Your feed is personalized',
    'Les tailles, le budget et tes swipes ajustent automatiquement les pièces proposées.':
        'Your sizes, budget and swipes automatically adjust the pieces shown.',
    'Compris': 'Got it',
    'Drop': 'Drop',
    'Alertes': 'Alerts',
    'Dressing': 'Wardrobe',
    'Profil': 'Profile',
    'Mon espace': 'My space',
    'Session anonyme': 'Anonymous session',
    'Chineuse SwipeWear': 'SwipeWear finder',
    'Toujours à la recherche de belles pièces.':
        'Always looking for great pieces.',
    'TON ALGORITHME': 'YOUR ALGORITHM',
    'Voir mon algorithme': 'View my algorithm',
    'Préférences apprises, choix et verrous':
        'Learned preferences, choices and locks',
    'Je cherche des pièces': 'I am looking for',
    'Mes tailles': 'My sizes',
    'À renseigner': 'Not set',
    'Budget maximum': 'Maximum budget',
    'Sans limite': 'No limit',
    'NOTIFICATIONS': 'NOTIFICATIONS',
    'Fréquence des alertes': 'Alert frequency',
    'Instantanée · Gold': 'Instant · Gold',
    'Résumé quotidien': 'Daily digest',
    'Désactivées': 'Disabled',
    'Préférences indisponibles': 'Preferences unavailable',
    'COMPTE': 'ACCOUNT',
    'Créer un compte ou se connecter': 'Create an account or sign in',
    'Recalibrer mon style': 'Recalibrate my style',
    'Supprimer mon compte': 'Delete my account',
    'Supprimer le compte ?': 'Delete your account?',
    'Ton compte, ton profil et tes événements seront supprimés définitivement.':
        'Your account, profile and events will be permanently deleted.',
    'Annuler': 'Cancel',
    'Supprimer': 'Delete',
    'Suppression impossible pour le moment.':
        'Deletion is unavailable right now.',
    'Charger mon profil': 'Load my profile',
    'Préférence de notification enregistrée.': 'Notification preference saved.',
    'Tes tailles': 'Your sizes',
    'Enregistrer': 'Save',
    'Sans budget max': 'No maximum budget',
    'Toutes tailles': 'All sizes',
    'Modifier': 'Edit',
    'Modifier ton alerte': 'Edit your alert',
    'Décris la pièce que tu veux chasser et affine les critères.':
        'Describe the item you are hunting and refine the criteria.',
    'Ajuste les critères de ta chasse.': 'Adjust your hunt criteria.',
    'Recherche': 'Search',
    'Ex. veste en cuir vintage': 'E.g. vintage leather jacket',
    'Tailles recherchées': 'Sizes wanted',
    'Budget maximum (optionnel)': 'Maximum budget (optional)',
    'État minimum': 'Minimum condition',
    'Décris la pièce que tu recherches.':
        'Describe the item you are looking for.',
    'Indique un budget valide.': 'Enter a valid budget.',
    'Créer mon alerte': 'Create my alert',
    'Enregistrer les critères': 'Save criteria',
    'Les sources légales disponibles sont surveillées automatiquement.':
        'Available legal sources are monitored automatically.',
    'Alertes indisponibles': 'Alerts unavailable',
    'Chasse personnalisée': 'Personal hunt',
    'Actives': 'Active',
    'En pause': 'Paused',
    'Toutes': 'All',
    'Découvrir Gold': 'Discover Gold',
    'Nouvelle alerte': 'New alert',
    'Les alertes actives surveillent les nouvelles pièces correspondant à tes tailles et ton budget.':
        'Active alerts monitor new pieces matching your sizes and budget.',
    'Alerte créée. On chine pour toi.': 'Alert created. We will hunt for you.',
    'Alerte mise à jour.': 'Alert updated.',
    'Aucune alerte active': 'No active alerts',
    'Crée une alerte pour que SwipeWear chine même quand tu n’es pas dans l’app.':
        'Create an alert so SwipeWear can hunt even when you are away.',
    'Le Drop arrive bientôt': 'The Drop is coming soon',
    'Actualise quand les nouvelles pépites sont disponibles.':
        'Refresh when new finds are available.',
    'Chaque jour à 19 h': 'Every day at 7 PM',
    'Le Drop du jour': 'Today’s Drop',
    'Nouvelles pépites demain à 19 h': 'New finds tomorrow at 7 PM',
    'Tout': 'All',
    'Vestes': 'Jackets',
    'Sneakers': 'Sneakers',
    'Sacs': 'Bags',
    'Pantalons': 'Trousers',
    'Voir toutes les pépites': 'See all finds',
    'Actualiser': 'Refresh',
    'Rien dans cette catégorie': 'Nothing in this category',
    'Drop terminé pour aujourd’hui': 'Today’s Drop is complete',
    'Change de catégorie pour retrouver les autres trouvailles du jour.':
        'Change category to see today’s other finds.',
    'Reviens demain à 19 h ou crée une alerte pour une chasse continue.':
        'Come back tomorrow at 7 PM or create an alert for continuous hunting.',
    'Dressing indisponible': 'Wardrobe unavailable',
    'Ta sélection': 'Your selection',
    'Mon dressing': 'My wardrobe',
    'Trier': 'Sort',
    'Récent': 'Recent',
    'Prix croissant': 'Price: low to high',
    'Prix décroissant': 'Price: high to low',
    'Tes trouvailles, au même endroit.': 'Your finds, all in one place.',
    'Dressing vide': 'Empty wardrobe',
    'Aime une pièce dans le feed pour la retrouver ici.':
        'Like an item in the feed to find it here.',
    'Bon retour': 'Welcome back',
    'Créer mon compte': 'Create my account',
    'Retrouve ton style et tes alertes sur tous tes appareils.':
        'Keep your style and alerts across all your devices.',
    'Connecte-toi pour garder ton dressing et ton profil.':
        'Sign in to keep your wardrobe and profile.',
    'Email': 'Email',
    'Mot de passe': 'Password',
    '8 caractères minimum': 'At least 8 characters',
    'Indique un email valide et un mot de passe de 8 caractères minimum.':
        'Enter a valid email and a password with at least 8 characters.',
    'Connexion impossible. Vérifie ton réseau.':
        'Connection unavailable. Check your network.',
    'Connexion Google impossible. Vérifie la configuration de l’application.':
        'Google sign-in unavailable. Check the app configuration.',
    'ou': 'or',
    'Continuer avec Google': 'Continue with Google',
    'J’ai déjà un compte': 'I already have an account',
    'Créer un compte': 'Create an account',
    'Ton style.\nTa prochaine pépite.': 'Your style.\nYour next find.',
    'Ton style, à ta façon.': 'Your style, your way.',
    'SwipeWear apprend ce que tu aimes pour chiner plus vite, au meilleur prix.':
        'SwipeWear learns what you love to hunt faster, at the best price.',
    'Quels styles te font vibrer ?': 'Which styles inspire you?',
    'Choisis les univers qui te ressemblent ou importe quelques inspirations. L’IA affinera ensuite tes recommandations.':
        'Choose the worlds that feel like you or import inspiration. AI will refine your recommendations.',
    'Importer mes inspirations': 'Import my inspiration',
    'Les bons filtres, dès le départ': 'The right filters from the start',
    'Ta taille est un filtre dur : tu ne perdras pas de temps sur des pièces impossibles à porter.':
        'Your size is a hard filter: you will not waste time on pieces you cannot wear.',
    'Hauts': 'Tops',
    'Bas': 'Bottoms',
    'Pointures': 'Shoe sizes',
    'Découvrir mon feed': 'Discover my feed',
    'Continuer': 'Continue',
    'Passer': 'Skip',
    'Voir l’échelle de prix': 'View price ladder',
    'Partager': 'Share',
    'Préparation…': 'Preparing…',
    'Alerte créée pour la prochaine disponibilité.':
        'Alert created for the next availability.',
    'Impossible de créer l’alerte pour le moment.':
        'Could not create the alert right now.',
    'Impossible de préparer le partage.': 'Could not prepare sharing.',
    'SwipeWear Gold actif': 'SwipeWear Gold active',
    'Passe en Gold': 'Go Gold',
    'Tes alertes sont prioritaires.': 'Your alerts have priority.',
    'Alertes illimitées et instantanées.': 'Unlimited, instant alerts.',
    'Langue': 'Language',
    'Français': 'French',
    'Anglais': 'English',
    'Choisir la langue': 'Choose language',
    'Langue mise à jour.': 'Language updated.',
    'Mode hors connexion : dernières données disponibles.':
        'Offline mode: showing the latest available data.',
    'Se connecter': 'Sign in',
    'swipes': 'swipes',
    'marques aimées': 'liked brands',
    'tailles': 'sizes',
    'Choisis au moins un univers ou ajoute une inspiration.':
        'Choose at least one style world or add inspiration.',
    'Remplacer tes inspirations ?': 'Replace your inspiration?',
    'Le parcours par styles remplacera les inspirations importées pour garder un profil clair.':
        'Choosing styles will replace imported inspiration to keep your profile clear.',
    'Remplacer tes styles ?': 'Replace your styles?',
    'Le parcours par inspirations remplacera les styles sélectionnés pour laisser l’IA analyser tes images.':
        'Imported inspiration will replace selected styles so AI can analyze your images.',
    'Sélectionne au moins une taille pour recevoir des pièces pertinentes.':
        'Select at least one size to receive relevant pieces.',
    'Impossible de sauvegarder tes préférences. Réessaie.':
        'Could not save your preferences. Try again.',
    'Pourquoi tu passes ?': 'Why are you passing?',
    'Ton retour aide SwipeWear à mieux comprendre ton style.':
        'Your feedback helps SwipeWear understand your style.',
    'Pas mon style': 'Not my style',
    'Je préfère voir autre chose.': 'I would rather see something else.',
    'Trop cher': 'Too expensive',
    'Garde mon style, baisse le budget.': 'Keep my style, lower the budget.',
    'Alerte créée. On chine cette pièce pour toi.':
        'Alert created. We will hunt this style for you.',
    'Alerte sur ce style': 'Alert this style',
    'Créer une alerte': 'Create an alert',
    'Impossible d’ouvrir l’annonce.': 'Could not open the listing.',
    'On surveille les nouvelles pièces proches de cette trouvaille.':
        'We monitor new pieces close to this find.',
    'Nom de la chasse': 'Hunt name',
    'Tous les états': 'Any condition',
    'Bon état minimum': 'Good condition minimum',
    'Très bon état minimum': 'Very good condition minimum',
    'Neuf uniquement': 'New only',
    'Donne un nom à ta chasse.': 'Name your hunt.',
    'Activer cette alerte': 'Activate this alert',
    'Le budget proposé correspond à environ 80 % de la médiane des offres comparables.':
        'The suggested budget is about 80% of the median comparable offer.',
    'Mes alertes': 'My alerts',
    'Le feed est temporairement indisponible.':
        'The feed is temporarily unavailable.',
    'Impossible de charger tes pièces.': 'Could not load your items.',
    'ALERTE': 'ALERT',
    'J’AIME': 'LIKE',
    'NON': 'NO',
    'Ajouter au dressing': 'Add to wardrobe',
    'Sélection': 'Selection',
    'Tout vu !': 'All caught up!',
    'Plus de pièces à swiper pour le moment.':
        'No more pieces to swipe for now.',
    'Charger plus': 'Load more',
    'Bienvenue dans SwipeWear Gold.': 'Welcome to SwipeWear Gold.',
    'Achat annulé.': 'Purchase cancelled.',
    'Achat impossible :': 'Purchase unavailable:',
    'Restauration impossible :': 'Restore unavailable:',
    'SwipeWear Gold': 'SwipeWear Gold',
    'Chine avant tout le monde.': 'Hunt before everyone else.',
    '4,99 € / mois': '€4.99 / month',
    'ou 39,99 € / an': 'or €39.99 / year',
    'Alertes instantanées': 'Instant alerts',
    'Sois averti dès qu’une pépite correspond à ton style.':
        'Get notified as soon as a find matches your style.',
    'Alertes illimitées': 'Unlimited alerts',
    'Chasse plusieurs styles, tailles et budgets en parallèle.':
        'Hunt multiple styles, sizes and budgets in parallel.',
    'Drop sans friction': 'Frictionless Drop',
    'Ne rate plus les pièces rares avant qu’elles ne partent.':
        'Do not miss rare pieces before they are gone.',
    'Essai 7 jours · 4,99 € / mois': '7-day trial · €4.99 / month',
    'Essai 7 jours · 39,99 € / an': '7-day trial · €39.99 / year',
    'Restaurer mon abonnement': 'Restore my subscription',
    'Abonnement sécurisé via l’App Store ou Google Play.':
        'Secure subscription through the App Store or Google Play.',
    'Tu as atteint la limite gratuite. Gold garde toutes tes chasses actives.':
        'You reached the free limit. Gold keeps all your hunts active.',
    'Le Drop est épuisé. Gold ajoute la priorité et les alertes illimitées.':
        'The Drop is empty. Gold adds priority and unlimited alerts.',
    'Les membres Gold reçoivent les trouvailles avant le délai gratuit de 30 minutes.':
        'Gold members receive finds before the free 30-minute delay.',
    'Ton abonnement Gold est actif.': 'Your Gold subscription is active.',
    'Le statut Gold sera disponible dès que le serveur est connecté.':
        'Gold status will be available once the server is connected.',
    'À l’instant': 'Just now',
    'Sélection SwipeWear': 'SwipeWear selection',
    'Vendu — crée une alerte pour être prévenu·e de la prochaine pièce.':
        'Sold — create an alert to be notified about the next piece.',
    'Pourquoi cette pièce ?': 'Why this piece?',
    'Chaque swipe apprend tes préférences et rend ton prochain feed plus précis.':
        'Every swipe learns your preferences and makes your next feed more precise.',
    'Créer une alerte sur cette pièce': 'Create an alert for this item',
    'Créer une alerte pour la prochaine': 'Create an alert for the next one',
    'Voir l’annonce originale': 'View original listing',
    'Lien partenaire': 'Partner link',
    'Impossible d’ajouter cette préférence.': 'Could not add this preference.',
    'Impossible de retirer cette préférence.':
        'Could not remove this preference.',
    'Impossible de modifier cette préférence.':
        'Could not update this preference.',
    'Mon algorithme': 'My algorithm',
    'Ajouter une préférence': 'Add a preference',
    'Charger mon algorithme': 'Load my algorithm',
    'Ton algorithme apprend avec tes swipes. Ajoute, retire ou verrouille une préférence pour garder le contrôle.':
        'Your algorithm learns from your swipes. Add, remove or lock a preference to stay in control.',
    'Ton algorithme se construit': 'Your algorithm is taking shape',
    'Commence à swiper ou ajoute une préférence manuellement.':
        'Start swiping or add a preference manually.',
    'Préférences apprises': 'Learned preferences',
    'Mes choix': 'My choices',
    'Verrouillée dans ton feed': 'Locked in your feed',
    'Apprise avec tes swipes': 'Learned from your swipes',
    'Ajoutée par toi': 'Added by you',
    'Déverrouiller': 'Unlock',
    'Verrouiller': 'Lock',
    'Retirer': 'Remove',
    'Marque aimée': 'Liked brand',
    'Marque à éviter': 'Brand to avoid',
    'Couleur': 'Color',
    'Catégorie': 'Category',
    'Style': 'Style',
    'Taille': 'Size',
    'Budget max': 'Max budget',
    'Type': 'Type',
    'Style préféré': 'Preferred style',
    'Couleur préférée': 'Preferred color',
    'Catégorie préférée': 'Preferred category',
    'Valeur': 'Value',
    'Ex. vintage, noir, Levi’s…': 'E.g. vintage, black, Levi’s…',
    'Ajouter': 'Add',
    'Échelle de prix': 'Price ladder',
    'Comparaison indisponible': 'Comparison unavailable',
    'Filtrer les offres': 'Filter offers',
    'Sources': 'Sources',
    'Fourchette de prix': 'Price range',
    '👀 Dans le même style, du moins cher au plus cher':
        '👀 Same style, from cheapest to most expensive',
    'Aucune offre comparable trouvée': 'No comparable offer found',
    'Créer une alerte sur ce style': 'Create an alert for this style',
    'Aucune offre ne correspond à ces filtres':
        'No offer matches these filters',
    'Réinitialiser les filtres': 'Reset filters',
    'Être alerté sur cette pièce': 'Alert me about this piece',
    'Lien partenaire · Les prix et disponibilités sont fournis par les plateformes partenaires.':
        'Partner link · Prices and availability are provided by partner platforms.',
    'Partager ma trouvaille': 'Share my find',
    'TROUVAILLE': 'FIND',
    'Aucune offre comparable pour le moment.': 'No comparable offer yet.',
    'swipewear.fr · lien partenaire': 'swipewear.fr · partner link',
    'NEUF': 'NEW',
    'OCCASION': 'SECOND-HAND',
    'MÊME PIÈCE': 'SAME ITEM',
    'SIMILAIRE': 'SIMILAR',
    'VENDU': 'SOLD',
  };
}

class AppLocaleController extends ChangeNotifier {
  AppLocaleController(this._read, this._write) {
    _load();
  }

  final Future<String?> Function() _read;
  final Future<void> Function(String) _write;
  Locale _locale = const Locale('fr');

  Locale get locale => _locale;

  Future<void> _load() async {
    final value = await _read();
    if (value == 'en' || value == 'fr') {
      _locale = Locale(value!);
      notifyListeners();
    }
  }

  Future<void> setLocale(String languageCode) async {
    if (languageCode != 'fr' && languageCode != 'en') return;
    _locale = Locale(languageCode);
    notifyListeners();
    await _write(languageCode);
  }
}
