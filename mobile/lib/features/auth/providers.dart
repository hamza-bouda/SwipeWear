import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/network/api_client.dart';
import '../../core/localization/app_localizations.dart';
import '../../core/storage/session_store.dart';
import 'data/auth_repository.dart';
import 'data/session.dart';

final apiClientProvider = Provider<ApiClient>((ref) => ApiClient());

final sessionStoreProvider = Provider<SessionStore>((ref) => SessionStore());

final localeControllerProvider = ChangeNotifierProvider<AppLocaleController>((
  ref,
) {
  final store = ref.watch(sessionStoreProvider);
  return AppLocaleController(store.readLocale, store.writeLocale);
});

final authRepositoryProvider = Provider<AuthRepository>(
  (ref) => AuthRepository(
    ref.watch(apiClientProvider),
    ref.watch(sessionStoreProvider),
  ),
);

final sessionProvider = FutureProvider<Session>(
  (ref) => ref.watch(authRepositoryProvider).ensureSession(),
);

final onboardingCompleteProvider = FutureProvider<bool>(
  (ref) => ref.watch(sessionStoreProvider).isOnboardingComplete(),
);
