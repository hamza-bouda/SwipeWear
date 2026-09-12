import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../features/auth/providers.dart';
import 'analytics_service.dart';

final analyticsServiceProvider = Provider<AnalyticsService>(
  (ref) => AnalyticsService(ref.watch(apiClientProvider)),
);
