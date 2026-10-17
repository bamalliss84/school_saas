import 'dart:convert';

import 'package:dio/dio.dart';

import '../../../../core/local_database/app_database.dart';
import '../../../../core/offline/offline_error_policy.dart';
import '../domain/parent_result_models.dart';

class ParentResultsData {
  const ParentResultsData(this.items, this.lastUpdated, {this.offline = false});
  final List<ParentResult> items;
  final DateTime lastUpdated;
  final bool offline;
}

class ParentResultsRepository {
  ParentResultsRepository(this.dio, this.database);
  final Dio dio;
  final AppDatabase database;

  String _resource(int childId, int enrollmentId) =>
      'parent_results_v1_child_${childId}_enrollment_$enrollmentId';

  Future<ParentResultsData?> read(
    CacheScope scope, {
    required int childId,
    required int enrollmentId,
  }) async {
    final rows = await database.readContexts(scope);
    for (final row in rows) {
      if (row.resourceId == _resource(childId, enrollmentId)) {
        final payload = Map<String, dynamic>.from(
            jsonDecode(row.payloadJson) as Map);
        return ParentResultsData(
          (payload['items'] as List? ?? const [])
              .whereType<Map>()
              .map((item) => ParentResult.fromJson(
                  Map<String, dynamic>.from(item)))
              .toList(growable: false),
          row.lastSyncedAt,
          offline: true,
        );
      }
    }
    return null;
  }

  Future<ParentResultsData> load(
    CacheScope scope, {
    required int childId,
    required int enrollmentId,
  }) async {
    final cached = await read(
      scope,
      childId: childId,
      enrollmentId: enrollmentId,
    );
    try {
      return await refresh(
        scope,
        childId: childId,
        enrollmentId: enrollmentId,
      );
    } catch (error) {
      if (cached != null && isOfflineEligibleError(error)) return cached;
      rethrow;
    }
  }

  Future<ParentResultsData> refresh(
    CacheScope scope, {
    required int childId,
    required int enrollmentId,
  }) async {
    final response = await dio.get<dynamic>(
        'exam-results/reports/student/$childId/transcript/');
    final raw = response.data is Map ? response.data['results'] : response.data;
    final rows = (raw as List? ?? const [])
        .whereType<Map>()
        .map((item) => Map<String, dynamic>.from(item))
        .where((item) =>
            item['student_enrollment'] == enrollmentId &&
            item['workflow_status'] == 'approved' &&
            item['is_published'] == true)
        .toList(growable: false);
    final now = DateTime.now().toUtc();
    await database.putContext(
      scope: scope,
      resourceId: _resource(childId, enrollmentId),
      payload: {'items': rows},
      isHistorical: false,
      syncedAt: now,
    );
    return ParentResultsData(
      rows.map(ParentResult.fromJson).toList(growable: false),
      now,
    );
  }
}
