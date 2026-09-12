import '../../../core/network/api_client.dart';
import '../../auth/data/session.dart';

class LadderEntry {
  const LadderEntry({
    required this.productId,
    required this.title,
    required this.price,
    required this.source,
    required this.condition,
    required this.isNew,
    required this.confidence,
    required this.imageUrl,
    required this.url,
    required this.similarityScore,
  });

  final String productId;
  final String title;
  final double price;
  final String source;
  final String condition;
  final bool isNew;
  final String confidence;
  final String? imageUrl;
  final String? url;
  final double similarityScore;

  factory LadderEntry.fromJson(Map<String, dynamic> json) => LadderEntry(
    productId: json['product_id'] as String? ?? '',
    title: json['title'] as String? ?? 'Offre similaire',
    price: (json['price_eur'] as num?)?.toDouble() ?? 0,
    source: json['source'] as String? ?? 'source',
    condition: json['condition'] as String? ?? 'good',
    isNew: json['is_new'] as bool? ?? false,
    confidence: json['confidence'] as String? ?? 'similar',
    imageUrl: json['image_url'] as String?,
    url: (json['affiliate_url'] ?? json['url']) as String?,
    similarityScore: (json['similarity_score'] as num?)?.toDouble() ?? 0,
  );
}

class PriceLadder {
  const PriceLadder({required this.entries, this.savingsPct});

  final List<LadderEntry> entries;
  final double? savingsPct;

  factory PriceLadder.fromJson(Map<String, dynamic> json) {
    final raw = json['entries'];
    return PriceLadder(
      entries:
          raw is List
              ? raw
                  .whereType<Map<String, dynamic>>()
                  .map(LadderEntry.fromJson)
                  .toList()
              : const [],
      savingsPct: (json['savings_pct'] as num?)?.toDouble(),
    );
  }
}

class LadderRepository {
  LadderRepository(this._api);

  final ApiClient _api;

  Future<PriceLadder> get(Session session, String productId) async =>
      PriceLadder.fromJson(
        await _api.getJson(
          '/ladder/${Uri.encodeComponent(productId)}',
          token: session.accessToken,
        ),
      );

  Future<void> outboundClick(
    Session session,
    LadderEntry entry,
    int position,
  ) async {
    await _api.postJson('/analytics/events', {
      'name': 'outbound_click',
      'properties': {
        'product_id': entry.productId,
        'source': entry.source,
        'price': entry.price,
        'position': position,
      },
      'occurred_at': DateTime.now().toUtc().toIso8601String(),
    }, token: session.accessToken);
  }

  Future<void> recordAnalytics(
    Session session,
    String name,
    Map<String, dynamic> properties,
  ) async {
    await _api.postJson('/analytics/events', {
      'name': name,
      'properties': properties,
      'occurred_at': DateTime.now().toUtc().toIso8601String(),
    }, token: session.accessToken);
  }
}
