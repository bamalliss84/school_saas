import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../../app/app.dart';
import '../data/teacher_attendance_repository.dart';

final teacherAttendanceRepositoryProvider =
    Provider<TeacherAttendanceRepository>((ref) {
  return TeacherAttendanceRepository(ref.read(apiProvider).dio);
});
