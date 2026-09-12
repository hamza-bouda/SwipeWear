class Product {
  const Product({
    required this.id,
    required this.title,
    required this.brand,
    required this.price,
    required this.currency,
    required this.condition,
    required this.category,
    required this.size,
    required this.imageUrls,
    required this.source,
    this.available = true,
    this.affiliateUrl,
    this.enrichedAttrs = const {},
  });

  final String id;
  final String title;
  final String brand;
  final double price;
  final String currency;
  final String condition;
  final String category;
  final String? size;
  final List<String> imageUrls;
  final String source;
  final bool available;
  final String? affiliateUrl;
  final Map<String, String> enrichedAttrs;

  DateTime? get listedAt {
    final raw = enrichedAttrs['created_at'] ?? enrichedAttrs['indexed_at'];
    return raw == null ? null : DateTime.tryParse(raw);
  }

  String? get ageLabel {
    final listed = listedAt;
    if (listed == null) return null;
    final age = DateTime.now().toUtc().difference(listed.toUtc());
    if (age.isNegative || age.inMinutes < 1) return 'À l’instant';
    if (age.inHours < 24) return 'Il y a ${age.inHours} h';
    if (age.inDays < 7) return 'Il y a ${age.inDays} j';
    if (age.inDays < 30) return 'Il y a ${(age.inDays / 7).floor()} sem.';
    return 'Il y a ${(age.inDays / 30).floor()} mois';
  }

  factory Product.fromJson(Map<String, dynamic> json) {
    final rawImages = json['image_urls'];
    final rawAttrs = json['enriched_attrs'];
    final enrichedAttrs = <String, String>{};
    if (rawAttrs is Map) {
      rawAttrs.forEach((key, value) {
        if (key is String && value != null) {
          enrichedAttrs[key] = value.toString();
        }
      });
    }
    final directCreatedAt = json['created_at'];
    if (directCreatedAt is String && directCreatedAt.isNotEmpty) {
      enrichedAttrs['created_at'] = directCreatedAt;
    }
    return Product(
      id: json['id'] as String,
      title: json['title'] as String? ?? 'Pièce sans titre',
      brand: json['brand'] as String? ?? '',
      price: (json['price'] as num?)?.toDouble() ?? 0,
      currency: json['currency'] as String? ?? 'EUR',
      condition: json['condition'] as String? ?? 'good',
      category: json['category'] as String? ?? '',
      size: json['size_raw'] as String? ?? json['size_eu'] as String?,
      imageUrls:
          rawImages is List
              ? rawImages.whereType<String>().toList(growable: false)
              : const [],
      source: json['source'] as String? ?? 'unknown',
      available: json['available'] as bool? ?? true,
      affiliateUrl: json['affiliate_url'] as String?,
      enrichedAttrs: enrichedAttrs,
    );
  }
}
