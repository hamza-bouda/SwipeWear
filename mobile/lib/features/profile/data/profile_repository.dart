import '../../../core/network/api_client.dart';
import '../../auth/data/session.dart';
import 'profile.dart';

class ProfileRepository {
  ProfileRepository(this._api);

  final ApiClient _api;

  Future<ProfileSnapshot> get(Session session) async =>
      ProfileSnapshot.fromJson(
        await _api.getJson('/profile', token: session.accessToken),
      );

  Future<ProfileSnapshot> patch(
    Session session, {
    List<String>? sizes,
    double? maxPrice,
    bool clearMaxPrice = false,
    String? gender,
  }) async {
    final constraints = <String, dynamic>{
      if (sizes != null) 'sizes': sizes,
      if (maxPrice != null) 'max_price_eur': maxPrice,
      if (clearMaxPrice) 'max_price_eur': null,
      if (gender != null) 'gender': gender,
    };
    return ProfileSnapshot.fromJson(
      await _api.patchJson('/profile', {
        'hard_constraints': constraints,
      }, token: session.accessToken),
    );
  }

  Future<List<PreferenceItem>> preferences(Session session) async {
    final json = await _api.getJson(
      '/profile/preferences',
      token: session.accessToken,
    );
    final raw = json['preferences'];
    return raw is List
        ? raw
            .whereType<Map<String, dynamic>>()
            .map(PreferenceItem.fromJson)
            .toList()
        : const [];
  }

  Future<void> addPreference(
    Session session,
    String attribute,
    String value,
  ) async {
    await _api.postJson('/profile/preferences', {
      'attribute': attribute,
      'value': value,
    }, token: session.accessToken);
  }

  Future<void> removePreference(Session session, String id) async {
    await _api.delete(
      '/profile/preferences/${Uri.encodeComponent(id)}',
      token: session.accessToken,
    );
  }

  Future<void> setPreferenceLocked(
    Session session,
    String id, {
    required bool locked,
  }) async {
    final action = locked ? 'lock' : 'unlock';
    await _api.postJson(
      '/profile/preferences/${Uri.encodeComponent(id)}/$action',
      const {},
      token: session.accessToken,
    );
  }
}
