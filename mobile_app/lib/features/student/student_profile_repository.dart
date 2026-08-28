import 'dart:convert';
import 'package:dio/dio.dart';
import '../../core/local_database/app_database.dart';
import '../../core/offline/offline_error_policy.dart';
import 'student_profile_models.dart';

class StudentMoreData {
  const StudentMoreData(
      {required this.profile,
      required this.schools,
      required this.history,
      required this.lastUpdated,
      this.offline = false});
  final StudentProfile profile;
  final List<StudentSchoolSummary> schools;
  final List<StudentAcademicHistoryItem> history;
  final DateTime lastUpdated;
  final bool offline;
}

class StudentProfileRepository {
  StudentProfileRepository(this.dio, this.db);
  final Dio dio;
  final AppDatabase db;
  static const resourceId = 'student_more_profile_v1';

  Future<StudentMoreData?> read(CacheScope scope) async {
    final rows = await db.readContexts(scope);
    CachedContext? cached;
    for (final row in rows) {
      if (row.resourceId == resourceId) {
        cached = row;
        break;
      }
    }
    if (cached == null) return null;
    return _decode(
        Map<String, dynamic>.from(jsonDecode(cached.payloadJson) as Map),
        cached.lastSyncedAt,
        offline: true);
  }

  Future<StudentMoreData> refresh(CacheScope scope) async {
    final responses = await Future.wait([
      dio.get<Map<String, dynamic>>('students/me/profile/'),
      dio.get<List<dynamic>>('students/me/schools/'),
      dio.get<List<dynamic>>('students/me/academic-history/',
          queryParameters: {'school_membership_id': scope.membershipId}),
    ]);
    final payload = <String, Object?>{
      'profile': Map<String, dynamic>.from(responses[0].data as Map),
      'schools': (responses[1].data as List)
          .whereType<Map>()
          .map((item) => Map<String, dynamic>.from(item))
          .toList(),
      'history': (responses[2].data as List)
          .whereType<Map>()
          .map((item) => Map<String, dynamic>.from(item))
          .toList(),
    };
    final now = DateTime.now().toUtc();
    await db.putContext(
        scope: scope,
        resourceId: resourceId,
        payload: payload,
        isHistorical: false,
        syncedAt: now);
    return _decode(payload, now);
  }

  Future<StudentMoreData> load(CacheScope scope) async {
    final cached = await read(scope);
    try {
      return await refresh(scope);
    } catch (error) {
      if (cached != null && isOfflineEligibleError(error)) return cached;
      rethrow;
    }
  }

  StudentMoreData _decode(Map<String, dynamic> json, DateTime syncedAt,
          {bool offline = false}) =>
      StudentMoreData(
        profile: StudentProfile.fromJson(
            Map<String, dynamic>.from(json['profile'] as Map)),
        schools: (json['schools'] as List? ?? const [])
            .whereType<Map>()
            .map((item) =>
                StudentSchoolSummary.fromJson(Map<String, dynamic>.from(item)))
            .toList(),
        history: (json['history'] as List? ?? const [])
            .whereType<Map>()
            .map((item) => StudentAcademicHistoryItem.fromJson(
                Map<String, dynamic>.from(item)))
            .toList(),
        lastUpdated: syncedAt,
        offline: offline,
      );
}
