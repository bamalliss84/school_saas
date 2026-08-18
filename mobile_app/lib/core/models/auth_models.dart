class AuthTokens {
  const AuthTokens({required this.access, required this.refresh});
  final String access;
  final String refresh;
}

class AuthenticatedUser {
  const AuthenticatedUser(
      {required this.id,
      required this.username,
      required this.fullName,
      required this.role});
  final int id;
  final String username;
  final String fullName;
  final String role;

  factory AuthenticatedUser.fromJson(Map<String, dynamic> json) =>
      AuthenticatedUser(
        id: json['id'] as int,
        username: json['username']?.toString() ?? '',
        fullName: json['full_name']?.toString() ?? '',
        role: json['role']?.toString() ?? '',
      );

  Map<String, Object?> toJson() => {
        'id': id,
        'username': username,
        'full_name': fullName,
        'role': role,
      };
}

class LoginResult {
  const LoginResult({required this.tokens, required this.user});
  final AuthTokens tokens;
  final AuthenticatedUser user;
}
