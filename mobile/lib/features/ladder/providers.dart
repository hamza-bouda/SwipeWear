import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../auth/providers.dart';
import 'data/ladder_repository.dart';

final ladderRepositoryProvider = Provider<LadderRepository>(
  (ref) => LadderRepository(ref.watch(apiClientProvider)),
);

final ladderProvider = FutureProvider.autoDispose.family<PriceLadder, String>((
  ref,
  productId,
) async {
  final session = await ref.watch(sessionProvider.future);
  return ref.watch(ladderRepositoryProvider).get(session, productId);
});
