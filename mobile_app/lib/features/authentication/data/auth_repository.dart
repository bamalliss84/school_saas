import 'package:dio/dio.dart';
import '../../../core/models/auth_models.dart';
import '../../../core/storage/session_store.dart';

class AuthRepository {
  const AuthRepository(this._dio, this._store);
  final Dio _dio;
  final SessionStore _store;
  Future<LoginResult> login(String username, String password) async {
    final response = await _dio.post<Map<String, dynamic>>('auth/login/',
        data: {'username': username.trim(), 'password': password});
    final data = response.data!;
    await _store.writeTokens(
        access: data['access'].toString(), refresh: data['refresh'].toString());
    return LoginResult(
        tokens: AuthTokens(
            access: data['access'].toString(),
            refresh: data['refresh'].toString()),
        user: AuthenticatedUser.fromJson(
            Map<String, dynamic>.from(data['user'] as Map)));
  }

  Future<AuthenticatedUser> me() async => AuthenticatedUser.fromJson(
      (await _dio.get<Map<String, dynamic>>('auth/me/')).data!);
  Future<void> logout() async {
    final refresh = await _store.readRefreshToken();
    if (refresh != null) {
      await _dio.post<void>('auth/logout/', data: {'refresh': refresh});
    }
    await _store.clear();
  }
}
