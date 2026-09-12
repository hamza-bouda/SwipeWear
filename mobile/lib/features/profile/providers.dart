import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../auth/providers.dart';
import 'data/profile.dart';
import 'data/profile_repository.dart';

final profileRepositoryProvider = Provider<ProfileRepository>(
  (ref) => ProfileRepository(ref.watch(apiClientProvider)),
);

final profileProvider = FutureProvider.autoDispose<ProfileSnapshot>((
  ref,
) async {
  final session = await ref.watch(sessionProvider.future);
  return ref.watch(profileRepositoryProvider).get(session);
});
