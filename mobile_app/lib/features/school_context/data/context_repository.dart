import 'package:dio/dio.dart';
import '../../../core/models/school_context.dart';
import '../../../core/storage/session_store.dart';

class ContextRepository {
  const ContextRepository(this._dio, this._store);
  final Dio _dio;
  final SessionStore _store;
  Future<ContextListResult> list() async => ContextListResult.fromJson(
      (await _dio.get<Map<String, dynamic>>('auth/contexts/')).data!);
  Future<void> select(SchoolContext context) async {
    await _store.writeMembershipId(context.membershipId);
    if (context.isActive) {
      await _dio.post<void>('auth/context/default/',
          data: {'membership_id': context.membershipId});
    }
  }
}
