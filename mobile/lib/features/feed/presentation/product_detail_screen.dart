import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:url_launcher/url_launcher.dart';

import '../../../core/theme/app_theme.dart';
import '../../../core/localization/app_localizations.dart';
import '../../../core/analytics/providers.dart';
import '../../../core/network/api_client.dart';
import '../../alerts/providers.dart';
import '../../dressing/providers.dart';
import '../../auth/providers.dart';
import '../../billing/presentation/paywall_screen.dart';
import '../../profile/providers.dart';
import '../../ladder/presentation/price_ladder_screen.dart';
import '../../ladder/providers.dart';
import '../data/product.dart';

class ProductDetailScreen extends ConsumerStatefulWidget {
  const ProductDetailScreen({super.key, required this.product});

  final Product product;

  @override
  ConsumerState<ProductDetailScreen> createState() =>
      _ProductDetailScreenState();
}

class _ProductDetailScreenState extends ConsumerState<ProductDetailScreen> {
  int _imageIndex = 0;

  Future<void> _toggleSave() async {
    final l = AppLocalizations.of(context);
    final session = await ref.read(sessionProvider.future);
    final saved =
        ref
            .read(savesProvider)
            .valueOrNull
            ?.any((item) => item.id == widget.product.id) ??
        false;
    await ref
        .read(savesRepositoryProvider)
        .toggle(session, widget.product, saved: !saved);
    ref.invalidate(savesProvider);
    if (mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(
            saved ? l.t('Retirée du dressing') : l.t('Ajoutée au dressing'),
          ),
        ),
      );
    }
  }

  Future<void> _buy() async {
    final l = AppLocalizations.of(context);
    final url = widget.product.affiliateUrl;
    if (url == null || url.isEmpty) return;
    try {
      final session = await ref.read(sessionProvider.future);
      unawaited(
        ref
            .read(analyticsServiceProvider)
            .track(
              session,
              'outbound_click',
              properties: {
                'product_id': widget.product.id,
                'source': widget.product.source,
                'price': widget.product.price,
                'position': 0,
                'surface': 'detail',
              },
            ),
      );
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

  Future<void> _createAlert() async {
    final l = AppLocalizations.of(context);
    try {
      final session = await ref.read(sessionProvider.future);
      final profile = ref.read(profileProvider).valueOrNull;
      await ref
          .read(alertsRepositoryProvider)
          .create(
            session,
            label: widget.product.title,
            type: 'specific_item',
            referenceProductId: widget.product.id,
            maxPrice: widget.product.price,
            sizes: profile?.sizes ?? const [],
          );
      ref.invalidate(alertsProvider);
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(l.t('Alerte créée pour la prochaine disponibilité.')),
          ),
        );
      }
    } on ApiException catch (error) {
      if (!mounted) return;
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
    } catch (_) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(l.t('Impossible de créer l’alerte pour le moment.')),
          ),
        );
      }
    }
  }

  Future<void> _shareProduct() async {
    final l = AppLocalizations.of(context);
    try {
      final ladder = await ref.read(ladderProvider(widget.product.id).future);
      if (!mounted) return;
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
                      .read(analyticsServiceProvider)
                      .track(
                        session,
                        'share_card_generated',
                        properties: {
                          'product_id': widget.product.id,
                          'savings_pct': ladder.savingsPct,
                          'ladder_count': ladder.entries.length,
                        },
                      );
                } catch (_) {}
              },
            ),
      );
    } catch (_) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text(l.t('Impossible de préparer le partage.'))),
        );
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final l = AppLocalizations.of(context);
    final product = widget.product;
    final saved =
        ref
            .watch(savesProvider)
            .valueOrNull
            ?.any((item) => item.id == product.id) ??
        false;
    return Scaffold(
      // This route is pushed above AppShell, so it must provide its own
      // surface instead of inheriting the transparent scaffold background.
      backgroundColor: AppColors.background,
      body: DecoratedBox(
        decoration: const BoxDecoration(gradient: AppGradients.background),
        child: CustomScrollView(
          slivers: [
            SliverAppBar(
              expandedHeight: MediaQuery.sizeOf(context).width * 1.08,
              pinned: true,
              backgroundColor: AppColors.background,
              foregroundColor: AppColors.textPrimary,
              actions: [
                IconButton(
                  onPressed: _toggleSave,
                  icon: Icon(
                    saved ? Icons.favorite : Icons.favorite_border,
                    color: saved ? AppColors.error : null,
                  ),
                  tooltip: l.t('Dressing'),
                ),
                IconButton(
                  onPressed: _shareProduct,
                  icon: const Icon(Icons.ios_share_outlined),
                  tooltip: l.t('Partager'),
                ),
              ],
              flexibleSpace: FlexibleSpaceBar(
                background:
                    product.imageUrls.isEmpty
                        ? const ColoredBox(
                          color: AppColors.accentLight,
                          child: Center(
                            child: Icon(Icons.checkroom_rounded, size: 72),
                          ),
                        )
                        : PageView.builder(
                          itemCount: product.imageUrls.length,
                          onPageChanged:
                              (index) => setState(() => _imageIndex = index),
                          itemBuilder:
                              (_, index) => Image.network(
                                product.imageUrls[index],
                                fit: BoxFit.cover,
                                excludeFromSemantics: true,
                                errorBuilder:
                                    (_, __, ___) => const ColoredBox(
                                      color: AppColors.accentLight,
                                      child: Center(
                                        child: Icon(
                                          Icons.checkroom_rounded,
                                          size: 72,
                                        ),
                                      ),
                                    ),
                              ),
                        ),
              ),
            ),
            SliverToBoxAdapter(
              child: Padding(
                padding: const EdgeInsets.fromLTRB(24, 22, 24, 120),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Wrap(
                      spacing: 8,
                      runSpacing: 8,
                      children: [
                        _Badge(product.condition),
                        if (product.size != null)
                          _Badge(
                            l.isEnglish
                                ? 'Size ${product.size}'
                                : 'Taille ${product.size}',
                          ),
                        _Badge(_sourceLabel(product.source)),
                        if (product.ageLabel != null) _Badge(product.ageLabel!),
                      ],
                    ),
                    if (!product.available)
                      Padding(
                        padding: const EdgeInsets.only(top: 18),
                        child: Container(
                          padding: const EdgeInsets.all(14),
                          decoration: BoxDecoration(
                            color: AppColors.accentLight,
                            borderRadius: BorderRadius.circular(16),
                          ),
                          child: Row(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              const Icon(Icons.info_outline),
                              const SizedBox(width: 10),
                              Expanded(
                                child: Text(
                                  l.t(
                                    'Vendu — crée une alerte pour être prévenu·e de la prochaine pièce.',
                                  ),
                                  style: TextStyle(
                                    fontWeight: FontWeight.w700,
                                    height: 1.35,
                                  ),
                                ),
                              ),
                            ],
                          ),
                        ),
                      ),
                    const SizedBox(height: 18),
                    Text(
                      product.brand.isEmpty
                          ? l.t('Sélection SwipeWear')
                          : product.brand,
                      style: const TextStyle(
                        color: AppColors.textSecondary,
                        fontWeight: FontWeight.w700,
                      ),
                    ),
                    const SizedBox(height: 6),
                    Text(
                      product.title,
                      style: Theme.of(context).textTheme.headlineSmall
                          ?.copyWith(fontWeight: FontWeight.w900),
                    ),
                    const SizedBox(height: 12),
                    Text(
                      '${l.price(product.price)} ${product.currency}',
                      style: const TextStyle(
                        fontSize: 30,
                        fontWeight: FontWeight.w900,
                        color: AppColors.textPrimary,
                      ),
                    ),
                    const SizedBox(height: 8),
                    Text(
                      product.category,
                      style: const TextStyle(color: AppColors.textSecondary),
                    ),
                    if (product.imageUrls.length > 1)
                      Padding(
                        padding: const EdgeInsets.only(top: 12),
                        child: Text(
                          '${_imageIndex + 1} / ${product.imageUrls.length}',
                          style: const TextStyle(
                            color: AppColors.textSecondary,
                            fontSize: 12,
                          ),
                        ),
                      ),
                    const SizedBox(height: 24),
                    Text(
                      l.t('Pourquoi cette pièce ?'),
                      style: TextStyle(
                        fontWeight: FontWeight.w900,
                        fontSize: 17,
                      ),
                    ),
                    const SizedBox(height: 6),
                    Text(
                      l.t(
                        'Chaque swipe apprend tes préférences et rend ton prochain feed plus précis.',
                      ),
                      style: TextStyle(
                        color: AppColors.textSecondary,
                        height: 1.4,
                      ),
                    ),
                    const SizedBox(height: 24),
                    FilledButton.icon(
                      onPressed:
                          () => Navigator.push(
                            context,
                            MaterialPageRoute(
                              builder:
                                  (_) => PriceLadderScreen(product: product),
                            ),
                          ),
                      icon: const Icon(Icons.stacked_bar_chart),
                      label: Text(l.t('Voir l’échelle de prix')),
                    ),
                    const SizedBox(height: 10),
                    OutlinedButton.icon(
                      onPressed: _createAlert,
                      icon: const Icon(Icons.notifications_none),
                      label: Text(
                        product.available
                            ? l.t('Créer une alerte sur cette pièce')
                            : l.t('Créer une alerte pour la prochaine'),
                      ),
                    ),
                    const SizedBox(height: 10),
                    OutlinedButton(
                      onPressed:
                          product.affiliateUrl == null || !product.available
                              ? null
                              : _buy,
                      child: Text(l.t('Voir l’annonce originale')),
                    ),
                    if (product.affiliateUrl != null)
                      Padding(
                        padding: EdgeInsets.only(top: 8),
                        child: Center(
                          child: Text(
                            l.t('Lien partenaire'),
                            style: TextStyle(
                              color: AppColors.textSecondary,
                              fontSize: 11,
                            ),
                          ),
                        ),
                      ),
                  ],
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _Badge extends StatelessWidget {
  const _Badge(this.text);

  final String text;

  @override
  Widget build(BuildContext context) => DecoratedBox(
    decoration: BoxDecoration(
      color: AppColors.accentLight,
      borderRadius: BorderRadius.circular(8),
    ),
    child: Padding(
      padding: const EdgeInsets.symmetric(horizontal: 9, vertical: 5),
      child: Text(
        text.replaceAll('_', ' ').toUpperCase(),
        style: const TextStyle(fontSize: 10, fontWeight: FontWeight.w800),
      ),
    ),
  );
}

String _sourceLabel(String value) => switch (value.toLowerCase()) {
  'ebay' => 'eBay',
  'etsy' => 'Etsy',
  'vc' || 'vestiaire_collective' => 'Vestiaire',
  'awin' || 'cj' => 'Neuf',
  _ => value.toUpperCase(),
};
