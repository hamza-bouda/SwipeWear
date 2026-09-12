import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../auth/providers.dart';
import 'data/saves_repository.dart';

final savesRepositoryProvider = Provider<SavesRepository>(
  (ref) => SavesRepository(
    ref.watch(apiClientProvider),
    ref.watch(sessionStoreProvider),
  ),
);

final savesProvider = FutureProvider.autoDispose((ref) async {
  final session = await ref.watch(sessionProvider.future);
  return ref.watch(savesRepositoryProvider).get(session);
});
