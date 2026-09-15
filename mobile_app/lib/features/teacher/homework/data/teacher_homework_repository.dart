import 'package:dio/dio.dart';
import '../domain/teacher_homework_models.dart';
class TeacherHomeworkRepository {
 const TeacherHomeworkRepository(this.dio); final Dio dio;
 Future<List<TeacherHomework>> list({String? status,bool pending=false,String search=''}) async {final r=await dio.get<Map<String,dynamic>>('teachers/me/homework/',queryParameters:{if(status!=null)'status':status,if(pending)'pending_grading':'true',if(search.trim().isNotEmpty)'search':search.trim(),'page_size':100});return (r.data?['results'] as List? ?? const []).map((e)=>TeacherHomework.fromJson(Map<String,dynamic>.from(e as Map))).toList();}
 Future<TeacherHomework> detail(int id) async=>TeacherHomework.fromJson((await dio.get<Map<String,dynamic>>('homework/$id/')).data!);
 Future<Map<String,dynamic>> summary(int id) async=>(await dio.get<Map<String,dynamic>>('homework/$id/summary/')).data!;
 Future<TeacherHomework> save({int? id,required int assignmentId,required int academicYearId,required String title,required String description,required DateTime due,required String type,double? maxGrade}) async {final d={'teacher_assignment':assignmentId,'academic_year':academicYearId,'title':title,'description':description,'due_date':due.toUtc().toIso8601String(),'submission_type':type,'max_grade':maxGrade};final r=id==null?await dio.post<Map<String,dynamic>>('homework/',data:d):await dio.patch<Map<String,dynamic>>('homework/$id/',data:d);return TeacherHomework.fromJson(r.data!);}
 Future<TeacherHomework> action(int id,String action) async=>TeacherHomework.fromJson((await dio.post<Map<String,dynamic>>('homework/$id/$action/')).data!);
 Future<void> delete(int id)=>dio.delete<void>('homework/$id/');
 Future<TeacherStudentStatus> students(int id,{String? status,String search=''}) async=>TeacherStudentStatus.fromJson((await dio.get<Map<String,dynamic>>('homework/$id/student-status/',queryParameters:{if(status!=null)'status':status,if(search.trim().isNotEmpty)'search':search.trim()})).data!);
 Future<TeacherSubmission> submission(int id) async=>TeacherSubmission.fromJson((await dio.get<Map<String,dynamic>>('homework-submissions/$id/')).data!);
 Future<TeacherSubmission> grade(int id,double grade,String note) async=>TeacherSubmission.fromJson((await dio.post<Map<String,dynamic>>('homework-submissions/$id/grade/',data:{'grade':grade,'teacher_note':note})).data!);
 Future<TeacherSubmission> review(int id,String note) async=>TeacherSubmission.fromJson((await dio.post<Map<String,dynamic>>('homework-submissions/$id/review/',data:{'teacher_note':note})).data!);
 Future<TeacherSubmission> returnWork(int id,String note) async=>TeacherSubmission.fromJson((await dio.post<Map<String,dynamic>>('homework-submissions/$id/return/',data:{'teacher_note':note})).data!);
 Future<void> upload(int id,List<String> paths) async {final f=FormData();for(final p in paths){f.files.add(MapEntry('files',await MultipartFile.fromFile(p)));}await dio.post('homework/$id/attachments/',data:f);}
 Future<void> deleteAttachment(int id,int aid)=>dio.delete<void>('homework/$id/attachments/$aid/');
}
