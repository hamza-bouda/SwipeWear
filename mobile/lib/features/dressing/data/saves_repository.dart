import '../../../core/network/api_client.dart';
import '../../../core/storage/session_store.dart';
import '../../auth/data/session.dart';
import '../../feed/data/product.dart';

class SavesRepository {
  SavesRepository(this._api, this._store);

  final ApiClient _api;
  final SessionStore _store;

  Future<List<Product>> get(Session session) async {
    try {
      final json = await _api.getJson('/saves', token: session.accessToken);
      await _store.writeCachedJson('saves', session.userId, json);
      return _products(json);
    } catch (error) {
      if (error is ApiException && error.statusCode < 500) rethrow;
      final cached = await _store.readCachedJson('saves', session.userId);
      if (cached != null) return _products(cached);
      rethrow;
    }
  }

  List<Product> _products(Map<String, dynamic> json) {
    final raw = json['products'];
    return raw is List
        ? raw.whereType<Map<String, dynamic>>().map(Product.fromJson).toList()
        : const [];
  }

  Future<void> toggle(
    Session session,
    Product product, {
    required bool saved,
  }) async {
    await _api.postJson('/events', {
      'product_id': product.id,
      'event_type': saved ? 'save' : 'unsave',
      'payload': <String, dynamic>{},
    }, token: session.accessToken);
  }
}
