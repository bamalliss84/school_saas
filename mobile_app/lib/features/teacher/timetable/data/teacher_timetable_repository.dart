import 'dart:convert';

import 'package:dio/dio.dart';

import '../../../../core/local_database/app_database.dart';
import '../domain/teacher_timetable_models.dart';

class TeacherTimetableRepository {
  TeacherTimetableRepository(this._dio, this._database);

  final Dio _dio;
  final AppDatabase _database;

  static const _datasetKeys = {
    'today': 'teacher_today',
    'week': 'teacher_week',
    'current': 'teacher_current',
    'next': 'teacher_next',
  };

  Future<TeacherTimetableData?> readCache(CacheScope scope) async {
    final payloads = <String, Map<String, dynamic>>{};
    final syncedAt = <DateTime>[];
    for (final item in _datasetKeys.entries) {
      final row = await _database.readTimetableDataset(scope, item.value);
      if (row == null) return null;
      payloads[item.key] =
          Map<String, dynamic>.from(jsonDecode(row.payloadJson) as Map);
      syncedAt.add(row.lastSyncedAt);
    }
    final oldest = syncedAt.reduce((a, b) => a.isBefore(b) ? a : b);
    return _parse(payloads, oldest, true);
  }

  Future<TeacherTimetableData> refresh(CacheScope scope) async {
    final names = _datasetKeys.keys.toList(growable: false);
    final responses = await Future.wait(names.map(_fetch));
    final payloads = <String, Map<String, dynamic>>{
      for (var index = 0; index < names.length; index++)
        names[index]: responses[index],
    };
    final syncedAt = DateTime.now().toUtc();
    final parsed = _parse(payloads, syncedAt, false);
    await _database.replaceTimetableDatasets(
      scope,
      {
        for (final item in _datasetKeys.entries)
          item.value: payloads[item.key]!.cast<String, Object?>(),
      },
      syncedAt,
    );
    return parsed;
  }

  Future<Map<String, dynamic>> _fetch(String endpoint) async =>
      (await _dio.get<Map<String, dynamic>>('timetable/$endpoint/')).data!;

  TeacherTimetableData _parse(
    Map<String, Map<String, dynamic>> payloads,
    DateTime updatedAt,
    bool fromCache,
  ) =>
      TeacherTimetableData(
        today: TeacherTodayTimetable.fromJson(payloads['today']!),
        week: TeacherWeekTimetable.fromJson(payloads['week']!),
        current:
            datedTeacherLesson(payloads['current']!, 'current_entry'),
        next: datedTeacherLesson(payloads['next']!, 'next_entry'),
        lastUpdated: updatedAt,
        fromCache: fromCache,
      );
}
