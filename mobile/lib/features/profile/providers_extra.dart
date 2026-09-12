import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../auth/providers.dart';
import 'data/notification_repository.dart';
import 'data/profile.dart';
import 'providers.dart';

final notificationRepositoryProvider = Provider<NotificationRepository>(
  (ref) => NotificationRepository(ref.watch(apiClientProvider)),
);

final notificationPreferenceProvider = FutureProvider.autoDispose((ref) async {
  final session = await ref.watch(sessionProvider.future);
  return ref.watch(notificationRepositoryProvider).getPreference(session);
});

final algorithmPreferencesProvider =
    FutureProvider.autoDispose<List<PreferenceItem>>((ref) async {
      final session = await ref.watch(sessionProvider.future);
      return ref.watch(profileRepositoryProvider).preferences(session);
    });
