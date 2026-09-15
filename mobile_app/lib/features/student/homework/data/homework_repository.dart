import '../../../../core/local_database/app_database.dart';
import '../../../../core/offline/offline_error_policy.dart';
import '../domain/homework_models.dart';
import 'homework_local_data_source.dart';
import 'homework_remote_data_source.dart';

class HomeworkListData {
  const HomeworkListData(this.items, this.lastUpdated, {this.offline = false});
  final List<StudentHomework> items;
  final DateTime lastUpdated;
  final bool offline;

  HomeworkListData withPersistedDraft(int homeworkId) => HomeworkListData(
        items
            .map((item) => item.id == homeworkId &&
                    item.requiresElectronicSubmission &&
                    item.completionStatus == 'not_started'
                ? item.withCompletionStatus('draft')
                : item)
            .toList(),
        lastUpdated,
        offline: offline,
      );
}

class HomeworkDetailData {
  const HomeworkDetailData(this.homework, this.draft, this.lastUpdated,
      {this.offline = false});
  final StudentHomework homework;
  final HomeworkLocalDraft draft;
  final DateTime lastUpdated;
  final bool offline;
}

class StudentHomeworkRepository {
  StudentHomeworkRepository(this.remote, this.local);
  final HomeworkRemoteDataSource remote;
  final HomeworkLocalDataSource local;

  Future<HomeworkListData?> readList(CacheScope scope) async {
    final rows = await local.list(scope);
    if (rows.isEmpty) return null;
    final items = await _projectPersistedDrafts(
      scope,
      rows.map(StudentHomework.fromJson).toList(),
    );
    return HomeworkListData(
      items,
      _latest(rows),
      offline: true,
    );
  }

  Future<HomeworkListData> refreshList(CacheScope scope) async {
    final rows = await remote.list();
    final now = DateTime.now().toUtc();
    for (final row in rows) {
      row['_mobile_last_synced_at'] = now.toIso8601String();
    }
    await local.replaceList(scope, rows, now);
    final items = await _projectPersistedDrafts(
      scope,
      rows.map(StudentHomework.fromJson).toList(),
    );
    return HomeworkListData(items, now);
  }

  Future<HomeworkDetailData> loadDetail(
      CacheScope scope, int homeworkId) async {
    final draft = await local.readDraft(scope, homeworkId);
    try {
      final row = await remote.detail(homeworkId);
      final submission = await remote.submission(homeworkId);
      row['_mobile_submission'] = submission;
      final now = DateTime.now().toUtc();
      row['_mobile_last_synced_at'] = now.toIso8601String();
      await local.putDetail(scope, row, now);
      return HomeworkDetailData(_parse(row), draft, now);
    } catch (error) {
      if (!isOfflineEligibleError(error)) rethrow;
      final row = await local.detail(scope, homeworkId);
      if (row == null) rethrow;
      return HomeworkDetailData(_parse(row), draft, _latest([row]),
          offline: true);
    }
  }

  Future<void> saveDraft(
          CacheScope scope, int homeworkId, HomeworkLocalDraft draft) =>
      local.saveDraft(scope, homeworkId, draft);

  Future<HomeworkDetailData> uploadSubmissionAttachments(
      CacheScope scope, HomeworkDetailData current, List<String> paths) async {
    if (paths.isEmpty) return current;
    var submission = current.homework.submission;
    submission ??= HomeworkSubmissionModel.fromJson(
        await remote.createSubmission(current.homework.id));
    await remote.uploadSubmissionAttachments(submission.id, paths);
    return loadDetail(scope, current.homework.id);
  }

  Future<HomeworkDetailData> deleteSubmissionAttachment(
      CacheScope scope,
      HomeworkDetailData current,
      HomeworkAttachment attachment) async {
    final submission = current.homework.submission;
    if (submission == null) return current;
    await remote.deleteSubmissionAttachment(submission.id, attachment.id);
    return loadDetail(scope, current.homework.id);
  }

  Future<HomeworkDetailData> submit(
      CacheScope scope, HomeworkDetailData current) async {
    var submission = current.homework.submission;
    submission ??= HomeworkSubmissionModel.fromJson(
        await remote.createSubmission(current.homework.id));
    if (!current.homework.requiresElectronicSubmission) {
      throw StateError('This homework does not require electronic submission.');
    }
    var submissionId = submission.id;
    if (current.homework.acceptsText) {
      final updated = HomeworkSubmissionModel.fromJson(
        await remote.updateAnswer(submission.id, current.draft.answer),
      );
      submissionId = updated.id;
    }
    await remote.finalSubmit(submissionId);
    await local.deleteDraft(scope, current.homework.id);
    return loadDetail(scope, current.homework.id);
  }

  Future<String> downloadAttachment(HomeworkAttachment attachment) =>
      remote.downloadAttachment(attachment.url, attachment.name);

  StudentHomework _parse(Map<String, dynamic> row) {
    final rawSubmission = row['_mobile_submission'];
    return StudentHomework.fromJson(row).withSubmission(rawSubmission is Map
        ? HomeworkSubmissionModel.fromJson(
            Map<String, dynamic>.from(rawSubmission))
        : null);
  }

  Future<List<StudentHomework>> _projectPersistedDrafts(
      CacheScope scope, List<StudentHomework> items) async {
    return Future.wait(items.map((item) async {
      if (!item.requiresElectronicSubmission ||
          item.completionStatus != 'not_started') {
        return item;
      }
      final draft = await local.readDraft(scope, item.id);
      return draft.updatedAt == null
          ? item
          : item.withCompletionStatus('draft');
    }));
  }
}

DateTime _latest(List<Map<String, dynamic>> rows) => rows
    .map((row) =>
        DateTime.tryParse(row['_mobile_last_synced_at']?.toString() ?? '') ??
        DateTime.fromMillisecondsSinceEpoch(0, isUtc: true))
    .reduce((a, b) => a.isAfter(b) ? a : b);
