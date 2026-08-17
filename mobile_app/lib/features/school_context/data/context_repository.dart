import 'package:dio/dio.dart';
import '../../../core/models/school_context.dart';
import '../../../core/storage/session_store.dart';

class ContextRepository {
  const ContextRepository(this._dio, this._store);
  final Dio _dio;
  final SessionStore _store;
  Future<int?> storedMembershipId() => _store.readMembershipId();
  Future<void> clearStoredMembership() => _store.writeMembershipId(null);

  Future<ContextListResult> list() async => ContextListResult.fromJson(
      (await _dio.get<Map<String, dynamic>>('auth/contexts/')).data!);
  Future<void> select(SchoolContext context) async {
    // Persist only after the server accepts an active context. Historical
    // contexts are local read-only selections and need no default mutation.
    if (context.isActive) {
      await _dio.post<void>('auth/context/default/',
          data: {'membership_id': context.membershipId});
    }
    await _store.writeMembershipId(context.membershipId);
  }
}
