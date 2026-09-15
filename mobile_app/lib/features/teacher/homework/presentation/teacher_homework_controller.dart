import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../../app/app.dart';
import '../../../../core/local_database/app_database.dart';
import '../data/teacher_homework_repository.dart';
import '../domain/teacher_homework_models.dart';
final teacherHomeworkRepositoryProvider=Provider((ref)=>TeacherHomeworkRepository(ref.read(apiProvider).dio));
final teacherHomeworkProvider=FutureProvider.autoDispose.family<List<TeacherHomework>,({CacheScope scope,String filter,String search})>((ref,q){final r=ref.read(teacherHomeworkRepositoryProvider);return r.list(status:q.filter=='all'||q.filter=='pending'?null:q.filter,pending:q.filter=='pending',search:q.search);});
