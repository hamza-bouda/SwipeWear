import '../../../core/network/api_client.dart';
import '../../auth/data/session.dart';

class BillingStatus {
  const BillingStatus({required this.isPremium, this.status, this.expiresAt});

  final bool isPremium;
  final String? status;
  final DateTime? expiresAt;

  factory BillingStatus.fromJson(Map<String, dynamic> json) => BillingStatus(
    isPremium: json['is_premium'] as bool? ?? false,
    status: json['status'] as String?,
    expiresAt: DateTime.tryParse(json['expires_at'] as String? ?? ''),
  );
}

class BillingRepository {
  BillingRepository(this._api);
  final ApiClient _api;

  Future<BillingStatus> status(Session session) async => BillingStatus.fromJson(
    await _api.getJson('/billing/status', token: session.accessToken),
  );
}
