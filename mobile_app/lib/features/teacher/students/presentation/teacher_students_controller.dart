import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../../app/app.dart';
import '../../../../core/local_database/app_database.dart';
import '../data/teacher_students_repository.dart';
import '../domain/teacher_students_models.dart';

final teacherAssignmentsProvider = FutureProvider.autoDispose
    .family<List<TeacherAssignmentSummary>, CacheScope>((ref, scope) {
  final repository = TeacherStudentsRepository(ref.read(apiProvider).dio);
  return repository.getAssignments();
});

typedef TeacherRosterRequest = ({
  CacheScope scope,
  int assignmentId,
  String date,
});

final teacherRosterProvider = FutureProvider.autoDispose
    .family<TeacherAssignmentRoster, TeacherRosterRequest>((ref, request) {
  final repository = TeacherStudentsRepository(ref.read(apiProvider).dio);
  return repository.getRoster(
    assignmentId: request.assignmentId,
    date: request.date,
  );
});
