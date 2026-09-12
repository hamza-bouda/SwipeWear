import 'package:google_sign_in/google_sign_in.dart';

import '../../../core/config/app_config.dart';
import '../../../core/network/api_client.dart';
import '../../../core/storage/session_store.dart';
import 'session.dart';

class AuthRepository {
  AuthRepository(this._api, this._store);

  final ApiClient _api;
  final SessionStore _store;
  final GoogleSignIn _googleSignIn = GoogleSignIn(
    scopes: ['email'],
    serverClientId:
        AppConfig.googleServerClientId.isEmpty
            ? null
            : AppConfig.googleServerClientId,
    clientId:
        AppConfig.googleIosClientId.isEmpty
            ? null
            : AppConfig.googleIosClientId,
  );

  Future<Session> ensureSession() async {
    final existing = await _store.read();
    if (existing != null) return existing;

    final json = await _api.postJson('/auth/anonymous', const {});
    final session = Session.fromJson(json);
    await _store.write(session);
    return session;
  }

  Future<Session> login(String email, String password) async {
    final json = await _api.postJson('/auth/login', {
      'email': email,
      'password': password,
    });
    final session = Session.fromJson(json, authenticated: true);
    await _store.write(session);
    return session;
  }

  Future<Session?> loginWithGoogle(Session current) async {
    final account = await _googleSignIn.signIn();
    if (account == null) return null;
    final authentication = await account.authentication;
    final idToken = authentication.idToken;
    if (idToken == null || idToken.isEmpty) {
      throw StateError('Google n’a pas retourné de jeton d’identité.');
    }
    final json = await _api.postJson('/auth/google', {
      'id_token': idToken,
    }, token: current.accessToken);
    final session = Session.fromJson(json, authenticated: true);
    await _store.write(session);
    return session;
  }

  Future<Session> register(
    String email,
    String password,
    Session current,
  ) async {
    final json = await _api.postJson('/auth/register', {
      'email': email,
      'password': password,
    }, token: current.accessToken);
    final session = Session.fromJson(json, authenticated: true);
    await _store.write(session);
    return session;
  }

  Future<void> deleteAccount(Session session) async {
    await _api.delete('/auth/account', token: session.accessToken);
    await _store.clear();
  }
}
