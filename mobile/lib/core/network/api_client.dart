import 'dart:convert';

import 'package:http/http.dart' as http;

import '../config/app_config.dart';

class ApiException implements Exception {
  const ApiException(this.statusCode, this.message);

  final int statusCode;
  final String message;

  @override
  String toString() => 'ApiException($statusCode): $message';
}

class ApiClient {
  ApiClient({http.Client? httpClient}) : _http = httpClient ?? http.Client();

  final http.Client _http;

  Future<Map<String, dynamic>> getJson(
    String path, {
    String? token,
    Map<String, String>? queryParameters,
  }) async {
    final uri = _buildUri(path, queryParameters);
    final response = await _http.get(uri, headers: _headers(token));
    return _decode(response);
  }

  Future<Map<String, dynamic>> postJson(
    String path,
    Map<String, dynamic> body, {
    String? token,
  }) async {
    final uri = _buildUri(path);
    final response = await _http.post(
      uri,
      headers: {..._headers(token), 'Content-Type': 'application/json'},
      body: jsonEncode(body),
    );
    return _decode(response);
  }

  Future<Map<String, dynamic>> patchJson(
    String path,
    Map<String, dynamic> body, {
    String? token,
  }) async {
    final response = await _http.patch(
      _buildUri(path),
      headers: {..._headers(token), 'Content-Type': 'application/json'},
      body: jsonEncode(body),
    );
    return _decode(response);
  }

  Future<void> delete(String path, {String? token}) async {
    final response = await _http.delete(
      _buildUri(path),
      headers: _headers(token),
    );
    _decode(response);
  }

  Future<Map<String, dynamic>> postMultipart(
    String path,
    List<http.MultipartFile> files, {
    String? token,
  }) async {
    final request = http.MultipartRequest('POST', _buildUri(path));
    request.headers.addAll(_headers(token));
    request.files.addAll(files);
    final response = await http.Response.fromStream(await request.send());
    return _decode(response);
  }

  Uri _buildUri(String path, [Map<String, String>? queryParameters]) {
    final base = AppConfig.apiBaseUrl;
    return Uri.parse('$base$path').replace(queryParameters: queryParameters);
  }

  Map<String, String> _headers(String? token) => {
    'Accept': 'application/json',
    if (token != null && token.isNotEmpty) 'Authorization': 'Bearer $token',
  };

  Map<String, dynamic> _decode(http.Response response) {
    Map<String, dynamic> payload = <String, dynamic>{};
    if (response.body.isNotEmpty) {
      final decoded = jsonDecode(response.body);
      if (decoded is Map<String, dynamic>) payload = decoded;
    }

    if (response.statusCode < 200 || response.statusCode >= 300) {
      final detail = payload['detail'];
      throw ApiException(
        response.statusCode,
        detail is String ? detail : 'La requête n’a pas abouti.',
      );
    }
    return payload;
  }
}
