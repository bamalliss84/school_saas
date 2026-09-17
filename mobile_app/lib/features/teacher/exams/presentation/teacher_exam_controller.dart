import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../../app/app.dart';
import '../../../../core/local_database/app_database.dart';
import '../data/teacher_exam_repository.dart';
import '../domain/teacher_exam_models.dart';

final teacherExamRepositoryProvider = Provider<TeacherExamRepository>((ref) {
  return TeacherExamRepository(ref.read(apiProvider).dio);
});

final teacherExamsProvider = FutureProvider.autoDispose
    .family<List<TeacherExam>, ({CacheScope scope, int? assignmentId})>(
  (ref, query) => ref
      .read(teacherExamRepositoryProvider)
      .getExams(assignmentId: query.assignmentId),
);

final teacherExamTypesProvider = FutureProvider.autoDispose
    .family<List<TeacherExamType>, CacheScope>(
  (ref, scope) => ref.read(teacherExamRepositoryProvider).getExamTypes(),
);

final teacherExamResultsProvider = FutureProvider.autoDispose
    .family<List<TeacherExamResult>, ({CacheScope scope, int examId})>(
  (ref, query) =>
      ref.read(teacherExamRepositoryProvider).getResults(query.examId),
);

final teacherExamSummaryProvider = FutureProvider.autoDispose
    .family<Map<String, dynamic>, ({CacheScope scope, int examId})>(
  (ref, query) =>
      ref.read(teacherExamRepositoryProvider).getSummary(query.examId),
);
