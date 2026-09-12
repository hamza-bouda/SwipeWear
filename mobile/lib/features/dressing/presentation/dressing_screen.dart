import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/theme/app_theme.dart';
import '../../../core/localization/app_localizations.dart';
import '../../auth/providers.dart';
import '../../feed/presentation/product_detail_screen.dart';
import '../../shared/widgets/product_tile.dart';
import '../providers.dart';

class DressingScreen extends ConsumerStatefulWidget {
  const DressingScreen({super.key});

  @override
  ConsumerState<DressingScreen> createState() => _DressingScreenState();
}

class _DressingScreenState extends ConsumerState<DressingScreen> {
  String _category = 'Tout';
  String _sort = 'Récent';
  String _availability = 'Tout';

  bool _matches(String category, String value) {
    if (value == 'Tout') return true;
    final text = category.toLowerCase();
    if (value == 'Hauts') {
      return ['top', 'shirt', 'jacket', 'coat', 'sweater'].any(text.contains);
    }
    if (value == 'Bas') {
      return ['pant', 'jean', 'short', 'skirt'].any(text.contains);
    }
    if (value == 'Chaussures') {
      return ['shoe', 'sneaker', 'boot'].any(text.contains);
    }
    return ['bag', 'hat', 'watch', 'accessor'].any(text.contains);
  }

  @override
  Widget build(BuildContext context) {
    final l = AppLocalizations.of(context);
    final saves = ref.watch(savesProvider);
    return Scaffold(
      backgroundColor: Colors.transparent,
      body: SafeArea(
        child: saves.when(
          loading:
              () => const Center(
                child: CircularProgressIndicator(color: AppColors.accent),
              ),
          error:
              (_, __) => Center(
                child: Padding(
                  padding: const EdgeInsets.all(24),
                  child: Column(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      const Icon(Icons.cloud_off_outlined, size: 44),
                      const SizedBox(height: 12),
                      Text(
                        l.t('Dressing indisponible'),
                        style: const TextStyle(fontWeight: FontWeight.w800),
                      ),
                      const SizedBox(height: 8),
                      TextButton(
                        onPressed: () => ref.invalidate(savesProvider),
                        child: Text(l.t('Réessayer')),
                      ),
                    ],
                  ),
                ),
              ),
          data: (products) {
            final filtered =
                products
                    .where(
                      (item) =>
                          _matches(item.category, _category) &&
                          _matchesAvailability(item.available),
                    )
                    .toList();
            if (_sort == 'Prix croissant') {
              filtered.sort((a, b) => a.price.compareTo(b.price));
            }
            if (_sort == 'Prix décroissant') {
              filtered.sort((a, b) => b.price.compareTo(a.price));
            }
            return RefreshIndicator(
              onRefresh: () async {
                ref.invalidate(savesProvider);
                await ref.read(savesProvider.future);
              },
              child: CustomScrollView(
                slivers: [
                  SliverToBoxAdapter(
                    child: SectionHeader(
                      eyebrow: l.t('Ta sélection'),
                      title: l.t('Mon dressing'),
                    ),
                  ),
                  SliverToBoxAdapter(child: _Summary(products: products)),
                  SliverToBoxAdapter(
                    child: SizedBox(
                      height: 48,
                      child: ListView.separated(
                        padding: const EdgeInsets.symmetric(horizontal: 24),
                        scrollDirection: Axis.horizontal,
                        itemCount: _categories.length,
                        separatorBuilder: (_, __) => const SizedBox(width: 8),
                        itemBuilder: (_, index) {
                          final item = _categories[index];
                          return ChoiceChip(
                            label: Text(l.t(item)),
                            selected: item == _category,
                            onSelected: (_) => setState(() => _category = item),
                          );
                        },
                      ),
                    ),
                  ),
                  SliverToBoxAdapter(
                    child: SizedBox(
                      height: 44,
                      child: ListView.separated(
                        padding: const EdgeInsets.symmetric(horizontal: 24),
                        scrollDirection: Axis.horizontal,
                        itemCount: _availabilityFilters.length,
                        separatorBuilder: (_, __) => const SizedBox(width: 8),
                        itemBuilder: (_, index) {
                          final item = _availabilityFilters[index];
                          return ChoiceChip(
                            label: Text(l.t(item)),
                            selected: item == _availability,
                            onSelected:
                                (_) => setState(() => _availability = item),
                          );
                        },
                      ),
                    ),
                  ),
                  SliverToBoxAdapter(
                    child: Padding(
                      padding: const EdgeInsets.fromLTRB(24, 10, 24, 12),
                      child: DropdownButtonFormField<String>(
                        value: _sort,
                        decoration: InputDecoration(labelText: l.t('Trier')),
                        items: [
                          DropdownMenuItem(
                            value: 'Récent',
                            child: Text(l.t('Récent')),
                          ),
                          DropdownMenuItem(
                            value: 'Prix croissant',
                            child: Text(l.t('Prix croissant')),
                          ),
                          DropdownMenuItem(
                            value: 'Prix décroissant',
                            child: Text(l.t('Prix décroissant')),
                          ),
                        ],
                        onChanged: (value) {
                          if (value != null) setState(() => _sort = value);
                        },
                      ),
                    ),
                  ),
                  if (filtered.isEmpty)
                    const SliverFillRemaining(
                      hasScrollBody: false,
                      child: _EmptyDressing(),
                    )
                  else
                    SliverPadding(
                      padding: const EdgeInsets.fromLTRB(20, 0, 20, 120),
                      sliver: SliverGrid(
                        delegate: SliverChildBuilderDelegate((context, index) {
                          final product = filtered[index];
                          return ProductTile(
                            product: product,
                            onTap:
                                () => Navigator.push(
                                  context,
                                  MaterialPageRoute(
                                    builder:
                                        (_) => ProductDetailScreen(
                                          product: product,
                                        ),
                                  ),
                                ),
                            onRemove: () async {
                              final session = await ref.read(
                                sessionProvider.future,
                              );
                              await ref
                                  .read(savesRepositoryProvider)
                                  .toggle(session, product, saved: false);
                              ref.invalidate(savesProvider);
                            },
                          );
                        }, childCount: filtered.length),
                        gridDelegate:
                            const SliverGridDelegateWithFixedCrossAxisCount(
                              crossAxisCount: 2,
                              crossAxisSpacing: 12,
                              mainAxisSpacing: 12,
                              // ProductTile has a variable-height metadata
                              // block (title, price, size and listing age).
                              // Leave enough vertical room on compact phones
                              // instead of letting the grid force a 22 px
                              // RenderFlex overflow.
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

  bool _matchesAvailability(bool available) => switch (_availability) {
    'Disponibles' => available,
    'Vendus' => !available,
    _ => true,
  };
}

const _categories = ['Tout', 'Hauts', 'Bas', 'Chaussures', 'Accessoires'];
const _availabilityFilters = ['Tout', 'Disponibles', 'Vendus'];

class _Summary extends StatelessWidget {
  const _Summary({required this.products});
  final List products;

  @override
  Widget build(BuildContext context) {
    final l = AppLocalizations.of(context);
    return Padding(
      padding: const EdgeInsets.fromLTRB(24, 0, 24, 18),
      child: Container(
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(
          gradient: AppGradients.mint,
          borderRadius: BorderRadius.circular(22),
        ),
        child: Row(
          children: [
            Container(
              width: 44,
              height: 44,
              decoration: BoxDecoration(
                color: AppColors.accent,
                borderRadius: BorderRadius.circular(14),
              ),
              child: const Icon(Icons.checkroom, color: AppColors.textPrimary),
            ),
            const SizedBox(width: 12),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    l.savedPieces(products.length),
                    style: const TextStyle(
                      color: AppColors.textPrimary,
                      fontWeight: FontWeight.w800,
                    ),
                  ),
                  const SizedBox(height: 3),
                  Text(
                    l.t('Tes trouvailles, au même endroit.'),
                    style: const TextStyle(
                      color: AppColors.textPrimary,
                      fontSize: 12,
                    ),
                  ),
                ],
              ),
            ),
            Text(
              l.price(
                products.fold<double>(0, (sum, item) => sum + item.price),
              ),
              style: const TextStyle(
                color: AppColors.textPrimary,
                fontWeight: FontWeight.w900,
                fontSize: 20,
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _EmptyDressing extends StatelessWidget {
  const _EmptyDressing();

  @override
  Widget build(BuildContext context) => Center(
    child: Padding(
      padding: const EdgeInsets.all(28),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          const Icon(
            Icons.checkroom_outlined,
            size: 48,
            color: AppColors.textSecondary,
          ),
          const SizedBox(height: 14),
          Text(
            AppLocalizations.of(context).t('Dressing vide'),
            style: Theme.of(
              context,
            ).textTheme.titleLarge?.copyWith(fontWeight: FontWeight.w900),
          ),
          const SizedBox(height: 8),
          Text(
            AppLocalizations.of(
              context,
            ).t('Aime une pièce dans le feed pour la retrouver ici.'),
            textAlign: TextAlign.center,
            style: const TextStyle(color: AppColors.textSecondary),
          ),
        ],
      ),
    ),
  );
}
