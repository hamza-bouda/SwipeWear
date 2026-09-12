import '../../../core/network/api_client.dart';
import '../../../core/storage/session_store.dart';
import '../../auth/data/session.dart';
import '../../feed/data/feed_repository.dart';

class DropRepository {
  DropRepository(this._api, this._store);

  final ApiClient _api;
  final SessionStore _store;

  Future<List<FeedItem>> get(Session session) async {
    try {
      final json = await _api.getJson('/drop', token: session.accessToken);
      await _store.writeCachedJson('drop', session.userId, json);
      return _items(json);
    } catch (error) {
      if (error is ApiException && error.statusCode < 500) rethrow;
      final cached = await _store.readCachedJson('drop', session.userId);
      if (cached != null) return _items(cached);
      rethrow;
    }
  }

  List<FeedItem> _items(Map<String, dynamic> json) {
    final raw = json['items'];
    return raw is List
        ? raw.whereType<Map<String, dynamic>>().map(FeedItem.fromJson).toList()
        : const [];
  }

  Future<void> markOpened(Session session, String productId) async {
    await _api.postJson('/events', {
      'product_id': productId,
      'event_type': 'open',
      'payload': {'surface': 'drop'},
    }, token: session.accessToken);
  }
}
