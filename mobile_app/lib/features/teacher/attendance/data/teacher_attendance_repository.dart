import 'package:dio/dio.dart';

import '../domain/teacher_attendance_models.dart';

class TeacherAttendanceRepository {
  const TeacherAttendanceRepository(this._dio);

  final Dio _dio;

  Future<TeacherAttendanceSaveResult> saveBulk({
    required int assignmentId,
    required String date,
    required List<TeacherAttendanceDraft> changes,
  }) async {
    final response = await _dio.post<Map<String, dynamic>>(
      'attendance/bulk/',
      data: {
        'teacher_assignment_id': assignmentId,
        'attendance_date': date,
        'students': changes.map((item) => item.toRequestJson()).toList(),
      },
    );
    return TeacherAttendanceSaveResult.fromJson(response.data!);
  }
}
