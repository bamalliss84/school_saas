import 'package:dio/dio.dart';
import 'package:path_provider/path_provider.dart';

abstract interface class HomeworkRemoteDataSource {
  Future<List<Map<String, dynamic>>> list();
  Future<Map<String, dynamic>> detail(int homeworkId);
  Future<Map<String, dynamic>?> submission(int homeworkId);
  Future<Map<String, dynamic>> createSubmission(int homeworkId);
  Future<Map<String, dynamic>> updateAnswer(int submissionId, String answer);
  Future<Map<String, dynamic>> finalSubmit(int submissionId);
  Future<String> downloadAttachment(String url, String fileName);
}

class DioHomeworkRemoteDataSource implements HomeworkRemoteDataSource {
  DioHomeworkRemoteDataSource(this._dio);
  final Dio _dio;

  @override
  Future<List<Map<String, dynamic>>> list() async {
    final response = await _dio.get<Map<String, dynamic>>(
      'students/me/homework/',
      queryParameters: const {'ordering': 'due_date'},
    );
    return _results(response.data);
  }

  @override
  Future<Map<String, dynamic>> detail(int homeworkId) async =>
      Map<String, dynamic>.from(
          (await _dio.get<Map<String, dynamic>>('homework/$homeworkId/'))
              .data!);

  @override
  Future<Map<String, dynamic>?> submission(int homeworkId) async {
    final response = await _dio.get<Map<String, dynamic>>(
      'homework-submissions/',
      queryParameters: {'homework_id': homeworkId},
    );
    final rows = _results(response.data);
    return rows.isEmpty ? null : rows.first;
  }

  @override
  Future<Map<String, dynamic>> createSubmission(int homeworkId) async =>
      Map<String, dynamic>.from((await _dio.post<Map<String, dynamic>>(
        'homework/$homeworkId/submission/',
      ))
          .data!);

  @override
  Future<Map<String, dynamic>> updateAnswer(
          int submissionId, String answer) async =>
      Map<String, dynamic>.from((await _dio.patch<Map<String, dynamic>>(
        'homework-submissions/$submissionId/',
        data: {'answer': answer},
      ))
          .data!);

  @override
  Future<Map<String, dynamic>> finalSubmit(int submissionId) async =>
      Map<String, dynamic>.from((await _dio.post<Map<String, dynamic>>(
        'homework-submissions/$submissionId/final-submit/',
      ))
          .data!);

  @override
  Future<String> downloadAttachment(String url, String fileName) async {
    final directory = await getApplicationDocumentsDirectory();
    final safeName = fileName.replaceAll(RegExp(r'[^A-Za-z0-9._-]'), '_');
    final path = '${directory.path}/homework_$safeName';
    await _dio.download(url, path);
    return path;
  }
}

List<Map<String, dynamic>> _results(Map<String, dynamic>? data) =>
    (data?['results'] as List? ?? const [])
        .map((item) => Map<String, dynamic>.from(item as Map))
        .toList();
