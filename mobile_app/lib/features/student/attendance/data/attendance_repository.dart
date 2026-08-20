import 'dart:convert';

import 'package:dio/dio.dart';

import '../../../../core/local_database/app_database.dart';
import '../../../../core/offline/offline_error_policy.dart';
import '../domain/attendance_models.dart';

const _attendanceCacheResource = 'student_attendance_v1';

class StudentAttendanceRepository {
  StudentAttendanceRepository(this.dio, this.db);
  final Dio dio;
  final AppDatabase db;

  Future<StudentAttendanceData?> read(CacheScope scope) async {
    final rows = await db.readContexts(scope);
    final matches = rows.where((row) => row.resourceId == _attendanceCacheResource);
    if (matches.isEmpty) return null;
    final row = matches.first;
    return StudentAttendanceData.fromJson(
      Map<String, dynamic>.from(jsonDecode(row.payloadJson) as Map),
      row.lastSyncedAt,
      offline: true,
    );
  }

  Future<StudentAttendanceData> refresh(CacheScope scope) async {
    final response = await dio.get('students/me/attendance/');
    final payload = Map<String, Object?>.from(response.data as Map);
    final now = DateTime.now().toUtc();
    await db.putContext(
      scope: scope,
      resourceId: _attendanceCacheResource,
      payload: payload,
      isHistorical: false,
      syncedAt: now,
    );
    return StudentAttendanceData.fromJson(
      Map<String, dynamic>.from(payload), now,
    );
  }

  Future<StudentAttendanceData> load(CacheScope scope) async {
    final cached = await read(scope);
    try {
      return await refresh(scope);
    } catch (error) {
      if (cached != null && isOfflineEligibleError(error)) return cached;
      rethrow;
    }
  }
}
