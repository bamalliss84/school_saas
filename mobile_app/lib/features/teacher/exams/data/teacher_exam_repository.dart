import 'package:dio/dio.dart';

import '../domain/teacher_exam_models.dart';

class TeacherExamRepository {
  const TeacherExamRepository(this._dio);

  final Dio _dio;

  Future<List<TeacherExamType>> getExamTypes() async {
    final response = await _dio.get<dynamic>(
      'exam-types/',
      queryParameters: {'is_active': true, 'page_size': 100},
    );
    return _rows(response.data)
        .map((row) => TeacherExamType.fromJson(row))
        .toList(growable: false);
  }

  Future<List<TeacherExam>> getExams({int? assignmentId}) async {
    final response = await _dio.get<dynamic>(
      'exams/',
      queryParameters: {
        if (assignmentId != null) 'teacher_assignment_id': assignmentId,
        'page_size': 100,
      },
    );
    return _rows(response.data)
        .map((row) => TeacherExam.fromJson(row))
        .toList(growable: false);
  }

  Future<TeacherExam> updateExam(TeacherExam exam) async {
    final response = await _dio.patch<Map<String, dynamic>>(
      'exams/${exam.id}/',
      data: {
        'academic_year': exam.academicYearId,
        'academic_term': exam.academicTermId,
        'teacher_assignment': exam.assignmentId,
        'exam_type': exam.examTypeId,
        'title': exam.title,
        'exam_date': _apiDate(exam.examDate),
        'total_marks': exam.totalMarks,
        'notes': exam.notes,
      },
    );
    return TeacherExam.fromJson(response.data!);
  }

  Future<void> deleteExam(int examId) async {
    await _dio.delete<void>('exams/$examId/');
  }

  Future<List<TeacherExamResult>> getResults(int examId) async {
    final response = await _dio.get<dynamic>(
      'exam-results/',
      queryParameters: {'exam_id': examId, 'page_size': 200},
    );
    return _rows(response.data)
        .map((row) => TeacherExamResult.fromJson(row))
        .toList(growable: false);
  }

  Future<Map<String, dynamic>> getSummary(int examId) async {
    final response = await _dio.get<Map<String, dynamic>>(
      'exam-results/reports/exam/$examId/summary/',
    );
    return Map<String, dynamic>.from(
      response.data?['statistics'] as Map? ?? const {},
    );
  }

  Future<List<TeacherExamResult>> saveResults(
    int examId,
    List<TeacherExamResultDraft> drafts,
  ) async {
    final response = await _dio.post<dynamic>(
      'exam-results/bulk/',
      data: {
        'exam': examId,
        'results': drafts.map((draft) => draft.toJson()).toList(),
      },
    );
    final rows = response.data as List? ?? const [];
    return rows
        .map((row) => TeacherExamResult.fromJson(
              Map<String, dynamic>.from(row as Map),
            ))
        .toList(growable: false);
  }

  Future<TeacherExamResult> submitResult(int resultId) async {
    final response = await _dio.post<Map<String, dynamic>>(
      'exam-results/$resultId/submit/',
      data: const <String, dynamic>{},
    );
    return TeacherExamResult.fromJson(response.data!);
  }
}

List<Map<String, dynamic>> _rows(dynamic payload) {
  final raw = payload is Map ? payload['results'] : payload;
  return (raw as List? ?? const [])
      .map((row) => Map<String, dynamic>.from(row as Map))
      .toList(growable: false);
}

String _apiDate(DateTime value) =>
    '${value.year.toString().padLeft(4, '0')}-${value.month.toString().padLeft(2, '0')}-${value.day.toString().padLeft(2, '0')}';
