class Session {
  const Session({
    required this.userId,
    required this.accessToken,
    this.email,
    this.isAuthenticated = false,
  });

  final String userId;
  final String accessToken;
  final String? email;
  final bool isAuthenticated;

  factory Session.fromJson(
    Map<String, dynamic> json, {
    bool authenticated = false,
  }) => Session(
    userId: json['user_id'] as String,
    accessToken: json['access_token'] as String,
    email: json['email'] as String?,
    isAuthenticated: authenticated,
  );
}
