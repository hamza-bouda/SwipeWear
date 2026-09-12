import '../../../core/network/api_client.dart';
import '../../auth/data/session.dart';

class NotificationRepository {
  NotificationRepository(this._api);
  final ApiClient _api;

  Future<String> getPreference(Session session) async =>
      (await _api.getJson(
            '/notifications/preferences',
            token: session.accessToken,
          ))['preference']
          as String? ??
      'instant';

  Future<void> setPreference(Session session, String preference) async {
    await _api.patchJson('/notifications/preferences', {
      'preference': preference,
    }, token: session.accessToken);
  }
}
