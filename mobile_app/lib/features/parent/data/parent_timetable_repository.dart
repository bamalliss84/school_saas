import 'dart:convert';

import 'package:dio/dio.dart';

import '../../../../core/local_database/app_database.dart';
import '../../../../core/offline/offline_error_policy.dart';
import '../domain/parent_timetable_models.dart';

class ParentTimetableRepository {
  ParentTimetableRepository(this.dio, this.database);
  final Dio dio;
  final AppDatabase database;

  String _resource(int childId) => 'parent_timetable_v1_child_$childId';

  Future<ParentTimetableData?> read(CacheScope scope, int childId) async {
    final rows = await database.readContexts(scope);
    for (final row in rows) {
      if (row.resourceId == _resource(childId)) {
        return ParentTimetableData.fromJson(
          Map<String, dynamic>.from(jsonDecode(row.payloadJson) as Map),
          row.lastSyncedAt,
          offline: true,
        );
      }
    }
    return null;
  }

  Future<ParentTimetableData> load(CacheScope scope, int childId) async {
    final cached = await read(scope, childId);
    try {
      return await refresh(scope, childId);
    } catch (error) {
      if (cached != null && isOfflineEligibleError(error)) return cached;
      rethrow;
    }
  }

  Future<ParentTimetableData> refresh(CacheScope scope, int childId) async {
    final response = await dio.get<dynamic>(
      'timetable/week/',
      queryParameters: {'student_id': childId},
    );
    final payload = Map<String, dynamic>.from(response.data as Map);
    final data = ParentTimetableData.fromJson(payload, DateTime.now().toUtc());
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
