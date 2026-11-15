import 'dart:convert';

import 'package:dio/dio.dart';

import '../../../../core/local_database/app_database.dart';
import '../../../../core/offline/offline_error_policy.dart';
import '../domain/parent_fee_models.dart';

/// Thrown when the guardian has no financial access to this child (server 403/404).
class ParentFeesUnavailable implements Exception {
  const ParentFeesUnavailable();
}

class ParentFeesRepository {
  ParentFeesRepository(this.dio, this.database);
  final Dio dio;
  final AppDatabase database;

  String _resource(int childId) => 'parent_fees_v1_child_$childId';

  Future<ParentFeesData?> read(CacheScope scope, int childId) async {
    final rows = await database.readContexts(scope);
    for (final row in rows) {
      if (row.resourceId == _resource(childId)) {
        return ParentFeesData.fromJson(
          Map<String, dynamic>.from(jsonDecode(row.payloadJson) as Map),
          row.lastSyncedAt,
          offline: true,
        );
      }
    }
    return null;
  }

  Future<ParentFeesData> load(CacheScope scope, int childId) async {
    final cached = await read(scope, childId);
    try {
      return await refresh(scope, childId);
    } catch (error) {
      if (cached != null && isOfflineEligibleError(error)) return cached;
      rethrow;
    }
  }

  Future<ParentFeesData> refresh(CacheScope scope, int childId) async {
    final Response<dynamic> response;
    try {
      response = await dio.get<dynamic>('parents/me/children/$childId/fees/');
    } on DioException catch (error) {
      final status = error.response?.statusCode;
      if (status == 403 || status == 404) throw const ParentFeesUnavailable();
      rethrow;
    }
    final payload = Map<String, dynamic>.from(response.data as Map);
    final data = ParentFeesData.fromJson(payload, DateTime.now().toUtc());
    await database.putContext(
      scope: scope,
      resourceId: _resource(childId),
      payload: payload,
      isHistorical: false,
      syncedAt: data.lastUpdated,
    );
    return data;
  }
}
