import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/analytics/providers.dart';
import '../../../core/localization/app_localizations.dart';
import '../../../core/theme/app_theme.dart';
import '../../auth/providers.dart';
import '../../billing/presentation/paywall_screen.dart';
import '../../feed/presentation/product_detail_screen.dart';
import '../../shared/widgets/product_tile.dart';
import '../providers.dart';

class DropScreen extends ConsumerStatefulWidget {
  const DropScreen({super.key});

  @override
  ConsumerState<DropScreen> createState() => _DropScreenState();
}

class _DropScreenState extends ConsumerState<DropScreen> {
  final _seen = <String>{};
  bool _completionTracked = false;
  String _category = 'Tout';

  Future<void> _track(String name, Map<String, dynamic> properties) async {
    try {
      final session = await ref.read(sessionProvider.future);
      await ref
          .read(analyticsServiceProvider)
          .track(session, name, properties: properties);
    } catch (_) {}
  }

  Future<void> _open(String id) async {
    try {
      final session = await ref.read(sessionProvider.future);
      await ref.read(dropRepositoryProvider).markOpened(session, id);
      unawaited(_track('drop_opened', {'product_id': id}));
    } catch (_) {
      // Opening the product remains possible when the event endpoint is down.
    }
    if (mounted) setState(() => _seen.add(id));
  }

  @override
  Widget build(BuildContext context) {
    final l = AppLocalizations.of(context);
    final drop = ref.watch(dropProvider);
    return Scaffold(
      backgroundColor: Colors.transparent,
      body: SafeArea(
        child: drop.when(
          loading:
              () => const Center(
                child: CircularProgressIndicator(color: AppColors.accent),
              ),
          error:
              (_, __) => _DropEmpty(
                onReload: () => ref.invalidate(dropProvider),
                title: l.t('Le Drop arrive bientôt'),
                subtitle: l.t(
                  'Actualise quand les nouvelles pépites sont disponibles.',
                ),
              ),
          data: (items) {
            final unseen =
                items
                    .where((item) => !_seen.contains(item.product.id))
                    .toList();
            final visible =
                unseen
                    .where((item) => _matchesCategory(item.product.category))
                    .toList();
            if (unseen.isEmpty && !_completionTracked) {
              _completionTracked = true;
              unawaited(_track('drop_completed', {'item_count': items.length}));
            }
            final emptyBecauseOfFilter = unseen.isNotEmpty && visible.isEmpty;
            return RefreshIndicator(
              onRefresh: () async {
                ref.invalidate(dropProvider);
                await ref.read(dropProvider.future);
              },
              child:
                  visible.isEmpty
                      ? _DropEmpty(
                        onReload:
                            emptyBecauseOfFilter
                                ? () => setState(() => _category = 'Tout')
                                : () => ref.invalidate(dropProvider),
                        reloadLabel:
                            emptyBecauseOfFilter
                                ? l.t('Voir toutes les pépites')
                                : l.t('Actualiser'),
                        title:
                            emptyBecauseOfFilter
                                ? l.t('Rien dans cette catégorie')
                                : l.t('Drop terminé pour aujourd’hui'),
                        subtitle:
                            emptyBecauseOfFilter
                                ? l.t(
                                  'Change de catégorie pour retrouver les autres trouvailles du jour.',
                                )
                                : l.t(
                                  'Reviens demain à 19 h ou crée une alerte pour une chasse continue.',
                                ),
                        onGold:
                            emptyBecauseOfFilter
                                ? null
                                : () => Navigator.push(
                                  context,
                                  MaterialPageRoute(
                                    builder:
                                        (_) => const PaywallScreen(
                                          trigger: 'drop_completed',
                                        ),
                                  ),
                                ),
                      )
                      : CustomScrollView(
                        slivers: [
                          SliverToBoxAdapter(
                            child: SectionHeader(
                              eyebrow: l.t('Chaque jour à 19 h'),
                              title: l.t('Le Drop du jour'),
                            ),
                          ),
                          SliverToBoxAdapter(
                            child: Padding(
                              padding: const EdgeInsets.fromLTRB(24, 0, 24, 14),
                              child: Container(
                                padding: const EdgeInsets.symmetric(
                                  horizontal: 14,
                                  vertical: 10,
                                ),
                                decoration: BoxDecoration(
                                  gradient: AppGradients.mint,
                                  borderRadius: BorderRadius.circular(14),
                                ),
                                child: Row(
                                  mainAxisSize: MainAxisSize.min,
                                  children: [
                                    const Icon(Icons.schedule, size: 17),
                                    const SizedBox(width: 8),
                                    Text(
                                      l.t('Nouvelles pépites demain à 19 h'),
                                      style: const TextStyle(
                                        fontWeight: FontWeight.w800,
                                      ),
                                    ),
                                  ],
                                ),
                              ),
                            ),
                          ),
                          SliverToBoxAdapter(
                            child: SizedBox(
                              height: 44,
                              child: ListView.separated(
                                padding: const EdgeInsets.symmetric(
                                  horizontal: 24,
                                ),
                                scrollDirection: Axis.horizontal,
                                itemCount: _categories.length,
                                separatorBuilder:
                                    (_, __) => const SizedBox(width: 8),
                                itemBuilder: (_, index) {
                                  final category = _categories[index];
                                  return ChoiceChip(
                                    label: Text(l.t(category)),
                                    selected: category == _category,
                                    onSelected:
                                        (_) => setState(
                                          () => _category = category,
                                        ),
                                  );
                                },
                              ),
                            ),
                          ),
                          SliverToBoxAdapter(
                            child: Padding(
                              padding: const EdgeInsets.fromLTRB(24, 0, 24, 18),
                              child: Row(
                                children: [
                                  const Icon(
                                    Icons.bolt,
                                    color: AppColors.success,
                                    size: 18,
                                  ),
                                  const SizedBox(width: 6),
                                  Text(
                                    l.discoveries(visible.length),
                                    style: const TextStyle(
                                      color: AppColors.textSecondary,
                                      fontWeight: FontWeight.w700,
                                    ),
                                  ),
                                ],
                              ),
                            ),
                          ),
                          SliverPadding(
                            padding: const EdgeInsets.fromLTRB(20, 0, 20, 120),
                            sliver: SliverGrid(
                              delegate: SliverChildBuilderDelegate((
                                context,
                                index,
                              ) {
                                final item = visible[index];
                                return ProductTile(
                                  product: item.product,
                                  onTap: () async {
                                    await _open(item.product.id);
                                    if (!context.mounted) return;
                                    await Navigator.push(
                                      context,
                                      MaterialPageRoute(
                                        builder:
                                            (_) => ProductDetailScreen(
                                              product: item.product,
                                            ),
                                      ),
                                    );
                                  },
                                );
                              }, childCount: visible.length),
                              gridDelegate:
                                  const SliverGridDelegateWithFixedCrossAxisCount(
                                    crossAxisCount: 2,
                                    crossAxisSpacing: 12,
                                    mainAxisSpacing: 12,
                                    // Keep the tile's metadata readable on
                                    // compact Android screens; the title and
                                    // listing-age line are not a fixed height.
                                    childAspectRatio: .55,
                                  ),
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

  bool _matchesCategory(String value) {
    if (_category == 'Tout') return true;
    final text = value.toLowerCase();
    return switch (_category) {
      'Vestes' => ['jacket', 'coat', 'veste', 'manteau'].any(text.contains),
      'Sneakers' => ['shoe', 'sneaker', 'basket'].any(text.contains),
      'Sacs' => ['bag', 'sac'].any(text.contains),
      'Pantalons' => ['pant', 'jean', 'trouser', 'pantalon'].any(text.contains),
      _ => true,
    };
  }
}

const _categories = ['Tout', 'Vestes', 'Sneakers', 'Sacs', 'Pantalons'];

class _DropEmpty extends StatelessWidget {
  const _DropEmpty({
    required this.onReload,
    required this.title,
    required this.subtitle,
    this.onGold,
    this.reloadLabel = 'Actualiser',
  });

  final VoidCallback onReload;
  final String title;
  final String subtitle;
  final VoidCallback? onGold;
  final String reloadLabel;

  @override
  Widget build(BuildContext context) => Center(
    child: Padding(
      padding: const EdgeInsets.all(30),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          Container(
            width: 72,
            height: 72,
            decoration: BoxDecoration(
              color: AppColors.accentLight,
              borderRadius: BorderRadius.circular(24),
            ),
            child: const Icon(Icons.bolt, size: 34),
          ),
          const SizedBox(height: 18),
          Text(
            title,
            textAlign: TextAlign.center,
            style: Theme.of(
              context,
            ).textTheme.titleLarge?.copyWith(fontWeight: FontWeight.w900),
          ),
          const SizedBox(height: 8),
          Text(
            subtitle,
            textAlign: TextAlign.center,
            style: const TextStyle(color: AppColors.textSecondary, height: 1.4),
          ),
          const SizedBox(height: 18),
          if (onGold != null) ...[
            FilledButton.icon(
              onPressed: onGold,
              icon: const Icon(Icons.workspace_premium_outlined),
              label: Text(AppLocalizations.of(context).t('Découvrir Gold')),
            ),
            const SizedBox(height: 8),
          ],
          OutlinedButton(onPressed: onReload, child: Text(reloadLabel)),
        ],
      ),
    ),
  );
}
