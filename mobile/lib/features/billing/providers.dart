import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../auth/providers.dart';
import 'data/billing_repository.dart';

final billingRepositoryProvider = Provider<BillingRepository>(
  (ref) => BillingRepository(ref.watch(apiClientProvider)),
);

final billingProvider = FutureProvider.autoDispose((ref) async {
  final session = await ref.watch(sessionProvider.future);
  return ref.watch(billingRepositoryProvider).status(session);
});
