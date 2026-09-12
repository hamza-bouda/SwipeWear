import 'package:http/http.dart' as http;

import '../../../core/network/api_client.dart';
import '../../auth/data/session.dart';

class OnboardingRepository {
  OnboardingRepository(this._api);

  final ApiClient _api;

  Future<void> submitStyles(
    Session session, {
    required List<String> styleIds,
    required List<String> sizes,
    required double? maxPrice,
    required String gender,
  }) async {
    await _api.postJson('/onboarding/styles', {
      'style_ids': styleIds,
      'sizes': sizes,
      'max_price_eur': maxPrice,
      'gender': gender,
    }, token: session.accessToken);
  }

  Future<void> uploadInspirations(Session session, List<String> paths) async {
    final files = <http.MultipartFile>[];
    for (var index = 0; index < paths.length; index++) {
      files.add(
        await http.MultipartFile.fromPath(
          'files',
          paths[index],
          filename: 'inspiration-$index.jpg',
        ),
      );
    }
    await _api.postMultipart(
      '/onboarding/images/upload',
      files,
      token: session.accessToken,
    );
  }
}
