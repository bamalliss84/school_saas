import 'dart:convert';

import '../../../../core/local_database/app_database.dart';
import '../domain/homework_models.dart';

class HomeworkLocalDataSource {
  HomeworkLocalDataSource(this._database);
  final AppDatabase _database;

  Future<List<Map<String, dynamic>>> list(CacheScope scope) async =>
      (await _database.readHomeworkItems(scope))
          .map((row) => Map<String, dynamic>.from(jsonDecode(row.payloadJson)))
          .toList();

  Future<Map<String, dynamic>?> detail(CacheScope scope, int homeworkId) async {
    final row = await _database.readHomeworkItem(scope, homeworkId);
    return row == null
        ? null
        : Map<String, dynamic>.from(jsonDecode(row.payloadJson));
  }

  Future<void> replaceList(CacheScope scope, List<Map<String, dynamic>> rows,
          DateTime syncedAt) =>
      _database.replaceHomeworkItems(
          scope, rows.cast<Map<String, Object?>>(), syncedAt);

  Future<void> putDetail(
          CacheScope scope, Map<String, dynamic> row, DateTime syncedAt) =>
      _database.putHomeworkItem(scope, row.cast<String, Object?>(), syncedAt);

  Future<HomeworkLocalDraft> readDraft(CacheScope scope, int homeworkId) async {
    final row = await _database.readHomeworkDraft(scope, homeworkId);
    if (row == null) return const HomeworkLocalDraft();
    return HomeworkLocalDraft(
      answer: row.answer,
      studentNote: row.studentNote,
      localFiles: (jsonDecode(row.localFilesJson) as List).cast<String>(),
      updatedAt: row.updatedAt,
    );
  }

  Future<void> saveDraft(
          CacheScope scope, int homeworkId, HomeworkLocalDraft draft) =>
      _database.saveHomeworkDraft(
        scope: scope,
        homeworkId: homeworkId,
        answer: draft.answer,
        studentNote: draft.studentNote,
        localFiles: draft.localFiles,
      );

  Future<void> deleteDraft(CacheScope scope, int homeworkId) =>
      _database.deleteHomeworkDraft(scope, homeworkId);
}
