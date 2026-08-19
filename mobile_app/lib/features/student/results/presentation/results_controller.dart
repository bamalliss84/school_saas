import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../../core/local_database/app_database.dart';
import '../../../../core/offline/offline_error_policy.dart';
import '../data/results_repository.dart';
import '../domain/result_models.dart';

sealed class ResultsState {
  const ResultsState();
}
class ResultsLoading extends ResultsState { const ResultsLoading(); }
class ResultsFailure extends ResultsState {
  const ResultsFailure(this.message);
  final String message;
}
class ResultsReady extends ResultsState {
  const ResultsReady(this.data, {this.term, this.subject, this.examTypeId, this.selected});
  final StudentResultsData data;
  final String? term;
  final String? subject;
  final int? examTypeId;
  final StudentResult? selected;

  List<StudentResult> get visible => data.items.where((item) =>
      (term == null || item.academicTermName == term) &&
      (subject == null || item.subject == subject) &&
      (examTypeId == null || item.examTypeId == examTypeId)).toList();

  ResultsReady copyWith({StudentResultsData? data, String? term, String? subject,
      int? examTypeId, StudentResult? selected, bool clearTerm=false, bool clearSubject=false,
      bool clearExamType=false, bool clearSelected=false}) => ResultsReady(
        data ?? this.data,
        term: clearTerm ? null : term ?? this.term,
        subject: clearSubject ? null : subject ?? this.subject,
        examTypeId: clearExamType ? null : examTypeId ?? this.examTypeId,
        selected: clearSelected ? null : selected ?? this.selected,
      );
}

class ResultsController extends StateNotifier<ResultsState> {
  ResultsController(this.repository, this.scope) : super(const ResultsLoading());
  final StudentResultsRepository repository;
  final CacheScope scope;

  Future<void> load() async {
    final cached = await repository.read(scope);
    if (cached != null) state = ResultsReady(cached);
    try {
      final fresh = await repository.refresh(scope);
      final current = state;
      state = current is ResultsReady ? current.copyWith(data: fresh) : ResultsReady(fresh);
    } catch (error) {
      if (cached != null && isOfflineEligibleError(error)) {
        state = ResultsReady(cached);
      } else {
        state = ResultsFailure(failureMessage(error, 'تعذر تحميل النتائج ولا توجد بيانات محفوظة'));
      }
    }
  }

  Future<void> refresh() => load();
  void selectTerm(String? value) {
    final s=state; if (s is ResultsReady) state=s.copyWith(term:value, clearTerm:value==null, clearSelected:true);
  }
  void selectSubject(String? value) {
    final s=state; if (s is ResultsReady) state=s.copyWith(subject:value, clearSubject:value==null, clearSelected:true);
  }
  void selectExamType(int? value) {
    final s=state; if (s is ResultsReady) state=s.copyWith(examTypeId:value, clearExamType:value==null, clearSelected:true);
  }
  void open(StudentResult value) {
    final s=state; if (s is ResultsReady) state=s.copyWith(selected:value);
  }
  void close() {
    final s=state; if (s is ResultsReady) state=s.copyWith(clearSelected:true);
  }
}
