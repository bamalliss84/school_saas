import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../../app/app.dart';
import '../../../../core/local_database/app_database.dart';
import '../../../../core/offline/offline_error_policy.dart';
import '../data/teacher_timetable_repository.dart';
import '../domain/teacher_timetable_models.dart';

sealed class TeacherTimetableState {
  const TeacherTimetableState();
}

class TeacherTimetableLoading extends TeacherTimetableState {
  const TeacherTimetableLoading();
}

class TeacherTimetableReady extends TeacherTimetableState {
  const TeacherTimetableReady(
    this.data, {
    this.offline = false,
    this.refreshing = false,
  });

  final TeacherTimetableData data;
  final bool offline;
  final bool refreshing;
}

class TeacherTimetableFailure extends TeacherTimetableState {
  const TeacherTimetableFailure(this.message);
  final String message;
}

class TeacherTimetableController
    extends StateNotifier<TeacherTimetableState> {
  TeacherTimetableController(this.repository, this.scope)
      : super(const TeacherTimetableLoading());

  final TeacherTimetableRepository repository;
  final CacheScope scope;

  Future<void> load() async {
    final cached = await repository.readCache(scope);
    if (cached != null) {
      state = TeacherTimetableReady(cached, refreshing: true);
    }
    try {
      state = TeacherTimetableReady(await repository.refresh(scope));
    } catch (error) {
      if (cached != null && isOfflineEligibleError(error)) {
        state = TeacherTimetableReady(cached, offline: true);
      } else {
        state = TeacherTimetableFailure(failureMessage(
          error,
          'تعذر تحميل الجدول. تحقق من الاتصال وحاول مرة أخرى.',
        ));
      }
    }
  }

  Future<void> refresh() => load();
}

final teacherTimetableProvider = StateNotifierProvider.autoDispose.family<
    TeacherTimetableController,
    TeacherTimetableState,
    CacheScope>((ref, scope) {
  final controller = TeacherTimetableController(
    TeacherTimetableRepository(
      ref.read(apiProvider).dio,
      ref.read(databaseProvider),
    ),
    scope,
  );
  Future<void>.microtask(controller.load);
  return controller;
});
