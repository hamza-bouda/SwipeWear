import 'dart:async';

import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:firebase_core/firebase_core.dart';
import 'package:firebase_messaging/firebase_messaging.dart';

import '../../../core/network/api_client.dart';
import '../../auth/data/session.dart';
import '../../drop/presentation/drop_screen.dart';
import '../../feed/data/product.dart';
import '../../feed/presentation/product_detail_screen.dart';

class PushNotificationService {
  PushNotificationService(this._api);

  final ApiClient _api;
  String? _registeredForUser;
  Session? _session;
  GlobalKey<NavigatorState>? _navigatorKey;
  bool _listenersConfigured = false;
  StreamSubscription<String>? _tokenRefreshSubscription;

  Future<void> initialize(
    Session session, {
    GlobalKey<NavigatorState>? navigatorKey,
  }) async {
    _session = session;
    _navigatorKey = navigatorKey ?? _navigatorKey;
    if (_registeredForUser == session.userId) return;
    try {
      if (Firebase.apps.isEmpty) await Firebase.initializeApp();
      final messaging = FirebaseMessaging.instance;
      _configureMessageOpening(messaging);
      _configureTokenRefresh(messaging);
      final permission = await messaging.requestPermission(
        alert: true,
        badge: true,
        sound: true,
      );
      if (permission.authorizationStatus == AuthorizationStatus.denied) return;
      final token = await messaging.getToken();
      await _registerToken(session, token);
    } catch (_) {
      // Firebase configuration is supplied per app environment. A missing
      // config or temporary network issue must not block browsing.
    }
  }

  void _configureTokenRefresh(FirebaseMessaging messaging) {
    if (_tokenRefreshSubscription != null) return;
    _tokenRefreshSubscription = messaging.onTokenRefresh.listen((token) {
      final session = _session;
      if (session != null) unawaited(_registerToken(session, token));
    });
  }

  Future<void> _registerToken(Session session, String? token) async {
    if (token == null || token.isEmpty) return;
    try {
      await _api.postJson('/notifications/register', {
        'device_token': token,
        'platform': defaultTargetPlatformName,
      }, token: session.accessToken);
      _registeredForUser = session.userId;
    } catch (_) {
      // A token refresh must never interrupt browsing. The next refresh or
      // app launch retries registration with the current session.
    }
  }

  void _configureMessageOpening(FirebaseMessaging messaging) {
    if (_listenersConfigured || _navigatorKey == null) return;
    _listenersConfigured = true;
    FirebaseMessaging.onMessageOpenedApp.listen(_openMessage);
    messaging.getInitialMessage().then((message) {
      if (message != null) {
        Future<void>.delayed(
          const Duration(milliseconds: 500),
          () => _openMessage(message),
        );
      }
    });
  }

  Future<void> _openMessage(RemoteMessage message) async {
    final navigator = _navigatorKey?.currentState;
    final session = _session;
    if (navigator == null || session == null) return;
    final queueId = message.data['queue_id'];
    if (queueId is String && queueId.isNotEmpty) {
      try {
        await _api.postJson('/notifications/opened', {
          'queue_id': queueId,
        }, token: session.accessToken);
      } catch (_) {}
    }
    try {
      await _api.postJson('/analytics/events', {
        'name': 'push_opened',
        'properties': {'queue_id': queueId, 'type': message.data['type']},
        'occurred_at': DateTime.now().toUtc().toIso8601String(),
      }, token: session.accessToken);
    } catch (_) {}
    final productId = message.data['product_id'];
    if (productId is String && productId.isNotEmpty) {
      try {
        final json = await _api.getJson(
          '/products/${Uri.encodeComponent(productId)}',
          token: session.accessToken,
        );
        if (!navigator.mounted) return;
        navigator.push(
          MaterialPageRoute(
            builder:
                (_) => ProductDetailScreen(product: Product.fromJson(json)),
          ),
        );
      } catch (_) {}
      return;
    }
    if (message.data['type'] == 'drop' || message.data['screen'] == 'Drop') {
      if (!navigator.mounted) return;
      navigator.push(MaterialPageRoute(builder: (_) => const DropScreen()));
    }
  }

  static String get defaultTargetPlatformName {
    // The backend accepts the platform as metadata; FCM remains the single
    // token format for both Android and iOS.
    return switch (defaultTargetPlatform) {
      TargetPlatform.android => 'android',
      TargetPlatform.iOS => 'ios',
      _ => 'unknown',
    };
  }
}
