import 'dart:convert';

import 'package:dio/dio.dart';

import '../../../../core/local_database/app_database.dart';
import '../../../../core/offline/offline_error_policy.dart';
import '../domain/parent_homework_models.dart';

class ParentHomeworkListData {
  const ParentHomeworkListData(
    this.items,
    this.lastUpdated, {
    this.offline = false,
  });
  final List<ParentHomework> items;
  final DateTime lastUpdated;
  final bool offline;
}

class ParentHomeworkDetailData {
  const ParentHomeworkDetailData(
    this.homework,
    this.submission,
    this.lastUpdated, {
    this.offline = false,
  });
  final ParentHomework homework;
  final ParentHomeworkSubmission? submission;
  final DateTime lastUpdated;
  final bool offline;
}

class ParentHomeworkRepository {
  ParentHomeworkRepository(this.dio, this.database);
  final Dio dio;
  final AppDatabase database;

  String _listResource(int childId) => 'parent_homework_v1_child_$childId';
  String _detailResource(int childId, int homeworkId) =>
      'parent_homework_detail_v1_child_${childId}_homework_$homeworkId';

  Future<ParentHomeworkListData?> readList(
      CacheScope scope, int childId) async {
    final row = await _read(scope, _listResource(childId));
    if (row == null) return null;
    final payload =
        Map<String, dynamic>.from(jsonDecode(row.payloadJson) as Map);
    return ParentHomeworkListData(
      _rows(payload).map(ParentHomework.fromJson).toList(growable: false),
      row.lastSyncedAt,
      offline: true,
    );
  }

  Future<ParentHomeworkListData> loadList(CacheScope scope, int childId) async {
    final cached = await readList(scope, childId);
    try {
      return await refreshList(scope, childId);
    } catch (error) {
      if (cached != null && isOfflineEligibleError(error)) return cached;
      rethrow;
    }
  }

  Future<ParentHomeworkListData> refreshList(
      CacheScope scope, int childId) async {
    final academicYearId = int.tryParse(scope.academicYearKey);
    final response = await dio.get<dynamic>(
      'parents/me/children/$childId/homework/',
      queryParameters: {
        if (academicYearId != null) 'academic_year_id': academicYearId,
        'ordering': 'due_date',
      },
    );
    final payload = Map<String, dynamic>.from(response.data as Map);
    final now = DateTime.now().toUtc();
    await _write(scope, _listResource(childId), payload, now);
    return ParentHomeworkListData(
      _rows(payload).map(ParentHomework.fromJson).toList(growable: false),
      now,
    );
  }

  Future<ParentHomeworkDetailData?> readDetail(
    CacheScope scope,
    int childId,
    int homeworkId,
  ) async {
    final row = await _read(scope, _detailResource(childId, homeworkId));
    if (row == null) return null;
    final payload =
        Map<String, dynamic>.from(jsonDecode(row.payloadJson) as Map);
    final rawSubmission = payload['submission'];
    return ParentHomeworkDetailData(
      ParentHomework.fromJson(
          Map<String, dynamic>.from(payload['homework'] as Map)),
      rawSubmission is Map
          ? ParentHomeworkSubmission.fromJson(
              Map<String, dynamic>.from(rawSubmission))
          : null,
      row.lastSyncedAt,
      offline: true,
    );
  }

  Future<ParentHomeworkDetailData> loadDetail(
    CacheScope scope,
    int childId,
    ParentHomework homework,
  ) async {
    final cached = await readDetail(scope, childId, homework.id);
    try {
      return await refreshDetail(scope, childId, homework);
    } catch (error) {
      if (cached != null && isOfflineEligibleError(error)) return cached;
      rethrow;
    }
  }

  Future<ParentHomeworkDetailData> refreshDetail(
    CacheScope scope,
    int childId,
    ParentHomework homework,
  ) async {
    final response = await dio.get<dynamic>(
      'homework-submissions/',
      queryParameters: {
        'homework_id': homework.id,
        'student_id': childId,
      },
    );
    final payload = Map<String, dynamic>.from(response.data as Map);
    final submissions = _rows(payload);
    final submission = submissions.isEmpty
        ? null
        : ParentHomeworkSubmission.fromJson(submissions.first);
    final now = DateTime.now().toUtc();
    await _write(
      scope,
      _detailResource(childId, homework.id),
      {
        'homework': homework.toJson(),
        'submission': submission?.toJson(),
      },
      now,
    );
    return ParentHomeworkDetailData(homework, submission, now);
  }

  Future<CachedContext?> _read(CacheScope scope, String resource) async {
    for (final row in await database.readContexts(scope)) {
      if (row.resourceId == resource) return row;
    }
    return null;
  }

  Future<void> _write(
    CacheScope scope,
    String resource,
    Map<String, dynamic> payload,
    DateTime syncedAt,
  ) =>
      database.putContext(
        scope: scope,
        resourceId: resource,
        payload: payload,
        isHistorical: false,
        syncedAt: syncedAt,
      );
}

List<Map<String, dynamic>> _rows(Map<String, dynamic> payload) =>
    (payload['results'] as List? ?? const [])
        .whereType<Map>()
        .map((item) => Map<String, dynamic>.from(item))
        .toList(growable: false);
