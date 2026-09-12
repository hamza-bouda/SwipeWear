import '../../../core/network/api_client.dart';
import '../../../core/storage/session_store.dart';
import '../../auth/data/session.dart';
import 'product.dart';

class FeedItem {
  const FeedItem({required this.product, this.explanation});

  final Product product;
  final String? explanation;

  factory FeedItem.fromJson(Map<String, dynamic> json) {
    final explanation = json['explanation'];
    return FeedItem(
      product: Product.fromJson(json['product'] as Map<String, dynamic>),
      explanation:
          explanation is Map<String, dynamic>
              ? explanation['sentence'] as String?
              : null,
    );
  }
}

class FeedResponse {
  const FeedResponse({
    required this.items,
    this.nextCursor,
    this.isOffline = false,
  });

  final List<FeedItem> items;
  final String? nextCursor;
  final bool isOffline;

  factory FeedResponse.fromJson(
    Map<String, dynamic> json, {
    bool isOffline = false,
  }) {
    final rawItems = json['items'];
    return FeedResponse(
      items:
          rawItems is List
              ? rawItems
                  .whereType<Map<String, dynamic>>()
                  .map(FeedItem.fromJson)
                  .toList(growable: false)
              : const [],
      nextCursor: json['next_cursor'] as String?,
      isOffline: isOffline,
    );
  }
}

class FeedRepository {
  FeedRepository(this._api, this._store);

  final ApiClient _api;
  final SessionStore _store;

  Future<FeedResponse> fetch(Session session) async {
    try {
      final json = await _api.getJson(
        '/feed',
        token: session.accessToken,
        queryParameters: const {'n_results': '30'},
      );
      await _store.writeCachedJson('feed', session.userId, json);
      return FeedResponse.fromJson(json);
    } catch (error) {
      if (error is ApiException && error.statusCode < 500) rethrow;
      final cached = await _store.readCachedJson('feed', session.userId);
      if (cached != null) return FeedResponse.fromJson(cached, isOffline: true);
      rethrow;
    }
  }

  Future<void> postEvent(
    Session session,
    String productId,
    String eventType,
  ) async {
    await _api.postJson('/events', {
      'product_id': productId,
      'event_type': eventType,
      'payload': <String, dynamic>{},
    }, token: session.accessToken);
  }
}
