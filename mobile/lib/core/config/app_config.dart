import 'dart:io';

abstract final class AppConfig {
  static const googleServerClientId = String.fromEnvironment(
    'GOOGLE_SERVER_CLIENT_ID',
  );
  static const googleIosClientId = String.fromEnvironment(
    'GOOGLE_IOS_CLIENT_ID',
  );

  static String get apiBaseUrl {
    const configured = String.fromEnvironment('API_BASE_URL');
    if (configured.trim().isNotEmpty) {
      return configured.trim().replaceFirst(RegExp(r'/$'), '');
    }

    // Android emulators expose the host machine through 10.0.2.2.
    return Platform.isAndroid
        ? 'http://10.0.2.2:8000'
        : 'http://localhost:8000';
  }
}
