import 'package:flutter/foundation.dart';
import 'package:purchases_flutter/purchases_flutter.dart';

import '../../auth/data/session.dart';

const premiumEntitlementId = 'swipewear_premium_monthly';

class PurchaseOutcome {
  const PurchaseOutcome({
    required this.success,
    required this.active,
    this.message,
  });
  final bool success;
  final bool active;
  final String? message;
}

class RevenueCatService {
  static bool _configured = false;

  static String get _apiKey => switch (defaultTargetPlatform) {
    TargetPlatform.iOS => const String.fromEnvironment('REVENUECAT_IOS_KEY'),
    TargetPlatform.android => const String.fromEnvironment(
      'REVENUECAT_ANDROID_KEY',
    ),
    _ => '',
  };

  static Future<bool> configure(Session session) async {
    if (_apiKey.isEmpty) return false;
    if (!_configured) {
      await Purchases.configure(
        PurchasesConfiguration(_apiKey)..appUserID = session.userId,
      );
      _configured = true;
    } else {
      await Purchases.logIn(session.userId);
    }
    return true;
  }

  static Future<PurchaseOutcome> purchase(
    Session session, {
    bool annual = false,
  }) async {
    if (!await configure(session)) {
      return const PurchaseOutcome(
        success: false,
        active: false,
        message: 'Clé RevenueCat manquante.',
      );
    }
    try {
      final offerings = await Purchases.getOfferings();
      final package =
          annual
              ? (offerings.current?.annual ??
                  offerings.current?.monthly ??
                  offerings.current?.availablePackages.firstOrNull)
              : (offerings.current?.monthly ??
                  offerings.current?.annual ??
                  offerings.current?.availablePackages.firstOrNull);
      if (package == null) {
        return const PurchaseOutcome(
          success: false,
          active: false,
          message: 'Aucun abonnement disponible.',
        );
      }
      final info = await Purchases.purchasePackage(package);
      final active = info.entitlements.active.containsKey(premiumEntitlementId);
      return PurchaseOutcome(success: true, active: active);
    } on PurchasesErrorCode catch (error) {
      return PurchaseOutcome(
        success: false,
        active: false,
        message: error.toString(),
      );
    } catch (error) {
      return PurchaseOutcome(
        success: false,
        active: false,
        message: error.toString(),
      );
    }
  }

  static Future<PurchaseOutcome> restore(Session session) async {
    if (!await configure(session)) {
      return const PurchaseOutcome(
        success: false,
        active: false,
        message: 'Clé RevenueCat manquante.',
      );
    }
    try {
      final info = await Purchases.restorePurchases();
      return PurchaseOutcome(
        success: true,
        active: info.entitlements.active.containsKey(premiumEntitlementId),
      );
    } catch (error) {
      return PurchaseOutcome(
        success: false,
        active: false,
        message: error.toString(),
      );
    }
  }
}
