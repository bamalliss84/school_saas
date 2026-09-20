import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../../core/local_database/app_database.dart';
import '../../../../core/offline/offline_error_policy.dart';
import '../data/results_repository.dart';
import '../domain/result_models.dart';

sealed class ResultsState {
  const ResultsState();
}

class ResultsLoading extends ResultsState {
  const ResultsLoading();
}

class ResultsFailure extends ResultsState {
  const ResultsFailure(this.message);
  final String message;
}

class ResultsReady extends ResultsState {
  const ResultsReady(this.data,
      {this.term, this.subject, this.examTypeId, this.selected});
  final StudentResultsData data;
  final String? term;
  final String? subject;
  final int? examTypeId;
  final StudentResult? selected;

  List<StudentResult> get filterUniverse => data.items
      .where((item) =>
          item.isPublished &&
          (term == null || item.academicTermName == term) &&
          (subject == null || item.subject == subject))
      .toList();

  List<ResultExamTypeOption> get availableExamTypes {
    final byId = <int, ResultExamTypeOption>{};
    for (final item in filterUniverse) {
      final name = item.examTypeName.trim();
      if (item.examTypeId <= 0 || name.isEmpty) continue;
      byId[item.examTypeId] = ResultExamTypeOption(item.examTypeId, name);
    }
    final values = byId.values.toList();
    values.sort((a, b) => a.id.compareTo(b.id));
    return values;
  }

  List<StudentResult> get visible => filterUniverse
      .where((item) => (examTypeId == null || item.examTypeId == examTypeId))
      .toList();

  ResultsReady normalizeExamType() {
    if (examTypeId == null ||
        availableExamTypes.any((type) => type.id == examTypeId)) {
      return this;
    }
    return copyWith(clearExamType: true);
  }

  ResultsReady copyWith(
          {StudentResultsData? data,
          String? term,
          String? subject,
          int? examTypeId,
          StudentResult? selected,
          bool clearTerm = false,
          bool clearSubject = false,
          bool clearExamType = false,
          bool clearSelected = false}) =>
      ResultsReady(
        data ?? this.data,
        term: clearTerm ? null : term ?? this.term,
        subject: clearSubject ? null : subject ?? this.subject,
        examTypeId: clearExamType ? null : examTypeId ?? this.examTypeId,
        selected: clearSelected ? null : selected ?? this.selected,
      );
}

class ResultExamTypeOption {
  const ResultExamTypeOption(this.id, this.label);
  final int id;
  final String label;
}

class ResultsController extends StateNotifier<ResultsState> {
  ResultsController(this.repository, this.scope)
      : super(const ResultsLoading());
  final StudentResultsRepository repository;
  final CacheScope scope;
  Future<void>? _inFlight;

  Future<void> load() async {
    final active = _inFlight;
    if (active != null) {
      await active;
      return;
    }
    final operation = _loadOnce();
    _inFlight = operation;
    try {
      await operation;
    } finally {
      if (identical(_inFlight, operation)) _inFlight = null;
    }
  }

  Future<void> _loadOnce() async {
    final cached = await repository.read(scope);
    try {
      final fresh = await repository.refresh(scope);
      final current = state;
      state = current is ResultsReady
          ? current.copyWith(data: fresh).normalizeExamType()
          : ResultsReady(fresh);
    } catch (error) {
      final current = state;
      if (isOfflineEligibleError(error) && current is ResultsReady) {
        return;
      }
      if (cached != null && isOfflineEligibleError(error)) {
        state = ResultsReady(cached);
      } else {
        state = ResultsFailure(
            failureMessage(error, 'تعذر تحميل النتائج ولا توجد بيانات محفوظة'));
      }
    }
  }

  Future<void> refresh() => load();
  void selectTerm(String? value) {
    final s = state;
    if (s is ResultsReady) {
      state = s
          .copyWith(term: value, clearTerm: value == null, clearSelected: true)
          .normalizeExamType();
    }
  }

  void selectSubject(String? value) {
    final s = state;
    if (s is ResultsReady) {
      state = s
          .copyWith(
              subject: value, clearSubject: value == null, clearSelected: true)
          .normalizeExamType();
    }
  }

  void selectExamType(int? value) {
    final s = state;
    if (s is ResultsReady) {
      state = s.copyWith(
          examTypeId: value, clearExamType: value == null, clearSelected: true);
    }
  }

  void open(StudentResult value) {
    final s = state;
    if (s is ResultsReady) state = s.copyWith(selected: value);
  }

  void close() {
    final s = state;
    if (s is ResultsReady) state = s.copyWith(clearSelected: true);
  }
}
