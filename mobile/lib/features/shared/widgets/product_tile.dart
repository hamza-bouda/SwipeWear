import 'package:flutter/material.dart';

import '../../../core/theme/app_theme.dart';
import '../../../core/localization/app_localizations.dart';
import '../../feed/data/product.dart';

class ProductTile extends StatelessWidget {
  const ProductTile({
    super.key,
    required this.product,
    this.onTap,
    this.onRemove,
  });

  final Product product;
  final VoidCallback? onTap;
  final VoidCallback? onRemove;

  @override
  Widget build(BuildContext context) {
    final l = AppLocalizations.of(context);
    final sold = !product.available;
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(20),
      child: Ink(
        decoration: BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.circular(20),
          border: Border.all(color: AppColors.border),
          boxShadow: const [
            BoxShadow(
              color: Color(0x0A000000),
              blurRadius: 10,
              offset: Offset(0, 4),
            ),
          ],
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            AspectRatio(
              aspectRatio: .83,
              child: Stack(
                fit: StackFit.expand,
                children: [
                  ClipRRect(
                    borderRadius: const BorderRadius.vertical(
                      top: Radius.circular(20),
                    ),
                    child:
                        product.imageUrls.isEmpty
                            ? const ColoredBox(color: AppColors.accentLight)
                            : Image.network(
                              product.imageUrls.first,
                              fit: BoxFit.cover,
                              errorBuilder:
                                  (_, __, ___) => const ColoredBox(
                                    color: AppColors.accentLight,
                                  ),
                            ),
                  ),
                  Positioned(
                    top: 10,
                    left: 10,
                    child: _Tag(text: _sourceLabel(product.source)),
                  ),
                  if (sold)
                    const Positioned.fill(
                      child: ColoredBox(
                        color: Color.fromRGBO(255, 255, 255, .62),
                      ),
                    ),
                  if (sold) Center(child: _Tag(text: l.t('VENDU'))),
                  if (onRemove != null)
                    Positioned(
                      top: 8,
                      right: 8,
                      child: IconButton.filledTonal(
                        onPressed: onRemove,
                        icon: const Icon(Icons.close, size: 16),
                        tooltip: l.t('Retirer du dressing'),
                      ),
                    ),
                ],
              ),
            ),
            Padding(
              padding: const EdgeInsets.fromLTRB(12, 10, 12, 12),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    product.brand.isEmpty ? product.source : product.brand,
                    style: const TextStyle(
                      fontSize: 11,
                      color: AppColors.textSecondary,
                      fontWeight: FontWeight.w700,
                    ),
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                  ),
                  const SizedBox(height: 3),
                  Text(
                    product.title,
                    style: const TextStyle(
                      fontWeight: FontWeight.w700,
                      height: 1.2,
                    ),
                    maxLines: 2,
                    overflow: TextOverflow.ellipsis,
                  ),
                  const SizedBox(height: 8),
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      Text(
                        '${l.price(product.price)} ${product.currency}',
                        style: const TextStyle(
                          color: AppColors.textPrimary,
                          fontWeight: FontWeight.w900,
                        ),
                      ),
                      if (product.size != null)
                        Text(
                          product.size!,
                          style: const TextStyle(
                            fontSize: 11,
                            color: AppColors.textSecondary,
                          ),
                        ),
                    ],
                  ),
                  if (product.ageLabel != null) ...[
                    const SizedBox(height: 4),
                    Text(
                      product.ageLabel!,
                      style: const TextStyle(
                        fontSize: 10,
                        color: AppColors.textSecondary,
                      ),
                    ),
                  ],
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _Tag extends StatelessWidget {
  const _Tag({required this.text});

  final String text;

  @override
  Widget build(BuildContext context) => DecoratedBox(
    decoration: BoxDecoration(
      color: Colors.black.withValues(alpha: .72),
      borderRadius: BorderRadius.circular(8),
    ),
    child: Padding(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
      child: Text(
        text,
        style: const TextStyle(
          color: Colors.white,
          fontSize: 9,
          fontWeight: FontWeight.w800,
          letterSpacing: .4,
        ),
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

class SectionHeader extends StatelessWidget {
  const SectionHeader({super.key, required this.eyebrow, required this.title});

  final String eyebrow;
  final String title;

  @override
  Widget build(BuildContext context) => Padding(
    padding: const EdgeInsets.fromLTRB(24, 20, 24, 14),
    child: Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          eyebrow.toUpperCase(),
          style: const TextStyle(
            color: AppColors.textSecondary,
            fontSize: 11,
            fontWeight: FontWeight.w900,
            letterSpacing: 1,
          ),
        ),
        const SizedBox(height: 4),
        Text(
          title,
          style: Theme.of(
            context,
          ).textTheme.headlineSmall?.copyWith(fontWeight: FontWeight.w900),
        ),
      ],
    ),
  );
}
