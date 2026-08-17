import 'dart:convert';

import 'package:dio/dio.dart';

import '../../../../core/local_database/app_database.dart';
import '../../../../core/offline/offline_error_policy.dart';
import '../domain/result_models.dart';

class StudentResultsData {
  const StudentResultsData(this.items, this.lastUpdated, {this.offline = false});
  final List<StudentResult> items;
  final DateTime lastUpdated;
  final bool offline;

  List<String> get terms =>
      items.map((e) => e.academicTermName).where((e) => e.isNotEmpty).toSet().toList();
  List<String> get subjects =>
      items.map((e) => e.subject).where((e) => e.isNotEmpty).toSet().toList();
}

class StudentResultsRepository {
  StudentResultsRepository(this.dio, this.db);
  final Dio dio;
  final AppDatabase db;

  Future<StudentResultsData?> read(CacheScope scope) async {
    final rows = await db.readStudentResults(scope);
    if (rows.isEmpty) return null;
    return StudentResultsData(
      rows.map((row) => StudentResult.fromJson(
        Map<String, dynamic>.from(jsonDecode(row.payloadJson) as Map))).toList(),
      rows.map((e) => e.lastSyncedAt).reduce((a, b) => a.isAfter(b) ? a : b),
      offline: true,
    );
  }

  Future<StudentResultsData> refresh(CacheScope scope) async {
    final response = await dio.get('students/me/results/');
    final raw = response.data;
    final list = raw is Map ? raw['results'] : raw;
    final rows = (list as List? ?? const [])
        .map((e) => Map<String, Object?>.from(e as Map))
        .where((e) => e['is_published'] == true)
        .toList();
    final now = DateTime.now().toUtc();
    await db.replaceStudentResults(scope, rows, now);
    return StudentResultsData(rows.map(StudentResult.fromJson).toList(), now);
  }

  Future<StudentResultsData> load(CacheScope scope) async {
    final cached = await read(scope);
    try {
      return await refresh(scope);
    } catch (error) {
      if (cached != null && isOfflineEligibleError(error)) return cached;
      rethrow;
    }
  }
}
