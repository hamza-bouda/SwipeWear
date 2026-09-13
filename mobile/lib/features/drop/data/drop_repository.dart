import '../../../core/network/api_client.dart';
import '../../../core/storage/session_store.dart';
import '../../auth/data/session.dart';
import '../../feed/data/feed_repository.dart';

class DropSnapshot {
  const DropSnapshot({required this.items, this.isOffline = false});

  final List<FeedItem> items;
  final bool isOffline;
}

class DropRepository {
  DropRepository(this._api, this._store);

  final ApiClient _api;
  final SessionStore _store;

  Future<DropSnapshot> get(Session session) async {
    try {
      final json = await _api.getJson('/drop', token: session.accessToken);
      await _store.writeCachedJson('drop', session.userId, json);
      return DropSnapshot(items: _items(json));
    } catch (error) {
      if (error is ApiException && error.statusCode < 500) rethrow;
      final cached = await _store.readCachedJson('drop', session.userId);
      if (cached != null) {
        return DropSnapshot(items: _items(cached), isOffline: true);
      }
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
