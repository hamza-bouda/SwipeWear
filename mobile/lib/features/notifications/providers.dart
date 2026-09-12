import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../auth/providers.dart';
import 'data/push_notification_service.dart';

final pushNotificationServiceProvider = Provider<PushNotificationService>(
  (ref) => PushNotificationService(ref.watch(apiClientProvider)),
);
