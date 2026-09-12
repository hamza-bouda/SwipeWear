import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../auth/providers.dart';
import 'data/alerts_repository.dart';

final alertsRepositoryProvider = Provider<AlertsRepository>(
  (ref) => AlertsRepository(
    ref.watch(apiClientProvider),
    ref.watch(sessionStoreProvider),
  ),
);

final alertsProvider = FutureProvider.autoDispose((ref) async {
  final session = await ref.watch(sessionProvider.future);
  return ref.watch(alertsRepositoryProvider).get(session);
});
