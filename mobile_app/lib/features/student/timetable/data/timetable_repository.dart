import 'dart:convert';
import 'package:dio/dio.dart';
import '../../../../core/local_database/app_database.dart';
import '../domain/timetable_models.dart';

class StudentTimetableData {
  const StudentTimetableData(
      {required this.today,
      required this.week,
      this.current,
      this.next,
      required this.lastUpdated,
      required this.fromCache});
  final TodayTimetable today;
  final WeekTimetable week;
  final TimetableEntryModel? current;
  final TimetableEntryModel? next;
  final DateTime lastUpdated;
  final bool fromCache;
}

class StudentTimetableRepository {
  StudentTimetableRepository(this._dio, this._database,
      {Future<Map<String, dynamic>> Function(String key)? fetcher})
      : _fetcher = fetcher;
  final Dio _dio;
  final AppDatabase _database;
  final Future<Map<String, dynamic>> Function(String key)? _fetcher;
  static const keys = ['today', 'week', 'current', 'next'];

  Future<StudentTimetableData?> readCache(CacheScope scope) async {
    final rows = <String, CachedTimetableDataset>{};
    for (final key in keys) {
      final row = await _database.readTimetableDataset(scope, key);
      if (row == null) return null;
      rows[key] = row;
    }
    return _parse(
        rows.map((key, value) => MapEntry(key,
            Map<String, dynamic>.from(jsonDecode(value.payloadJson) as Map))),
        rows.values
            .map((e) => e.lastSyncedAt)
            .reduce((a, b) => a.isBefore(b) ? a : b),
        true);
  }

  Future<StudentTimetableData> refresh(CacheScope scope) async {
    final responses = await Future.wait<Map<String, dynamic>>(keys.map(_fetch));
    final payloads = <String, Map<String, dynamic>>{
      for (var i = 0; i < keys.length; i++) keys[i]: responses[i],
    };
    final now = DateTime.now().toUtc();
    final parsed = _parse(payloads, now, false);
    await _database.replaceTimetableDatasets(
        scope,
        payloads
            .map((key, value) => MapEntry(key, value.cast<String, Object?>())),
        now);
    return parsed;
  }

  Future<Map<String, dynamic>> _fetch(String key) async {
    final custom = _fetcher;
    if (custom != null) return custom(key);
    return (await _dio.get<Map<String, dynamic>>('timetable/$key/')).data!;
  }

  StudentTimetableData _parse(Map<String, Map<String, dynamic>> values,
          DateTime updated, bool cached) =>
      StudentTimetableData(
        today: TodayTimetable.fromJson(values['today']!),
        week: WeekTimetable.fromJson(values['week']!),
        current: nullableEntry(values['current']!, 'current_entry'),
        next: nullableEntry(values['next']!, 'next_entry'),
        lastUpdated: updated,
        fromCache: cached,
      );
}
