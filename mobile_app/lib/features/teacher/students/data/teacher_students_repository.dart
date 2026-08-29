import 'package:dio/dio.dart';

import '../domain/teacher_students_models.dart';

class TeacherStudentsRepository {
  const TeacherStudentsRepository(this._dio);

  final Dio _dio;

  Future<List<TeacherAssignmentSummary>> getAssignments() async {
    final assignments = <TeacherAssignmentSummary>[];
    var page = 1;
    var totalPages = 1;
    do {
      final response = await _dio.get<dynamic>(
        'teachers/me/assignments/',
        queryParameters: {'page': page, 'page_size': 100},
      );
      final raw = response.data;
      final rows = raw is Map ? raw['results'] : raw;
      assignments.addAll(
        (rows as List? ?? const []).map((item) =>
            TeacherAssignmentSummary.fromJson(
              Map<String, dynamic>.from(item as Map),
            )),
      );
      totalPages = raw is Map
          ? (raw['total_pages'] as num?)?.toInt() ?? 1
          : 1;
      page += 1;
    } while (page <= totalPages);
    return List.unmodifiable(assignments);
  }

  Future<TeacherAssignmentRoster> getRoster({
    required int assignmentId,
    required String date,
  }) async {
    final response = await _dio.get<Map<String, dynamic>>(
      'teachers/me/assignments/$assignmentId/students/',
      queryParameters: {'date': date},
    );
    return TeacherAssignmentRoster.fromJson(response.data!);
  }
}
