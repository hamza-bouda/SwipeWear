import 'dart:ui' as ui;

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter/rendering.dart';
import 'package:share_plus/share_plus.dart';
import 'package:url_launcher/url_launcher.dart';

import '../../../core/analytics/analytics_screen_view.dart';
import '../../../core/localization/app_localizations.dart';
import '../../../core/network/api_client.dart';
import '../../../core/theme/app_theme.dart';
import '../../alerts/providers.dart';
import '../../auth/providers.dart';
import '../../billing/presentation/paywall_screen.dart';
import '../../feed/data/product.dart';
import '../data/ladder_repository.dart';
import '../providers.dart';

class PriceLadderScreen extends ConsumerStatefulWidget {
  const PriceLadderScreen({super.key, required this.product});

  final Product product;

  @override
  ConsumerState<PriceLadderScreen> createState() => _PriceLadderScreenState();
}

class _PriceLadderScreenState extends ConsumerState<PriceLadderScreen> {
  String _sourceFilter = 'Toutes';
  String _conditionFilter = 'Toutes';
  RangeValues? _priceRange;

  Future<void> _openOffer(LadderEntry entry, int position) async {
    final l = AppLocalizations.of(context);
    final url = entry.url;
    if (url == null || url.isEmpty) return;
    try {
      final session = await ref.read(sessionProvider.future);
      await ref
          .read(ladderRepositoryProvider)
          .outboundClick(session, entry, position);
    } catch (_) {}
    final opened = await launchUrl(
      Uri.parse(url),
      mode: LaunchMode.externalApplication,
    );
    if (!opened && mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(l.t('Impossible d’ouvrir l’annonce.'))),
      );
    }
  }

  Future<void> _createAlert(BuildContext context) async {
    final l = AppLocalizations.of(context);
    try {
      final session = await ref.read(sessionProvider.future);
      await ref
          .read(alertsRepositoryProvider)
          .create(
            session,
            label: widget.product.title,
            type: 'specific_item',
            referenceProductId: widget.product.id,
            maxPrice: widget.product.price,
          );
      await ref.read(ladderRepositoryProvider).recordAnalytics(
        session,
        'alert_created',
        {
          'type': 'specific_item',
          'product_id': widget.product.id,
          'surface': 'ladder',
        },
      );
      ref.invalidate(alertsProvider);
      if (context.mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text(l.t('Alerte créée. On chine pour toi.'))),
        );
      }
    } on ApiException catch (error) {
      if (context.mounted) {
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
    }
  }

  Future<void> _openShare(BuildContext context, PriceLadder ladder) async {
    await showDialog<void>(
      context: context,
      builder:
          (_) => ShareCardDialog(
            product: widget.product,
            ladder: ladder,
            onShared: () async {
              try {
                final session = await ref.read(sessionProvider.future);
                await ref
                    .read(ladderRepositoryProvider)
                    .recordAnalytics(session, 'share_card_generated', {
                      'product_id': widget.product.id,
                      'savings_pct': ladder.savingsPct,
                      'ladder_count': ladder.entries.length,
                    });
              } catch (_) {}
            },
          ),
    );
  }

  List<LadderEntry> _filteredEntries(
    List<LadderEntry> entries,
    RangeValues range,
  ) {
    final minimumCondition = _conditionRank(_conditionFilter);
    return entries
        .where((entry) {
          final sourceMatches =
              _sourceFilter == 'Toutes' || entry.source == _sourceFilter;
          final conditionMatches =
              _conditionFilter == 'Toutes' ||
              _conditionRank(entry.condition) >= minimumCondition;
          final priceMatches =
              entry.price >= range.start && entry.price <= range.end;
          return sourceMatches && conditionMatches && priceMatches;
        })
        .toList(growable: false);
  }

  double _maxObservedPrice(List<LadderEntry> entries) {
    var maximum = 1.0;
    for (final entry in entries) {
      if (entry.price > maximum) maximum = entry.price;
    }
    return maximum;
  }

  RangeValues _effectiveRange(double maximum) {
    final stored = _priceRange ?? RangeValues(0, maximum);
    final start = stored.start.clamp(0.0, maximum).toDouble();
    final end = stored.end.clamp(0.0, maximum).toDouble();
    return start <= end ? RangeValues(start, end) : RangeValues(0, maximum);
  }

  void _resetFilters(double maximum) {
    setState(() {
      _sourceFilter = 'Toutes';
      _conditionFilter = 'Toutes';
      _priceRange = RangeValues(0, maximum);
    });
  }

  @override
  Widget build(BuildContext context) {
    final l = AppLocalizations.of(context);
    final product = widget.product;
    final ladder = ref.watch(ladderProvider(product.id));
    return Scaffold(
      appBar: AppBar(
        title: Text(
          l.t('Échelle de prix'),
          style: TextStyle(fontWeight: FontWeight.w900),
        ),
        actions: [
          IconButton(
            onPressed:
                ladder.valueOrNull == null
                    ? null
                    : () => _openShare(context, ladder.valueOrNull!),
            icon: const Icon(Icons.ios_share_outlined),
            tooltip: l.t('Partager'),
          ),
        ],
      ),
      body: AnalyticsScreenView(
        name: 'ladder_viewed',
        properties: {'product_id': product.id},
        child: ladder.when(
          loading:
              () => const Center(
                child: CircularProgressIndicator(color: AppColors.accent),
              ),
          error:
              (_, __) => _LadderMessage(
                icon: Icons.compare_arrows_outlined,
                title: l.t('Comparaison indisponible'),
                action: TextButton(
                  onPressed: () => ref.invalidate(ladderProvider(product.id)),
                  child: Text(l.t('Réessayer')),
                ),
              ),
          data: (data) {
            final maximum = _maxObservedPrice(data.entries);
            final range = _effectiveRange(maximum);
            final entries = _filteredEntries(data.entries, range);
            final sourceOptions =
                <String>{...data.entries.map((entry) => entry.source)}.toList()
                  ..sort();
            return RefreshIndicator(
              onRefresh: () async {
                ref.invalidate(ladderProvider(product.id));
                await ref.read(ladderProvider(product.id).future);
              },
              child: ListView(
                padding: const EdgeInsets.fromLTRB(20, 8, 20, 32),
                children: [
                  _SourceProduct(product: product),
                  if (data.savingsPct != null)
                    Container(
                      margin: const EdgeInsets.only(top: 16),
                      padding: const EdgeInsets.all(16),
                      decoration: BoxDecoration(
                        color: AppColors.accentLight,
                        borderRadius: BorderRadius.circular(18),
                      ),
                      child: Text(
                        l.isEnglish
                            ? 'Up to ${data.savingsPct!.round()}% saved vs new'
                            : 'Jusqu’à ${data.savingsPct!.round()} % d’économie vs le neuf',
                        style: const TextStyle(fontWeight: FontWeight.w900),
                      ),
                    ),
                  if (data.entries.isNotEmpty) ...[
                    const SizedBox(height: 22),
                    Text(
                      l.t('Filtrer les offres'),
                      style: TextStyle(
                        fontWeight: FontWeight.w900,
                        fontSize: 16,
                      ),
                    ),
                    const SizedBox(height: 10),
                    Text(
                      l.t('Sources'),
                      style: TextStyle(
                        color: AppColors.textSecondary,
                        fontSize: 12,
                        fontWeight: FontWeight.w700,
                      ),
                    ),
                    const SizedBox(height: 6),
                    SizedBox(
                      height: 42,
                      child: ListView.separated(
                        scrollDirection: Axis.horizontal,
                        itemCount: sourceOptions.length + 1,
                        separatorBuilder: (_, __) => const SizedBox(width: 8),
                        itemBuilder: (_, index) {
                          final source =
                              index == 0 ? 'Toutes' : sourceOptions[index - 1];
                          return ChoiceChip(
                            label: Text(_sourceLabel(source, l)),
                            selected: _sourceFilter == source,
                            onSelected:
                                (_) => setState(() => _sourceFilter = source),
                          );
                        },
                      ),
                    ),
                    const SizedBox(height: 10),
                    Text(
                      l.t('État minimum'),
                      style: TextStyle(
                        color: AppColors.textSecondary,
                        fontSize: 12,
                        fontWeight: FontWeight.w700,
                      ),
                    ),
                    const SizedBox(height: 6),
                    SizedBox(
                      height: 42,
                      child: ListView.separated(
                        scrollDirection: Axis.horizontal,
                        itemCount: _conditionOptions.length,
                        separatorBuilder: (_, __) => const SizedBox(width: 8),
                        itemBuilder: (_, index) {
                          final condition = _conditionOptions[index];
                          return ChoiceChip(
                            label: Text(l.t(condition.label)),
                            selected: _conditionFilter == condition.value,
                            onSelected:
                                (_) => setState(
                                  () => _conditionFilter = condition.value,
                                ),
                          );
                        },
                      ),
                    ),
                    const SizedBox(height: 8),
                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        Text(
                          l.t('Fourchette de prix'),
                          style: TextStyle(
                            color: AppColors.textSecondary,
                            fontSize: 12,
                            fontWeight: FontWeight.w700,
                          ),
                        ),
                        Text(
                          '${l.price(range.start)} – ${l.price(range.end)}',
                          style: const TextStyle(
                            fontSize: 12,
                            fontWeight: FontWeight.w900,
                          ),
                        ),
                      ],
                    ),
                    RangeSlider(
                      values: range,
                      min: 0,
                      max: maximum,
                      divisions: maximum > 1 ? 20 : null,
                      onChanged: (value) => setState(() => _priceRange = value),
                    ),
                  ],
                  const SizedBox(height: 26),
                  Text(
                    l.t('👀 Dans le même style, du moins cher au plus cher'),
                    style: Theme.of(context).textTheme.titleMedium?.copyWith(
                      fontWeight: FontWeight.w900,
                    ),
                  ),
                  const SizedBox(height: 12),
                  if (data.entries.isEmpty) ...[
                    _LadderMessage(
                      icon: Icons.search_off_outlined,
                      title: l.t('Aucune offre comparable trouvée'),
                    ),
                    FilledButton.icon(
                      onPressed: () => _createAlert(context),
                      icon: const Icon(Icons.notifications_none),
                      label: Text(l.t('Créer une alerte sur ce style')),
                    ),
                  ] else if (entries.isEmpty) ...[
                    _LadderMessage(
                      icon: Icons.filter_alt_off_outlined,
                      title: l.t('Aucune offre ne correspond à ces filtres'),
                    ),
                    TextButton(
                      onPressed: () => _resetFilters(maximum),
                      child: Text(l.t('Réinitialiser les filtres')),
                    ),
                  ] else
                    ...entries.asMap().entries.map(
                      (item) => _OfferRow(
                        entry: item.value,
                        position: item.key + 1,
                        onTap: () => _openOffer(item.value, item.key + 1),
                      ),
                    ),
                  if (entries.isNotEmpty) ...[
                    const SizedBox(height: 12),
                    OutlinedButton.icon(
                      onPressed: () => _createAlert(context),
                      icon: const Icon(Icons.notifications_none),
                      label: Text(l.t('Être alerté sur cette pièce')),
                    ),
                  ],
                  const SizedBox(height: 12),
                  Text(
                    l.t(
                      'Lien partenaire · Les prix et disponibilités sont fournis par les plateformes partenaires.',
                    ),
                    style: TextStyle(
                      color: AppColors.textSecondary,
                      fontSize: 11,
                    ),
                  ),
                ],
              ),
            );
          },
        ),
      ),
    );
  }
}

const _conditionOptions = [
  _ConditionOption('Toutes', 'Tous les états'),
  _ConditionOption('fair', 'État correct +'),
  _ConditionOption('good', 'Bon état +'),
  _ConditionOption('like_new', 'Très bon état +'),
  _ConditionOption('new', 'Neuf'),
];

class _ConditionOption {
  const _ConditionOption(this.value, this.label);
  final String value;
  final String label;
}

int _conditionRank(String value) => switch (value) {
  'new' => 3,
  'like_new' || 'very_good' => 2,
  'good' => 1,
  'fair' => 0,
  _ => -1,
};

String _conditionLabel(String value) => switch (value) {
  'new' => 'NEUF',
  'like_new' || 'very_good' => 'TRÈS BON ÉTAT',
  'good' => 'BON ÉTAT',
  'fair' => 'ÉTAT CORRECT',
  _ => value.toUpperCase(),
};

String _sourceLabel(String value, AppLocalizations l) => switch (value) {
  'ebay' => 'eBay',
  'etsy' => 'Etsy',
  'vc' || 'vestiaire_collective' => l.t('Vestiaire'),
  'awin' || 'cj' => l.t('Neuf'),
  _ => value.toUpperCase(),
};

class ShareCardDialog extends StatefulWidget {
  const ShareCardDialog({
    super.key,
    required this.product,
    required this.ladder,
    this.onShared,
  });

  final Product product;
  final PriceLadder ladder;
  final Future<void> Function()? onShared;

  @override
  State<ShareCardDialog> createState() => _ShareCardDialogState();
}

class _ShareCardDialogState extends State<ShareCardDialog> {
  final _cardKey = GlobalKey();
  bool _sharing = false;
  String? _error;

  Future<void> _share() async {
    final l = AppLocalizations.of(context);
    setState(() {
      _sharing = true;
      _error = null;
    });
    try {
      await Future<void>.delayed(const Duration(milliseconds: 80));
      final renderObject = _cardKey.currentContext?.findRenderObject();
      if (renderObject is! RenderRepaintBoundary) {
        throw StateError(l.t('La carte de partage n’est pas prête.'));
      }
      final image = await renderObject.toImage(pixelRatio: 3);
      final byteData = await image.toByteData(format: ui.ImageByteFormat.png);
      if (byteData == null) throw StateError(l.t('Image indisponible.'));
      final bytes = byteData.buffer.asUint8List();
      await Share.shareXFiles(
        [
          XFile.fromData(
            bytes,
            mimeType: 'image/png',
            name: 'swipewear-share.png',
          ),
        ],
        text:
            l.isEnglish
                ? 'I found ${widget.product.title} on SwipeWear.'
                : 'J’ai trouvé ${widget.product.title} sur SwipeWear.',
        fileNameOverrides: const ['swipewear-share.png'],
      );
      await widget.onShared?.call();
      if (mounted) {
        Navigator.pop(context);
      }
    } catch (_) {
      if (mounted) {
        setState(() {
          _sharing = false;
          _error = l.t(
            'Impossible de préparer la carte. Réessaie dans un instant.',
          );
        });
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final l = AppLocalizations.of(context);
    return AlertDialog(
      title: Text(
        l.t('Partager ma trouvaille'),
        style: TextStyle(fontWeight: FontWeight.w900),
      ),
      content: SingleChildScrollView(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            RepaintBoundary(
              key: _cardKey,
              child: _ShareCard(product: widget.product, ladder: widget.ladder),
            ),
            if (_error != null)
              Padding(
                padding: const EdgeInsets.only(top: 12),
                child: Text(
                  _error!,
                  style: const TextStyle(color: AppColors.error),
                ),
              ),
          ],
        ),
      ),
      actions: [
        TextButton(
          onPressed: _sharing ? null : () => Navigator.pop(context),
          child: Text(l.t('Annuler')),
        ),
        FilledButton.icon(
          onPressed: _sharing ? null : _share,
          icon:
              _sharing
                  ? const SizedBox(
                    width: 18,
                    height: 18,
                    child: CircularProgressIndicator(strokeWidth: 2),
                  )
                  : const Icon(Icons.ios_share_outlined),
          label: Text(_sharing ? l.t('Préparation…') : l.t('Partager')),
        ),
      ],
    );
  }
}

class _ShareCard extends StatelessWidget {
  const _ShareCard({required this.product, required this.ladder});

  final Product product;
  final PriceLadder ladder;

  @override
  Widget build(BuildContext context) {
    final l = AppLocalizations.of(context);
    return SizedBox(
      width: 330,
      height: 590,
      child: DecoratedBox(
        decoration: BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.circular(24),
          border: Border.all(color: AppColors.border),
        ),
        child: ClipRRect(
          borderRadius: BorderRadius.circular(24),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Container(
                color: AppColors.accent,
                padding: const EdgeInsets.fromLTRB(18, 14, 18, 12),
                child: Row(
                  children: [
                    Icon(Icons.checkroom_rounded, size: 20),
                    SizedBox(width: 8),
                    Text(
                      'SwipeWear',
                      style: TextStyle(
                        fontWeight: FontWeight.w900,
                        fontSize: 18,
                      ),
                    ),
                    Spacer(),
                    Text(
                      l.t('TROUVAILLE'),
                      style: TextStyle(
                        fontSize: 10,
                        fontWeight: FontWeight.w900,
                      ),
                    ),
                  ],
                ),
              ),
              SizedBox(
                height: 230,
                width: double.infinity,
                child:
                    product.imageUrls.isEmpty
                        ? const ColoredBox(
                          color: AppColors.accentLight,
                          child: Center(
                            child: Icon(Icons.checkroom_rounded, size: 58),
                          ),
                        )
                        : Image.network(
                          product.imageUrls.first,
                          fit: BoxFit.cover,
                          errorBuilder:
                              (_, __, ___) => const ColoredBox(
                                color: AppColors.accentLight,
                                child: Center(
                                  child: Icon(
                                    Icons.checkroom_rounded,
                                    size: 58,
                                  ),
                                ),
                              ),
                        ),
              ),
              Padding(
                padding: const EdgeInsets.fromLTRB(18, 14, 18, 8),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      product.brand.isEmpty
                          ? l.t('Sélection SwipeWear')
                          : product.brand,
                      style: const TextStyle(
                        color: AppColors.textSecondary,
                        fontSize: 11,
                        fontWeight: FontWeight.w700,
                      ),
                    ),
                    const SizedBox(height: 4),
                    Text(
                      product.title,
                      maxLines: 2,
                      overflow: TextOverflow.ellipsis,
                      style: const TextStyle(
                        fontWeight: FontWeight.w900,
                        fontSize: 17,
                        height: 1.1,
                      ),
                    ),
                    const SizedBox(height: 5),
                    Text(
                      '${l.price(product.price)} ${product.currency}',
                      style: const TextStyle(
                        fontSize: 22,
                        fontWeight: FontWeight.w900,
                        color: AppColors.textPrimary,
                      ),
                    ),
                  ],
                ),
              ),
              if (ladder.savingsPct != null && ladder.savingsPct! > 0)
                Padding(
                  padding: const EdgeInsets.symmetric(
                    horizontal: 18,
                    vertical: 4,
                  ),
                  child: DecoratedBox(
                    decoration: BoxDecoration(
                      color: AppColors.accentLight,
                      borderRadius: BorderRadius.circular(9),
                    ),
                    child: Padding(
                      padding: const EdgeInsets.symmetric(
                        horizontal: 9,
                        vertical: 6,
                      ),
                      child: Text(
                        l.isEnglish
                            ? 'Up to -${ladder.savingsPct!.round()}% vs new'
                            : 'Jusqu’à -${ladder.savingsPct!.round()} % vs neuf',
                        style: const TextStyle(
                          fontWeight: FontWeight.w900,
                          fontSize: 11,
                        ),
                      ),
                    ),
                  ),
                ),
              Padding(
                padding: EdgeInsets.fromLTRB(18, 8, 18, 5),
                child: Text(
                  l.t('Échelle de prix'),
                  style: TextStyle(fontWeight: FontWeight.w900, fontSize: 12),
                ),
              ),
              Expanded(
                child: Padding(
                  padding: const EdgeInsets.symmetric(horizontal: 18),
                  child:
                      ladder.entries.isEmpty
                          ? Align(
                            alignment: Alignment.topLeft,
                            child: Text(
                              l.t('Aucune offre comparable pour le moment.'),
                              style: TextStyle(
                                color: AppColors.textSecondary,
                                fontSize: 11,
                              ),
                            ),
                          )
                          : Column(
                            children:
                                ladder.entries
                                    .take(3)
                                    .map(
                                      (entry) => Padding(
                                        padding: const EdgeInsets.only(
                                          bottom: 5,
                                        ),
                                        child: Row(
                                          children: [
                                            Expanded(
                                              child: Text(
                                                entry.source.toUpperCase(),
                                                style: const TextStyle(
                                                  color:
                                                      AppColors.textSecondary,
                                                  fontSize: 10,
                                                  fontWeight: FontWeight.w700,
                                                ),
                                              ),
                                            ),
                                            Text(
                                              l.price(entry.price),
                                              style: const TextStyle(
                                                fontWeight: FontWeight.w900,
                                                fontSize: 12,
                                              ),
                                            ),
                                          ],
                                        ),
                                      ),
                                    )
                                    .toList(),
                          ),
                ),
              ),
              Container(
                color: AppColors.textPrimary,
                width: double.infinity,
                padding: const EdgeInsets.symmetric(vertical: 11),
                child: Center(
                  child: Text(
                    l.t('swipewear.fr · lien partenaire'),
                    style: TextStyle(
                      color: AppColors.accent,
                      fontSize: 10,
                      fontWeight: FontWeight.w800,
                    ),
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

class _SourceProduct extends StatelessWidget {
  const _SourceProduct({required this.product});
  final Product product;

  @override
  Widget build(BuildContext context) {
    final l = AppLocalizations.of(context);
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(14),
        child: Row(
          children: [
            SizedBox(
              width: 72,
              height: 86,
              child: ClipRRect(
                borderRadius: BorderRadius.circular(12),
                child:
                    product.imageUrls.isEmpty
                        ? const ColoredBox(color: AppColors.accentLight)
                        : Image.network(
                          product.imageUrls.first,
                          fit: BoxFit.cover,
                          excludeFromSemantics: true,
                          errorBuilder:
                              (_, __, ___) => const ColoredBox(
                                color: AppColors.accentLight,
                                child: Center(
                                  child: Icon(
                                    Icons.checkroom_rounded,
                                    size: 32,
                                  ),
                                ),
                              ),
                        ),
              ),
            ),
            const SizedBox(width: 14),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    product.brand,
                    style: const TextStyle(
                      color: AppColors.textSecondary,
                      fontSize: 12,
                    ),
                  ),
                  Text(
                    product.title,
                    maxLines: 2,
                    overflow: TextOverflow.ellipsis,
                    style: const TextStyle(fontWeight: FontWeight.w800),
                  ),
                  const SizedBox(height: 6),
                  Text(
                    '${l.price(product.price)} ${product.currency}',
                    style: const TextStyle(
                      color: AppColors.textPrimary,
                      fontWeight: FontWeight.w900,
                    ),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _OfferRow extends StatelessWidget {
  const _OfferRow({
    required this.entry,
    required this.position,
    required this.onTap,
  });
  final LadderEntry entry;
  final int position;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    final image =
        entry.imageUrl == null
            ? const ColoredBox(color: AppColors.surface)
            : Image.network(
              entry.imageUrl!,
              fit: BoxFit.cover,
              errorBuilder:
                  (_, __, ___) => const ColoredBox(color: AppColors.surface),
            );
    return Card(
      margin: const EdgeInsets.only(bottom: 10),
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(20),
        child: Padding(
          padding: const EdgeInsets.all(10),
          child: Row(
            children: [
              SizedBox(
                width: 64,
                height: 64,
                child: ClipRRect(
                  borderRadius: BorderRadius.circular(12),
                  child: image,
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      entry.title,
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                      style: const TextStyle(fontWeight: FontWeight.w800),
                    ),
                    const SizedBox(height: 4),
                    Wrap(
                      spacing: 5,
                      runSpacing: 4,
                      children: [
                        _MiniTag(
                          _sourceLabel(
                            entry.source,
                            AppLocalizations.of(context),
                          ),
                        ),
                        _MiniTag(
                          entry.isNew
                              ? AppLocalizations.of(context).t('NEUF')
                              : AppLocalizations.of(context).t('OCCASION'),
                        ),
                        _MiniTag(
                          AppLocalizations.of(
                            context,
                          ).t(_conditionLabel(entry.condition)),
                        ),
                        _MiniTag(
                          entry.confidence == 'exact'
                              ? AppLocalizations.of(context).t('MÊME PIÈCE')
                              : AppLocalizations.of(context).t('SIMILAIRE'),
                        ),
                      ],
                    ),
                  ],
                ),
              ),
              const SizedBox(width: 8),
              Column(
                crossAxisAlignment: CrossAxisAlignment.end,
                children: [
                  Text(
                    AppLocalizations.of(context).price(entry.price),
                    style: const TextStyle(
                      color: AppColors.textPrimary,
                      fontWeight: FontWeight.w900,
                      fontSize: 16,
                    ),
                  ),
                  Text(
                    '#$position',
                    style: const TextStyle(
                      color: AppColors.textSecondary,
                      fontSize: 11,
                    ),
                  ),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _MiniTag extends StatelessWidget {
  const _MiniTag(this.text);
  final String text;
  @override
  Widget build(BuildContext context) => DecoratedBox(
    decoration: BoxDecoration(
      color: AppColors.background,
      borderRadius: BorderRadius.circular(6),
    ),
    child: Padding(
      padding: const EdgeInsets.symmetric(horizontal: 5, vertical: 3),
      child: Text(
        text,
        style: const TextStyle(
          fontSize: 8,
          fontWeight: FontWeight.w800,
          color: AppColors.textSecondary,
        ),
      ),
    ),
  );
}

class _LadderMessage extends StatelessWidget {
  const _LadderMessage({required this.icon, required this.title, this.action});
  final IconData icon;
  final String title;
  final Widget? action;
  @override
  Widget build(BuildContext context) => Padding(
    padding: const EdgeInsets.symmetric(vertical: 36),
    child: Column(
      children: [
        Icon(icon, size: 44, color: AppColors.textSecondary),
        const SizedBox(height: 12),
        Text(
          title,
          textAlign: TextAlign.center,
          style: const TextStyle(fontWeight: FontWeight.w800),
        ),
        if (action != null) action!,
      ],
    ),
  );
}
