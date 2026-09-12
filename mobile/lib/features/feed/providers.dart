import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../auth/providers.dart';
import 'data/feed_repository.dart';

final feedRepositoryProvider = Provider<FeedRepository>(
  (ref) => FeedRepository(
    ref.watch(apiClientProvider),
    ref.watch(sessionStoreProvider),
  ),
);

final feedProvider = FutureProvider.autoDispose<FeedResponse>((ref) async {
  final session = await ref.watch(sessionProvider.future);
  return ref.watch(feedRepositoryProvider).fetch(session);
});
