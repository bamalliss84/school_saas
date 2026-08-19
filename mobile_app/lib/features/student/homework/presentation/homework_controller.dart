import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../../core/local_database/app_database.dart';
import '../../../../core/offline/offline_error_policy.dart';
import '../data/homework_repository.dart';
import '../domain/homework_models.dart';

sealed class HomeworkState {
  const HomeworkState();
}

class HomeworkLoading extends HomeworkState {
  const HomeworkLoading();
}

class HomeworkFailure extends HomeworkState {
  const HomeworkFailure(this.message);
  final String message;
}

sealed class HomeworkDetailState {
  const HomeworkDetailState();
}

class HomeworkDetailClosed extends HomeworkDetailState {
  const HomeworkDetailClosed();
}

class HomeworkDetailLoading extends HomeworkDetailState {
  const HomeworkDetailLoading();
}

class HomeworkDetailFailure extends HomeworkDetailState {
  const HomeworkDetailFailure(this.message);
  final String message;
}

class HomeworkDetailReady extends HomeworkDetailState {
  const HomeworkDetailReady(this.data, {this.submitting = false});
  final HomeworkDetailData data;
  final bool submitting;
}

class HomeworkReady extends HomeworkState {
  const HomeworkReady(this.list,
      {this.detail = const HomeworkDetailClosed(), this.filter});
  final HomeworkListData list;
  final HomeworkDetailState detail;
  final String? filter;

  List<StudentHomework> get visible => filter == null
      ? list.items
      : list.items.where((item) => item.completionStatus == filter).toList();

  HomeworkReady copyWith({
    HomeworkListData? list,
    HomeworkDetailState? detail,
    String? filter,
    bool clearFilter = false,
  }) =>
      HomeworkReady(
        list ?? this.list,
        detail: detail ?? this.detail,
        filter: clearFilter ? null : filter ?? this.filter,
      );
}

class HomeworkController extends StateNotifier<HomeworkState> {
  HomeworkController(this.repository, this.scope)
      : super(const HomeworkLoading());

  final StudentHomeworkRepository repository;
  final CacheScope scope;

  Future<void> load() async {
    final cached = await repository.readList(scope);
    if (cached != null) state = HomeworkReady(cached);
    try {
      final fresh = await repository.refreshList(scope);
      final current = state;
      state = current is HomeworkReady
          ? current.copyWith(list: fresh)
          : HomeworkReady(fresh);
    } catch (error) {
      if (cached != null && isOfflineEligibleError(error)) {
        state = HomeworkReady(cached);
      } else {
        state = HomeworkFailure(failureMessage(
            error, 'تعذر تحميل الواجبات ولا توجد بيانات محفوظة'));
      }
    }
  }

  Future<void> refresh() => load();

  void selectFilter(String? value) {
    final current = state;
    if (current is HomeworkReady) {
      state = value == null
          ? current.copyWith(clearFilter: true)
          : current.copyWith(filter: value);
    }
  }

  Future<void> open(int homeworkId) async {
    final current = state;
    if (current is! HomeworkReady) return;
    state = current.copyWith(detail: const HomeworkDetailLoading());
    try {
      final detail = await repository.loadDetail(scope, homeworkId);
      state = (state as HomeworkReady)
          .copyWith(detail: HomeworkDetailReady(detail));
    } catch (error) {
      state = (state as HomeworkReady).copyWith(
          detail: HomeworkDetailFailure(failureMessage(
              error, 'تعذر فتح الواجب ولا توجد نسخة محفوظة')));
    }
  }

  void closeDetail() {
    final current = state;
    if (current is HomeworkReady) {
      state = current.copyWith(detail: const HomeworkDetailClosed());
    }
  }

  Future<void> saveDraft(HomeworkLocalDraft draft) async {
    final current = state;
    if (current is! HomeworkReady || current.detail is! HomeworkDetailReady) {
      return;
    }
    final detail = (current.detail as HomeworkDetailReady).data;
    await repository.saveDraft(scope, detail.homework.id, draft);
    state = current.copyWith(
      detail: HomeworkDetailReady(HomeworkDetailData(
        detail.homework,
        HomeworkLocalDraft(
          answer: draft.answer,
          studentNote: draft.studentNote,
          localFiles: draft.localFiles,
          updatedAt: DateTime.now(),
        ),
        detail.lastUpdated,
        offline: detail.offline,
      )),
    );
  }

  Future<bool> submit() async {
    final current = state;
    if (current is! HomeworkReady || current.detail is! HomeworkDetailReady) {
      return false;
    }
    final ready = current.detail as HomeworkDetailReady;
    if (ready.data.offline) return false;
    state = current.copyWith(
        detail: HomeworkDetailReady(ready.data, submitting: true));
    try {
      final updated = await repository.submit(scope, ready.data);
      state = (state as HomeworkReady)
          .copyWith(detail: HomeworkDetailReady(updated));
      await load();
      await open(updated.homework.id);
      return true;
    } catch (_) {
      state = (state as HomeworkReady)
          .copyWith(detail: HomeworkDetailReady(ready.data));
      return false;
    }
  }

  Future<bool> uploadAttachments(List<String> paths) async {
    final current = state;
    if (current is! HomeworkReady ||
        current.detail is! HomeworkDetailReady ||
        paths.isEmpty) {
      return false;
    }
    final ready = current.detail as HomeworkDetailReady;
    if (ready.data.offline || !ready.data.homework.canEditDraft) return false;
    state = current.copyWith(
        detail: HomeworkDetailReady(ready.data, submitting: true));
    try {
      final updated = await repository.uploadSubmissionAttachments(
          scope, ready.data, paths);
      state = (state as HomeworkReady)
          .copyWith(detail: HomeworkDetailReady(updated));
      return true;
    } catch (_) {
      state = (state as HomeworkReady)
          .copyWith(detail: HomeworkDetailReady(ready.data));
      return false;
    }
  }

  Future<bool> deleteAttachment(HomeworkAttachment attachment) async {
    final current = state;
    if (current is! HomeworkReady ||
        current.detail is! HomeworkDetailReady) {
      return false;
    }
    final ready = current.detail as HomeworkDetailReady;
    if (ready.data.offline || !ready.data.homework.canEditDraft) return false;
    try {
      final updated = await repository.deleteSubmissionAttachment(
          scope, ready.data, attachment);
      state = (state as HomeworkReady)
          .copyWith(detail: HomeworkDetailReady(updated));
      return true;
    } catch (_) {
      return false;
    }
  }

  Future<String> download(HomeworkAttachment attachment) =>
      repository.downloadAttachment(attachment);
}
