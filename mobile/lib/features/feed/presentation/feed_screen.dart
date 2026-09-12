import 'dart:async';
import 'dart:math' as math;

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/network/api_client.dart';
import '../../../core/analytics/providers.dart';
import '../../../core/localization/app_localizations.dart';
import '../../../core/widgets/offline_banner.dart';
import '../../../core/theme/app_theme.dart';
import '../../alerts/providers.dart';
import '../../auth/providers.dart';
import '../../billing/presentation/paywall_screen.dart';
import '../../dressing/providers.dart';
import '../../ladder/providers.dart';
import '../../onboarding/data/style_archetypes.dart';
import '../../profile/providers.dart';
import '../data/feed_repository.dart';
import 'product_detail_screen.dart';
import '../data/product.dart';
import '../providers.dart';

class FeedScreen extends ConsumerStatefulWidget {
  const FeedScreen({super.key, this.onOpenAlerts});

  final VoidCallback? onOpenAlerts;

  @override
  ConsumerState<FeedScreen> createState() => _FeedScreenState();
}

class _FeedScreenState extends ConsumerState<FeedScreen> {
  int _index = 0;
  int _lastPrefetchStart = -1;
  Offset _dragOffset = Offset.zero;
  bool _busy = false;

  void _prefetchImages(FeedResponse feed) {
    if (_lastPrefetchStart == _index) return;
    _lastPrefetchStart = _index;
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (!mounted) return;
      final end = math.min(feed.items.length, _index + 10);
      for (var itemIndex = _index; itemIndex < end; itemIndex++) {
        for (final imageUrl in feed.items[itemIndex].product.imageUrls.take(
          3,
        )) {
          // Prefetching is an optimisation only. A missing network/DNS route
          // must never surface as an uncaught Flutter image exception or make
          // an otherwise usable cached feed look broken.
          unawaited(
            precacheImage(
              NetworkImage(imageUrl),
              context,
              onError: (_, __) {},
            ).catchError((_) {}),
          );
        }
      }
    });
  }

  Future<void> _swipe(String eventType) async {
    final feed = ref.read(feedProvider).valueOrNull;
    final session = ref.read(sessionProvider).valueOrNull;
    if (feed == null ||
        session == null ||
        _busy ||
        _index >= feed.items.length) {
      return;
    }

    final product = feed.items[_index].product;
    unawaited(
      ref
          .read(analyticsServiceProvider)
          .track(
            session,
            'swipe',
            properties: {'product_id': product.id, 'direction': eventType},
          ),
    );
    setState(() => _busy = true);
    try {
      await ref
          .read(feedRepositoryProvider)
          .postEvent(session, product.id, eventType);
      if (eventType == 'swipe_right') {
        // A right swipe is both taste evidence and a wardrobe save.
        await ref
            .read(feedRepositoryProvider)
            .postEvent(session, product.id, 'save');
      }
      if (eventType == 'swipe_right' || eventType == 'save') {
        ref.invalidate(savesProvider);
      }
    } catch (_) {
      // Events are best-effort. The feed must remain usable if analytics is
      // temporarily unavailable.
    }
    if (!mounted) return;
    setState(() {
      _index++;
      _dragOffset = Offset.zero;
      _busy = false;
    });
  }

  void _handleDragEnd() {
    final horizontal = _dragOffset.dx.abs();
    final vertical = _dragOffset.dy.abs();
    if (_dragOffset.dy < -90 && vertical > horizontal) {
      final feed = ref.read(feedProvider).valueOrNull;
      if (feed != null && _index < feed.items.length) {
        _createAlert(feed.items[_index].product);
      }
    } else if (horizontal > 110) {
      if (_dragOffset.dx > 0) {
        _swipe('swipe_right');
      } else {
        _chooseRejection();
      }
    } else {
      setState(() => _dragOffset = Offset.zero);
    }
  }

  Future<void> _chooseRejection() async {
    final l = AppLocalizations.of(context);
    final choice = await showModalBottomSheet<String>(
      context: context,
      showDragHandle: true,
      builder:
          (context) => SafeArea(
            child: Padding(
              padding: const EdgeInsets.fromLTRB(24, 4, 24, 24),
              child: Column(
                mainAxisSize: MainAxisSize.min,
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    l.t('Pourquoi tu passes ?'),
                    style: Theme.of(context).textTheme.headlineSmall?.copyWith(
                      fontWeight: FontWeight.w900,
                    ),
                  ),
                  const SizedBox(height: 6),
                  Text(
                    l.t(
                      'Ton retour aide SwipeWear à mieux comprendre ton style.',
                    ),
                    style: TextStyle(color: AppColors.textSecondary),
                  ),
                  const SizedBox(height: 18),
                  ListTile(
                    leading: const CircleAvatar(
                      backgroundColor: AppColors.accentLight,
                      child: Icon(Icons.style_outlined),
                    ),
                    title: Text(
                      l.t('Pas mon style'),
                      style: TextStyle(fontWeight: FontWeight.w800),
                    ),
                    subtitle: Text(l.t('Je préfère voir autre chose.')),
                    onTap: () => Navigator.pop(context, 'swipe_left_style'),
                  ),
                  ListTile(
                    leading: const CircleAvatar(
                      backgroundColor: AppColors.accentLight,
                      child: Icon(Icons.euro_outlined),
                    ),
                    title: Text(
                      l.t('Trop cher'),
                      style: TextStyle(fontWeight: FontWeight.w800),
                    ),
                    subtitle: Text(l.t('Garde mon style, baisse le budget.')),
                    onTap: () => Navigator.pop(context, 'swipe_left_price'),
                  ),
                  const SizedBox(height: 8),
                  SizedBox(
                    width: double.infinity,
                    child: TextButton(
                      onPressed: () => Navigator.pop(context),
                      child: Text(l.t('Annuler')),
                    ),
                  ),
                ],
              ),
            ),
          ),
    );
    if (!mounted) return;
    setState(() => _dragOffset = Offset.zero);
    if (choice != null) await _swipe(choice);
  }

  Future<void> _showProduct(Product product) async {
    final session = ref.read(sessionProvider).valueOrNull;
    if (session != null) {
      try {
        await ref
            .read(feedRepositoryProvider)
            .postEvent(session, product.id, 'open');
      } catch (_) {}
    }
    if (!mounted) return;
    await Navigator.push(
      context,
      MaterialPageRoute(builder: (_) => ProductDetailScreen(product: product)),
    );
  }

  Future<void> _createAlert(Product product) async {
    final session = ref.read(sessionProvider).valueOrNull;
    if (session == null || _busy) return;
    setState(() => _busy = true);
    var created = false;
    try {
      final profile = ref.read(profileProvider).valueOrNull;
      final suggestedBudget = await _suggestAlertBudget(product);
      if (!mounted) return;
      final draft = await _showAlertEditor(
        product,
        initialBudget: suggestedBudget,
        initialSizes: profile?.sizes ?? const [],
      );
      if (draft == null || !mounted) return;
      await ref
          .read(alertsRepositoryProvider)
          .create(
            session,
            label: draft.label,
            // Swipe up means “hunt this style”, not only this exact listing.
            // The product id still gives the API the card embedding so the
            // alert is initialised from the user's current taste signal.
            type: 'style',
            referenceProductId: product.id,
            maxPrice: draft.budget,
            sizes: draft.sizes,
            minCondition: draft.minCondition,
          );
      unawaited(
        ref
            .read(analyticsServiceProvider)
            .track(
              session,
              'alert_created',
              properties: {'type': 'style', 'product_id': product.id},
            ),
      );
      ref.invalidate(alertsProvider);
      if (!mounted) return;
      created = true;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(
            AppLocalizations.of(
              context,
            ).t('Alerte créée. On chine cette pièce pour toi.'),
          ),
        ),
      );
    } on ApiException catch (error) {
      if (mounted) {
        if (error.statusCode == 403) {
          await Navigator.push(
            context,
            MaterialPageRoute(
              builder: (_) => const PaywallScreen(trigger: 'alert_limit'),
            ),
          );
        } else {
          ScaffoldMessenger.of(
            context,
          ).showSnackBar(SnackBar(content: Text(error.message)));
        }
      }
    } finally {
      if (mounted) {
        setState(() {
          if (created) _index++;
          _dragOffset = Offset.zero;
          _busy = false;
        });
      }
    }
  }

  Future<double?> _suggestAlertBudget(Product product) async {
    final prices = <double>[if (product.price > 0) product.price];
    try {
      final ladder = await ref.read(ladderProvider(product.id).future);
      prices.addAll(
        ladder.entries.map((entry) => entry.price).where((price) => price > 0),
      );
    } catch (_) {
      // The current price remains a safe fallback when the ladder is offline.
    }
    if (prices.isEmpty) return null;
    prices.sort();
    final median = prices[prices.length ~/ 2];
    return double.parse((median * .8).toStringAsFixed(2));
  }

  Future<_SwipeAlertDraft?> _showAlertEditor(
    Product product, {
    required double? initialBudget,
    required List<String> initialSizes,
  }) async {
    final l = AppLocalizations.of(context);
    final labelController = TextEditingController(text: product.title);
    final budgetController = TextEditingController(
      text: initialBudget?.toStringAsFixed(0),
    );
    final selectedSizes = {...initialSizes};
    var minCondition = 'Toutes';
    String? error;
    final draft = await showModalBottomSheet<_SwipeAlertDraft>(
      context: context,
      isScrollControlled: true,
      showDragHandle: true,
      builder:
          (context) => Padding(
            padding: EdgeInsets.fromLTRB(
              24,
              8,
              24,
              MediaQuery.viewInsetsOf(context).bottom + 24,
            ),
            child: StatefulBuilder(
              builder:
                  (context, setModalState) => SingleChildScrollView(
                    child: Column(
                      mainAxisSize: MainAxisSize.min,
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          l.t('Alerte sur ce style'),
                          style: Theme.of(context).textTheme.headlineSmall
                              ?.copyWith(fontWeight: FontWeight.w900),
                        ),
                        const SizedBox(height: 6),
                        Text(
                          l.t(
                            'On surveille les nouvelles pièces proches de cette trouvaille.',
                          ),
                        ),
                        const SizedBox(height: 18),
                        TextField(
                          controller: labelController,
                          decoration: InputDecoration(
                            labelText: l.t('Nom de la chasse'),
                          ),
                        ),
                        const SizedBox(height: 14),
                        Text(
                          l.t('Tailles recherchées'),
                          style: TextStyle(fontWeight: FontWeight.w800),
                        ),
                        const SizedBox(height: 8),
                        Wrap(
                          spacing: 7,
                          runSpacing: 7,
                          children:
                              availableSizes
                                  .map(
                                    (size) => ChoiceChip(
                                      label: Text(size),
                                      selected: selectedSizes.contains(size),
                                      onSelected:
                                          (_) => setModalState(() {
                                            if (!selectedSizes.add(size)) {
                                              selectedSizes.remove(size);
                                            }
                                          }),
                                    ),
                                  )
                                  .toList(),
                        ),
                        const SizedBox(height: 14),
                        TextField(
                          controller: budgetController,
                          keyboardType: const TextInputType.numberWithOptions(
                            decimal: true,
                          ),
                          decoration: InputDecoration(
                            labelText: l.t('Budget maximum'),
                            suffixText: '€',
                          ),
                        ),
                        const SizedBox(height: 14),
                        DropdownButtonFormField<String>(
                          value: minCondition,
                          decoration: InputDecoration(
                            labelText: l.t('État minimum'),
                          ),
                          items: [
                            DropdownMenuItem(
                              value: 'Toutes',
                              child: Text(l.t('Tous les états')),
                            ),
                            DropdownMenuItem(
                              value: 'good',
                              child: Text(l.t('Bon état minimum')),
                            ),
                            DropdownMenuItem(
                              value: 'like_new',
                              child: Text(l.t('Très bon état minimum')),
                            ),
                            DropdownMenuItem(
                              value: 'new',
                              child: Text(l.t('Neuf uniquement')),
                            ),
                          ],
                          onChanged: (value) {
                            if (value != null) {
                              setModalState(() => minCondition = value);
                            }
                          },
                        ),
                        if (error != null)
                          Padding(
                            padding: const EdgeInsets.only(top: 10),
                            child: Text(
                              error!,
                              style: const TextStyle(color: AppColors.error),
                            ),
                          ),
                        const SizedBox(height: 18),
                        FilledButton(
                          onPressed: () {
                            final label = labelController.text.trim();
                            final rawBudget = budgetController.text.trim();
                            final budget = double.tryParse(
                              rawBudget.replaceAll(',', '.'),
                            );
                            if (label.isEmpty) {
                              setModalState(
                                () => error = l.t('Donne un nom à ta chasse.'),
                              );
                              return;
                            }
                            if (budget == null || budget <= 0) {
                              setModalState(
                                () => error = l.t('Indique un budget valide.'),
                              );
                              return;
                            }
                            Navigator.pop(
                              context,
                              _SwipeAlertDraft(
                                label,
                                budget,
                                selectedSizes.toList(),
                                minCondition == 'Toutes' ? null : minCondition,
                              ),
                            );
                          },
                          child: Text(l.t('Activer cette alerte')),
                        ),
                        const SizedBox(height: 6),
                        Text(
                          l.t(
                            'Le budget proposé correspond à environ 80 % de la médiane des offres comparables.',
                          ),
                          style: TextStyle(
                            color: AppColors.textSecondary,
                            fontSize: 12,
                          ),
                        ),
                      ],
                    ),
                  ),
            ),
          ),
    );
    // The modal route may still be reversing when its Future completes. Keep
    // the controllers alive through that animation to avoid stale TextFields.
    await Future<void>.delayed(const Duration(milliseconds: 500));
    labelController.dispose();
    budgetController.dispose();
    return draft;
  }

  @override
  Widget build(BuildContext context) {
    final l = AppLocalizations.of(context);
    final feedAsync = ref.watch(feedProvider);
    return Scaffold(
      backgroundColor: Colors.transparent,
      appBar: AppBar(
        title: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text(
              'SwipeWear',
              style: TextStyle(
                fontSize: 10,
                color: AppColors.textSecondary,
                fontWeight: FontWeight.w800,
                letterSpacing: .2,
              ),
            ),
            Text(
              'Swipe',
              key: const ValueKey('feed-title'),
              style: TextStyle(
                fontSize: 24,
                fontWeight: FontWeight.w900,
                letterSpacing: -1,
              ),
            ),
            Text(
              l.t('Découvre. Swipe. Porte.'),
              style: TextStyle(
                fontSize: 10,
                color: AppColors.textSecondary,
                fontWeight: FontWeight.w700,
              ),
            ),
          ],
        ),
        actions: [
          IconButton(
            tooltip: l.t('Personnaliser mon feed'),
            onPressed: _showProductFilters,
            icon: const Icon(Icons.tune_rounded),
          ),
          IconButton(
            tooltip: l.t('Mes alertes'),
            onPressed: widget.onOpenAlerts,
            icon: Badge(
              isLabelVisible:
                  (ref.watch(alertsProvider).valueOrNull?.activeCount ?? 0) > 0,
              label: Text(
                '${ref.watch(alertsProvider).valueOrNull?.activeCount ?? 0}',
              ),
              child: const Icon(Icons.notifications_none_rounded),
            ),
          ),
        ],
      ),
      body: feedAsync.when(
        loading:
            () => const Center(
              child: CircularProgressIndicator(color: AppColors.accent),
            ),
        error:
            (error, _) => _ErrorState(
              message:
                  error is ApiException && error.statusCode == 503
                      ? l.t('Le feed est temporairement indisponible.')
                      : l.t('Impossible de charger tes pièces.'),
              onRetry: () => ref.invalidate(feedProvider),
            ),
        data: (feed) {
          _prefetchImages(feed);
          if (_index >= feed.items.length) {
            return _EmptyState(
              onReload: () {
                setState(() => _index = 0);
                _lastPrefetchStart = -1;
                ref.invalidate(feedProvider);
              },
            );
          }

          final current = feed.items[_index];
          final next =
              _index + 1 < feed.items.length ? feed.items[_index + 1] : null;
          final profile = ref.watch(profileProvider).valueOrNull;
          final calibration =
              ((profile?.eventCount ?? 0) / 30).clamp(0.0, 1.0).toDouble();
          return Column(
            children: [
              if (feed.isOffline) const OfflineBanner(),
              _StyleCalibration(progress: calibration),
              Expanded(
                child: Padding(
                  padding: const EdgeInsets.fromLTRB(20, 8, 20, 8),
                  child: Stack(
                    alignment: Alignment.center,
                    children: [
                      if (next != null)
                        _ProductCard(product: next.product, scale: .94),
                      GestureDetector(
                        onPanUpdate:
                            (details) =>
                                setState(() => _dragOffset += details.delta),
                        onPanEnd: (_) => _handleDragEnd(),
                        onTap: () => _showProduct(current.product),
                        child: Transform.translate(
                          offset: _dragOffset,
                          child: Transform.rotate(
                            angle: _dragOffset.dx / 1200,
                            child: Stack(
                              children: [
                                _ProductCard(
                                  product: current.product,
                                  onFavorite: () => _swipe('swipe_right'),
                                ),
                                if (_dragOffset.dx.abs() > 20 ||
                                    _dragOffset.dy < -20)
                                  Positioned(
                                    top: 24,
                                    left: _dragOffset.dx >= 0 ? 24 : null,
                                    right: _dragOffset.dx < 0 ? 24 : null,
                                    child: _SwipeLabel(
                                      label:
                                          _dragOffset.dy < -20
                                              ? l.t('ALERTE')
                                              : (_dragOffset.dx > 0
                                                  ? l.t('J’AIME')
                                                  : l.t('NON')),
                                      color:
                                          _dragOffset.dy < -20
                                              ? AppColors.accent
                                              : (_dragOffset.dx > 0
                                                  ? AppColors.success
                                                  : AppColors.error),
                                    ),
                                  ),
                              ],
                            ),
                          ),
                        ),
                      ),
                    ],
                  ),
                ),
              ),
              Padding(
                padding: const EdgeInsets.fromLTRB(24, 4, 24, 24),
                child: Row(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    _ActionButton(
                      icon: Icons.close_rounded,
                      label: l.t('Passer'),
                      onPressed: _chooseRejection,
                    ),
                    const SizedBox(width: 20),
                    _ActionButton(
                      icon: Icons.notifications_none_rounded,
                      label: l.t('Créer une alerte'),
                      emphasized: true,
                      onPressed: () => _createAlert(current.product),
                    ),
                    const SizedBox(width: 20),
                    _ActionButton(
                      icon: Icons.favorite_rounded,
                      label: l.t('Ajouter au dressing'),
                      positive: true,
                      onPressed: () => _swipe('swipe_right'),
                    ),
                  ],
                ),
              ),
            ],
          );
        },
      ),
    );
  }

  void _showProductFilters() {
    final l = AppLocalizations.of(context);
    showModalBottomSheet<void>(
      context: context,
      builder:
          (context) => SafeArea(
            child: Padding(
              padding: const EdgeInsets.fromLTRB(24, 4, 24, 28),
              child: Column(
                mainAxisSize: MainAxisSize.min,
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    l.t('Ton feed est personnalisé'),
                    style: Theme.of(context).textTheme.headlineSmall,
                  ),
                  const SizedBox(height: 8),
                  Text(
                    l.t(
                      'Les tailles, le budget et tes swipes ajustent automatiquement les pièces proposées.',
                    ),
                    style: const TextStyle(
                      color: AppColors.textSecondary,
                      height: 1.4,
                    ),
                  ),
                  const SizedBox(height: 18),
                  FilledButton(
                    onPressed: () => Navigator.pop(context),
                    child: Text(l.t('Compris')),
                  ),
                ],
              ),
            ),
          ),
    );
  }
}

class _SwipeAlertDraft {
  const _SwipeAlertDraft(
    this.label,
    this.budget,
    this.sizes,
    this.minCondition,
  );

  final String label;
  final double budget;
  final List<String> sizes;
  final String? minCondition;
}

class _ProductCard extends StatelessWidget {
  const _ProductCard({required this.product, this.scale = 1, this.onFavorite});

  final Product product;
  final double scale;
  final VoidCallback? onFavorite;

  @override
  Widget build(BuildContext context) {
    final l = AppLocalizations.of(context);
    final image = product.imageUrls.isNotEmpty ? product.imageUrls.first : null;
    return Transform.scale(
      scale: scale,
      child: AspectRatio(
        aspectRatio: .68,
        child: Card(
          margin: EdgeInsets.zero,
          clipBehavior: Clip.antiAlias,
          color: Colors.white,
          child: Column(
            children: [
              Expanded(
                flex: 7,
                child: Stack(
                  fit: StackFit.expand,
                  children: [
                    if (image != null)
                      Image.network(
                        image,
                        fit: BoxFit.cover,
                        errorBuilder: (_, __, ___) => const _ImageFallback(),
                        loadingBuilder:
                            (context, child, progress) =>
                                progress == null
                                    ? child
                                    : const _ImageFallback(),
                      )
                    else
                      const _ImageFallback(),
                    Positioned(
                      top: 14,
                      left: 14,
                      child: _Pill(
                        label: _sourceLabel(product.source),
                        dark: true,
                      ),
                    ),
                    Positioned(
                      top: 4,
                      right: 4,
                      child:
                          onFavorite == null
                              ? CircleAvatar(
                                radius: 18,
                                backgroundColor: Colors.white.withValues(
                                  alpha: .9,
                                ),
                                child: const Icon(
                                  Icons.favorite_border,
                                  size: 20,
                                ),
                              )
                              : IconButton(
                                onPressed: onFavorite,
                                tooltip: l.t('Ajouter au dressing'),
                                style: IconButton.styleFrom(
                                  backgroundColor: Colors.white.withValues(
                                    alpha: .9,
                                  ),
                                  foregroundColor: AppColors.error,
                                ),
                                icon: const Icon(Icons.favorite_border),
                              ),
                    ),
                  ],
                ),
              ),
              Expanded(
                flex: 3,
                child: Padding(
                  padding: const EdgeInsets.fromLTRB(14, 10, 14, 12),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Expanded(
                            child: Text(
                              product.brand.isEmpty
                                  ? l.t('Sélection')
                                  : product.brand,
                              maxLines: 1,
                              overflow: TextOverflow.ellipsis,
                              style: const TextStyle(
                                fontWeight: FontWeight.w900,
                                fontSize: 15,
                              ),
                            ),
                          ),
                          Text(
                            l.price(product.price),
                            style: const TextStyle(
                              color: AppColors.textPrimary,
                              fontWeight: FontWeight.w900,
                              fontSize: 18,
                            ),
                          ),
                        ],
                      ),
                      const SizedBox(height: 3),
                      Text(
                        product.title,
                        maxLines: 1,
                        overflow: TextOverflow.ellipsis,
                        style: const TextStyle(
                          color: AppColors.textSecondary,
                          fontSize: 12,
                        ),
                      ),
                      const Spacer(),
                      Wrap(
                        spacing: 6,
                        runSpacing: 4,
                        children: [
                          _Pill(label: _conditionLabel(product.condition)),
                          if (product.size != null && product.size!.isNotEmpty)
                            _Pill(
                              label:
                                  l.isEnglish
                                      ? 'Size ${product.size}'
                                      : 'Taille ${product.size}',
                            ),
                          if (product.ageLabel != null)
                            _Pill(label: product.ageLabel!),
                        ],
                      ),
                    ],
                  ),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _StyleCalibration extends StatelessWidget {
  const _StyleCalibration({required this.progress});

  final double progress;

  @override
  Widget build(BuildContext context) => Padding(
    padding: const EdgeInsets.fromLTRB(24, 2, 24, 6),
    child: Column(
      children: [
        Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            Text(
              AppLocalizations.of(context).t('🧠 PROFIL DE STYLE CALIBRÉ'),
              style: TextStyle(
                color: AppColors.textSecondary,
                fontSize: 10,
                fontWeight: FontWeight.w900,
                letterSpacing: .8,
              ),
            ),
            Text(
              '${(progress * 100).round()}%',
              style: const TextStyle(fontSize: 11, fontWeight: FontWeight.w900),
            ),
          ],
        ),
        const SizedBox(height: 5),
        ClipRRect(
          borderRadius: BorderRadius.circular(99),
          child: LinearProgressIndicator(
            value: progress,
            minHeight: 4,
            backgroundColor: AppColors.surface,
            valueColor: const AlwaysStoppedAnimation(AppColors.accent),
          ),
        ),
      ],
    ),
  );
}

String _conditionLabel(String value) => switch (value.toLowerCase()) {
  'new' => 'NEUF',
  'like_new' => 'TRÈS BON ÉTAT',
  'fair' => 'BON ÉTAT',
  _ => 'BON ÉTAT',
};

String _sourceLabel(String value) => switch (value.toLowerCase()) {
  'ebay' => 'eBay',
  'etsy' => 'Etsy',
  'vc' || 'vestiaire_collective' => 'VESTIAIRE',
  'awin' || 'cj' => 'NEUF',
  _ => value.toUpperCase(),
};

class _ImageFallback extends StatelessWidget {
  const _ImageFallback();

  @override
  Widget build(BuildContext context) => Container(
    color: AppColors.surface,
    alignment: Alignment.center,
    child: const Icon(
      Icons.checkroom_rounded,
      size: 72,
      color: AppColors.textSecondary,
    ),
  );
}

class _Pill extends StatelessWidget {
  const _Pill({required this.label, this.dark = false});

  final String label;
  final bool dark;

  @override
  Widget build(BuildContext context) => DecoratedBox(
    decoration: BoxDecoration(
      color: dark ? Colors.black.withValues(alpha: .62) : AppColors.accentLight,
      borderRadius: BorderRadius.circular(99),
      border: dark ? Border.all(color: Colors.white24) : null,
    ),
    child: Padding(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
      child: Text(
        label,
        style: TextStyle(
          color: dark ? Colors.white : AppColors.textPrimary,
          fontSize: 10,
          fontWeight: FontWeight.w700,
        ),
      ),
    ),
  );
}

class _SwipeLabel extends StatelessWidget {
  const _SwipeLabel({required this.label, required this.color});

  final String label;
  final Color color;

  @override
  Widget build(BuildContext context) => Transform.rotate(
    angle: -math.pi / 18,
    child: DecoratedBox(
      decoration: BoxDecoration(
        border: Border.all(color: color, width: 3),
        borderRadius: BorderRadius.circular(8),
      ),
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
        child: Text(
          label,
          style: TextStyle(
            color: color,
            fontSize: 21,
            fontWeight: FontWeight.w900,
          ),
        ),
      ),
    ),
  );
}

class _ActionButton extends StatelessWidget {
  const _ActionButton({
    required this.icon,
    required this.label,
    required this.onPressed,
    this.emphasized = false,
    this.positive = false,
  });

  final IconData icon;
  final String label;
  final VoidCallback onPressed;
  final bool emphasized;
  final bool positive;

  @override
  Widget build(BuildContext context) => Semantics(
    button: true,
    label: label,
    child: IconButton.filled(
      onPressed: onPressed,
      tooltip: label,
      icon: Icon(icon, semanticLabel: label),
      iconSize: emphasized ? 27 : 24,
      style: IconButton.styleFrom(
        minimumSize: Size.square(emphasized ? 64 : 56),
        backgroundColor:
            emphasized
                ? AppColors.accentLight
                : (positive ? AppColors.textPrimary : AppColors.surface),
        foregroundColor:
            emphasized
                ? AppColors.textPrimary
                : (positive ? Colors.white : AppColors.textSecondary),
        side: emphasized ? null : const BorderSide(color: AppColors.border),
      ),
    ),
  );
}

class _ErrorState extends StatelessWidget {
  const _ErrorState({required this.message, required this.onRetry});

  final String message;
  final VoidCallback onRetry;

  @override
  Widget build(BuildContext context) => Center(
    child: Padding(
      padding: const EdgeInsets.all(32),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          const Icon(
            Icons.cloud_off_rounded,
            size: 56,
            color: AppColors.textSecondary,
          ),
          const SizedBox(height: 16),
          Text(
            message,
            textAlign: TextAlign.center,
            style: Theme.of(context).textTheme.titleLarge,
          ),
          const SizedBox(height: 16),
          FilledButton(
            onPressed: onRetry,
            child: Text(AppLocalizations.of(context).t('Réessayer')),
          ),
        ],
      ),
    ),
  );
}

class _EmptyState extends StatelessWidget {
  const _EmptyState({required this.onReload});

  final VoidCallback onReload;

  @override
  Widget build(BuildContext context) => Center(
    child: Column(
      mainAxisSize: MainAxisSize.min,
      children: [
        const Icon(
          Icons.check_circle_outline_rounded,
          size: 56,
          color: AppColors.textSecondary,
        ),
        const SizedBox(height: 16),
        Text(
          AppLocalizations.of(context).t('Tout vu !'),
          style: Theme.of(context).textTheme.headlineSmall,
        ),
        const SizedBox(height: 8),
        Text(
          AppLocalizations.of(
            context,
          ).t('Plus de pièces à swiper pour le moment.'),
        ),
        const SizedBox(height: 16),
        FilledButton(
          onPressed: onReload,
          child: Text(AppLocalizations.of(context).t('Charger plus')),
        ),
      ],
    ),
  );
}
