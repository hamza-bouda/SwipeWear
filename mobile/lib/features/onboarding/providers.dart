import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../auth/providers.dart';
import 'data/onboarding_repository.dart';

final onboardingRepositoryProvider = Provider<OnboardingRepository>(
  (ref) => OnboardingRepository(ref.watch(apiClientProvider)),
);
