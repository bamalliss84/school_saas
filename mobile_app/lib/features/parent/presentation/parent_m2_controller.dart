import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../../app/app.dart';
import '../../../../core/local_database/app_database.dart';
import '../../../../core/offline/offline_error_policy.dart';
import '../data/parent_attendance_repository.dart';
import '../data/parent_timetable_repository.dart';
import '../domain/parent_attendance_models.dart';
import '../domain/parent_timetable_models.dart';

typedef ParentChildQuery = ({CacheScope scope, int childId});

sealed class ParentTimetableState {
  const ParentTimetableState();
}

class ParentTimetableLoading extends ParentTimetableState {
  const ParentTimetableLoading();
}

class ParentTimetableReady extends ParentTimetableState {
  const ParentTimetableReady(this.data, {this.refreshing = false});
  final ParentTimetableData data;
  final bool refreshing;
}

class ParentTimetableFailure extends ParentTimetableState {
  const ParentTimetableFailure(this.message);
  final String message;
}

sealed class ParentAttendanceState {
  const ParentAttendanceState();
}

class ParentAttendanceLoading extends ParentAttendanceState {
  const ParentAttendanceLoading();
}

class ParentAttendanceReady extends ParentAttendanceState {
  const ParentAttendanceReady(this.data, {this.refreshing = false});
  final ParentAttendanceData data;
  final bool refreshing;
}

class ParentAttendanceFailure extends ParentAttendanceState {
  const ParentAttendanceFailure(this.message);
  final String message;
}

final parentTimetableRepositoryProvider = Provider((ref) =>
    ParentTimetableRepository(ref.read(apiProvider).dio, ref.read(databaseProvider)));
final parentAttendanceRepositoryProvider = Provider((ref) =>
    ParentAttendanceRepository(ref.read(apiProvider).dio, ref.read(databaseProvider)));

final parentTimetableProvider = StateNotifierProvider.autoDispose.family<
    ParentTimetableController, ParentTimetableState, ParentChildQuery>(
  (ref, query) {
    final controller = ParentTimetableController(
      ref.read(parentTimetableRepositoryProvider),
      query,
    );
    Future<void>.microtask(controller.load);
    return controller;
  },
);

final parentAttendanceProvider = StateNotifierProvider.autoDispose.family<
    ParentAttendanceController, ParentAttendanceState, ParentChildQuery>(
  (ref, query) {
    final controller = ParentAttendanceController(
      ref.read(parentAttendanceRepositoryProvider),
      query,
    );
    Future<void>.microtask(controller.load);
    return controller;
  },
);

class ParentTimetableController extends StateNotifier<ParentTimetableState> {
  ParentTimetableController(this.repository, this.query)
      : super(const ParentTimetableLoading());
  final ParentTimetableRepository repository;
  final ParentChildQuery query;

  Future<void> load() async {
    final cached = await repository.read(query.scope, query.childId);
    if (cached != null) {
      state = ParentTimetableReady(cached, refreshing: true);
    }
    try {
      state = ParentTimetableReady(
          await repository.load(query.scope, query.childId));
    } catch (error) {
      state = cached != null && isOfflineEligibleError(error)
          ? ParentTimetableReady(cached)
          : ParentTimetableFailure(failureMessage(
              error, 'تعذر تحميل الجدول. تحقق من الاتصال وحاول مجددًا.'));
    }
  }

  Future<void> refresh() async {
    final current = state;
    if (current is ParentTimetableReady) {
      state = ParentTimetableReady(current.data, refreshing: true);
    }
    try {
      state = ParentTimetableReady(
          await repository.refresh(query.scope, query.childId));
    } catch (error) {
      state = current is ParentTimetableReady
          ? current
          : ParentTimetableFailure(
              failureMessage(error, 'تعذر تحديث الجدول.'));
    }
  }
}

class ParentAttendanceController extends StateNotifier<ParentAttendanceState> {
  ParentAttendanceController(this.repository, this.query)
      : super(const ParentAttendanceLoading());
  final ParentAttendanceRepository repository;
  final ParentChildQuery query;

  Future<void> load() async {
    final cached = await repository.read(query.scope, query.childId);
    if (cached != null) {
      state = ParentAttendanceReady(cached, refreshing: true);
    }
    try {
      state = ParentAttendanceReady(
          await repository.load(query.scope, query.childId));
    } catch (error) {
      state = cached != null && isOfflineEligibleError(error)
          ? ParentAttendanceReady(cached)
          : ParentAttendanceFailure(failureMessage(
              error, 'تعذر تحميل الحضور. تحقق من الاتصال وحاول مجددًا.'));
    }
  }

  Future<void> refresh() async {
    final current = state;
    if (current is ParentAttendanceReady) {
      state = ParentAttendanceReady(current.data, refreshing: true);
    }
    try {
      state = ParentAttendanceReady(
          await repository.refresh(query.scope, query.childId));
    } catch (error) {
      state = current is ParentAttendanceReady
          ? current
          : ParentAttendanceFailure(
              failureMessage(error, 'تعذر تحديث الحضور.'));
    }
  }
}
