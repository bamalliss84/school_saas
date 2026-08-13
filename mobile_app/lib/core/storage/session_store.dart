import 'package:flutter_secure_storage/flutter_secure_storage.dart';

abstract interface class SessionStore {
  Future<String?> readAccessToken();
  Future<String?> readRefreshToken();
  Future<int?> readMembershipId();
  Future<void> writeTokens({required String access, required String refresh});
  Future<void> writeMembershipId(int? membershipId);
  Future<void> clear();
}

class SecureSessionStore implements SessionStore {
  SecureSessionStore([FlutterSecureStorage? storage])
      : _storage = storage ?? const FlutterSecureStorage();
  static const _accessKey = 'session.access_token';
  static const _refreshKey = 'session.refresh_token';
  static const _membershipKey = 'session.membership_id';
  final FlutterSecureStorage _storage;

  @override
  Future<String?> readAccessToken() => _storage.read(key: _accessKey);
  @override
  Future<String?> readRefreshToken() => _storage.read(key: _refreshKey);
  @override
  Future<int?> readMembershipId() async =>
      int.tryParse(await _storage.read(key: _membershipKey) ?? '');
  @override
  Future<void> writeTokens(
      {required String access, required String refresh}) async {
    await _storage.write(key: _accessKey, value: access);
    await _storage.write(key: _refreshKey, value: refresh);
  }

  @override
  Future<void> writeMembershipId(int? membershipId) => membershipId == null
      ? _storage.delete(key: _membershipKey)
      : _storage.write(key: _membershipKey, value: '$membershipId');
  @override
  Future<void> clear() => _storage.deleteAll();
}
