import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../../core/local_database/app_database.dart';
import '../../../../core/offline/offline_error_policy.dart';
import '../data/attendance_repository.dart';
import '../domain/attendance_models.dart';

sealed class AttendanceState {
  const AttendanceState();
}
class AttendanceLoading extends AttendanceState { const AttendanceLoading(); }
class AttendanceFailure extends AttendanceState {
  const AttendanceFailure(this.message);
  final String message;
}
class AttendanceReady extends AttendanceState {
  const AttendanceReady(this.data, {this.filterKey = 'all', this.selected});
  final StudentAttendanceData data;
  final String filterKey;
  final StudentAttendanceRecord? selected;

  List<StudentAttendanceRecord> get visible {
    if (filterKey == 'all') return data.records;
    if (filterKey == 'month') {
      final now = DateTime.now();
      return data.records.where((row) =>
          row.date.year == now.year && row.date.month == now.month).toList();
    }
    if (filterKey.startsWith('term:')) {
      final id = int.tryParse(filterKey.substring(5));
      return data.records.where((row) => row.termId == id).toList();
    }
    return data.records;
  }

  AttendanceSummary get summary {
    var present = 0, absent = 0, late = 0, excused = 0;
    for (final row in visible) {
      if (row.status == StudentAttendanceStatus.present) present++;
      if (row.status == StudentAttendanceStatus.absent) absent++;
      if (row.status == StudentAttendanceStatus.late) late++;
      if (row.status == StudentAttendanceStatus.excused) excused++;
    }
    return AttendanceSummary(
      total: visible.length, present: present, absent: absent,
      late: late, excused: excused,
    );
  }

  AttendanceReady copyWith({StudentAttendanceData? data, String? filterKey,
      StudentAttendanceRecord? selected, bool clearSelected = false}) => AttendanceReady(
        data ?? this.data,
        filterKey: filterKey ?? this.filterKey,
        selected: clearSelected ? null : selected ?? this.selected,
      );
}

class AttendanceController extends StateNotifier<AttendanceState> {
  AttendanceController(this.repository, this.scope) : super(const AttendanceLoading());
  final StudentAttendanceRepository repository;
  final CacheScope scope;

  Future<void> load() async {
    final cached = await repository.read(scope);
    if (cached != null) state = AttendanceReady(cached);
    try {
      final fresh = await repository.refresh(scope);
      final current = state;
      state = current is AttendanceReady
          ? current.copyWith(data: fresh)
          : AttendanceReady(fresh);
    } catch (error) {
      if (cached != null && isOfflineEligibleError(error)) {
        state = AttendanceReady(cached);
      } else {
        state = AttendanceFailure(failureMessage(
            error, 'تعذر تحميل سجل الحضور ولا توجد بيانات محفوظة'));
      }
    }
  }

  Future<void> refresh() => load();
  void selectFilter(String value) {
    final current = state;
    if (current is AttendanceReady) {
      state = current.copyWith(filterKey: value, clearSelected: true);
    }
  }
  void open(StudentAttendanceRecord record) {
    final current = state;
    if (current is AttendanceReady) state = current.copyWith(selected: record);
  }
  void close() {
    final current = state;
    if (current is AttendanceReady) state = current.copyWith(clearSelected: true);
  }
}
