import '../network/api_client.dart';
import '../../features/auth/data/session.dart';

class AnalyticsService {
  AnalyticsService(this._api);

  final ApiClient _api;

  Future<void> track(
    Session session,
    String name, {
    Map<String, dynamic> properties = const {},
  }) async {
    try {
      await _api.postJson('/analytics/events', {
        'name': name,
        'properties': properties,
        'occurred_at': DateTime.now().toUtc().toIso8601String(),
      }, token: session.accessToken);
    } catch (_) {
      // Product analytics must never block a swipe, a purchase or navigation.
    }
  }
}
