import 'dart:convert';

import 'package:dio/dio.dart';

import '../../../../core/local_database/app_database.dart';
import '../../../../core/offline/offline_error_policy.dart';
import '../domain/parent_attendance_models.dart';

class ParentAttendanceRepository {
  ParentAttendanceRepository(this.dio, this.database);
  final Dio dio;
  final AppDatabase database;

  String _resource(int childId) => 'parent_attendance_v1_child_$childId';

  Future<ParentAttendanceData?> read(CacheScope scope, int childId) async {
    final rows = await database.readContexts(scope);
    for (final row in rows) {
      if (row.resourceId == _resource(childId)) {
        return ParentAttendanceData.fromJson(
          Map<String, dynamic>.from(jsonDecode(row.payloadJson) as Map),
          row.lastSyncedAt,
          offline: true,
        );
      }
    }
    return null;
  }

  Future<ParentAttendanceData> load(CacheScope scope, int childId) async {
    final cached = await read(scope, childId);
    try {
      return await refresh(scope, childId);
    } catch (error) {
      if (cached != null && isOfflineEligibleError(error)) return cached;
      rethrow;
    }
  }

  Future<ParentAttendanceData> refresh(CacheScope scope, int childId) async {
    final academicYearId = int.tryParse(scope.academicYearKey);
    final response = await dio.get<dynamic>(
      'attendance/student/$childId/summary/',
      queryParameters: {
        if (academicYearId != null) 'academic_year_id': academicYearId,
      },
    );
    final payload = Map<String, dynamic>.from(response.data as Map);
    final data = ParentAttendanceData.fromJson(
      payload,
      DateTime.now().toUtc(),
    );
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
