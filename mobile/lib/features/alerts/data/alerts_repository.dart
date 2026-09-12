import '../../../core/network/api_client.dart';
import '../../../core/storage/session_store.dart';
import '../../auth/data/session.dart';

class AlertItem {
  const AlertItem({
    required this.id,
    required this.type,
    required this.label,
    required this.status,
    required this.maxPrice,
    required this.sizes,
    required this.minCondition,
    this.referenceProductId,
  });

  final String id;
  final String type;
  final String label;
  final String status;
  final double? maxPrice;
  final List<String> sizes;
  final String? minCondition;
  final String? referenceProductId;

  bool get active => status == 'active';

  factory AlertItem.fromJson(Map<String, dynamic> json) {
    final constraints = json['constraints'];
    final map =
        constraints is Map<String, dynamic>
            ? constraints
            : const <String, dynamic>{};
    final rawSizes = map['sizes'];
    return AlertItem(
      id: json['alert_id'] as String? ?? '',
      type: json['alert_type'] as String? ?? 'style',
      label: json['label'] as String? ?? 'Alerte sans nom',
      status: json['status'] as String? ?? 'active',
      maxPrice: (map['max_price_eur'] as num?)?.toDouble(),
      sizes:
          rawSizes is List ? rawSizes.whereType<String>().toList() : const [],
      minCondition: map['min_condition'] as String?,
      referenceProductId: json['reference_product_id'] as String?,
    );
  }

  AlertItem copyWith({String? status}) => AlertItem(
    id: id,
    type: type,
    label: label,
    status: status ?? this.status,
    maxPrice: maxPrice,
    sizes: sizes,
    minCondition: minCondition,
    referenceProductId: referenceProductId,
  );
}

class AlertsSnapshot {
  const AlertsSnapshot({
    required this.alerts,
    required this.activeCount,
    required this.freeLimit,
    required this.missedDeals,
    this.isOffline = false,
  });

  final List<AlertItem> alerts;
  final int activeCount;
  final int freeLimit;
  final int missedDeals;
  final bool isOffline;

  factory AlertsSnapshot.fromJson(
    Map<String, dynamic> json, {
    bool isOffline = false,
  }) {
    final raw = json['alerts'];
    return AlertsSnapshot(
      alerts:
          raw is List
              ? raw
                  .whereType<Map<String, dynamic>>()
                  .map(AlertItem.fromJson)
                  .toList()
              : const [],
      activeCount: json['active_count'] as int? ?? 0,
      freeLimit: json['free_limit'] as int? ?? 1,
      missedDeals: json['missed_deals_count'] as int? ?? 0,
      isOffline: isOffline,
    );
  }
}

class AlertsRepository {
  AlertsRepository(this._api, this._store);

  final ApiClient _api;
  final SessionStore _store;

  Future<AlertsSnapshot> get(Session session) async {
    try {
      final json = await _api.getJson('/alerts', token: session.accessToken);
      await _store.writeCachedJson('alerts', session.userId, json);
      return AlertsSnapshot.fromJson(json);
    } catch (error) {
      if (error is ApiException && error.statusCode < 500) rethrow;
      final cached = await _store.readCachedJson('alerts', session.userId);
      if (cached != null) {
        return AlertsSnapshot.fromJson(cached, isOffline: true);
      }
      rethrow;
    }
  }

  Future<AlertItem> create(
    Session session, {
    required String label,
    required String type,
    String? referenceProductId,
    double? maxPrice,
    List<String> sizes = const [],
    String? minCondition,
  }) async {
    final json = await _api.postJson('/alerts', {
      'alert_type': type,
      'label': label,
      if (referenceProductId != null)
        'reference_product_id': referenceProductId,
      'constraints': {
        if (maxPrice != null) 'max_price_eur': maxPrice,
        'sizes': sizes,
        if (minCondition != null) 'min_condition': minCondition,
      },
    }, token: session.accessToken);
    return AlertItem.fromJson(json);
  }

  Future<AlertItem> setStatus(
    Session session,
    AlertItem alert,
    bool active,
  ) async => AlertItem.fromJson(
    await _api.patchJson('/alerts/${alert.id}', {
      'status': active ? 'active' : 'paused',
    }, token: session.accessToken),
  );

  Future<AlertItem> updateConstraints(
    Session session,
    AlertItem alert, {
    required double? maxPrice,
    required List<String> sizes,
    String? minCondition,
  }) async => AlertItem.fromJson(
    await _api.patchJson('/alerts/${alert.id}', {
      'constraints': {
        'max_price_eur': maxPrice,
        'sizes': sizes,
        if (minCondition != null) 'min_condition': minCondition,
      },
    }, token: session.accessToken),
  );

  Future<void> remove(Session session, AlertItem alert) async =>
      _api.delete('/alerts/${alert.id}', token: session.accessToken);
}
