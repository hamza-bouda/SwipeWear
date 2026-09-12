import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../auth/providers.dart';
import 'data/drop_repository.dart';

final dropRepositoryProvider = Provider<DropRepository>(
  (ref) => DropRepository(
    ref.watch(apiClientProvider),
    ref.watch(sessionStoreProvider),
  ),
);

final dropProvider = FutureProvider.autoDispose((ref) async {
  final session = await ref.watch(sessionProvider.future);
  return ref.watch(dropRepositoryProvider).get(session);
});
