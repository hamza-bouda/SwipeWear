import 'dart:convert';

import 'package:flutter_secure_storage/flutter_secure_storage.dart';

import '../../features/auth/data/session.dart';

class SessionStore {
  SessionStore({FlutterSecureStorage? storage})
    : _storage = storage ?? const FlutterSecureStorage();

  static const _userIdKey = 'swipewear.user_id';
  static const _accessTokenKey = 'swipewear.access_token';
  static const _emailKey = 'swipewear.email';
  static const _authenticatedKey = 'swipewear.authenticated';
  static const _onboardingKey = 'swipewear.onboarding_complete';
  static const _localeKey = 'swipewear.locale';

  final FlutterSecureStorage _storage;

  Future<Session?> read() async {
    final userId = await _storage.read(key: _userIdKey);
    final accessToken = await _storage.read(key: _accessTokenKey);
    if (userId == null || accessToken == null) return null;
    return Session(
      userId: userId,
      accessToken: accessToken,
      email: await _storage.read(key: _emailKey),
      isAuthenticated: await _storage.read(key: _authenticatedKey) == 'true',
    );
  }

  Future<void> write(Session session) async {
    await _storage.write(key: _userIdKey, value: session.userId);
    await _storage.write(key: _accessTokenKey, value: session.accessToken);
    await _storage.write(
      key: _authenticatedKey,
      value: session.isAuthenticated.toString(),
    );
    if (session.email == null) {
      await _storage.delete(key: _emailKey);
    } else {
      await _storage.write(key: _emailKey, value: session.email);
    }
  }

  Future<void> clear() async {
    final userId = await _storage.read(key: _userIdKey);
    if (userId != null && userId.isNotEmpty) {
      for (final namespace in _cachedNamespaces) {
        await _storage.delete(key: 'swipewear.cache.$userId.$namespace');
      }
    }
    await _storage.delete(key: _userIdKey);
    await _storage.delete(key: _accessTokenKey);
    await _storage.delete(key: _emailKey);
    await _storage.delete(key: _authenticatedKey);
    await _storage.delete(key: _onboardingKey);
  }

  Future<bool> isOnboardingComplete() async =>
      (await _storage.read(key: _onboardingKey)) == 'true';

  Future<void> setOnboardingComplete(bool value) async {
    await _storage.write(key: _onboardingKey, value: value.toString());
  }

  Future<void> clearOnboarding() async {
    await _storage.delete(key: _onboardingKey);
  }

  Future<String?> readLocale() => _storage.read(key: _localeKey);

  Future<void> writeLocale(String languageCode) =>
      _storage.write(key: _localeKey, value: languageCode);

  Future<void> writeCachedJson(
    String namespace,
    String userId,
    Map<String, dynamic> value,
  ) => _storage.write(
    key: 'swipewear.cache.$userId.$namespace',
    value: jsonEncode(value),
  );

  Future<Map<String, dynamic>?> readCachedJson(
    String namespace,
    String userId,
  ) async {
    final raw = await _storage.read(key: 'swipewear.cache.$userId.$namespace');
    if (raw == null || raw.isEmpty) return null;
    try {
      final decoded = jsonDecode(raw);
      return decoded is Map<String, dynamic> ? decoded : null;
    } catch (_) {
      return null;
    }
  }

  static const _cachedNamespaces = <String>['feed', 'alerts', 'saves', 'drop'];
}
