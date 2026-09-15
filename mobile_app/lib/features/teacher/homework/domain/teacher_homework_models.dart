class TeacherHomeworkAttachment {
  const TeacherHomeworkAttachment(this.id, this.name, this.url);
  final int id; final String name, url;
  factory TeacherHomeworkAttachment.fromJson(Map<String,dynamic> j)=>TeacherHomeworkAttachment((j['id'] as num).toInt(),j['original_name']?.toString()??'',j['file']?.toString()??'');
}
class TeacherHomework {
  const TeacherHomework({required this.id,required this.assignmentId,required this.title,required this.description,required this.subject,required this.classroomId,required this.sectionId,required this.status,required this.submissionType,required this.dueDate,required this.canEdit,required this.canPublish,required this.canClose,required this.attachments,this.maxGrade});
  final int id,assignmentId,classroomId,sectionId; final String title,description,subject,status,submissionType; final DateTime dueDate; final double? maxGrade; final bool canEdit,canPublish,canClose; final List<TeacherHomeworkAttachment> attachments;
  factory TeacherHomework.fromJson(Map<String,dynamic> j)=>TeacherHomework(id:(j['id'] as num).toInt(),assignmentId:(j['teacher_assignment'] as num).toInt(),title:j['title']?.toString()??'',description:j['description']?.toString()??'',subject:j['subject_name']?.toString()??'',classroomId:(j['classroom_id'] as num?)?.toInt()??0,sectionId:(j['section_id'] as num?)?.toInt()??0,status:j['status']?.toString()??'draft',submissionType:j['submission_type']?.toString()??'text',dueDate:DateTime.parse(j['due_date'].toString()),maxGrade:double.tryParse(j['max_grade']?.toString()??''),canEdit:j['can_edit']==true,canPublish:j['can_publish']==true,canClose:j['can_close']==true,attachments:(j['attachments'] as List? ?? const []).map((e)=>TeacherHomeworkAttachment.fromJson(Map<String,dynamic>.from(e as Map))).toList());
}
class TeacherHomeworkStudent {
 const TeacherHomeworkStudent({required this.studentName,required this.studentCode,required this.status,required this.isLate,required this.canGrade,required this.canReview,required this.canReturn,this.submissionId,this.grade,this.maxGrade,this.teacherNote=''});
 final String studentName,studentCode,status,teacherNote; final int? submissionId; final double? grade,maxGrade; final bool isLate,canGrade,canReview,canReturn;
 factory TeacherHomeworkStudent.fromJson(Map<String,dynamic> j)=>TeacherHomeworkStudent(studentName:j['student_name']?.toString()??'',studentCode:j['student_code']?.toString()??'',status:j['status']?.toString()??'not_started',submissionId:(j['submission_id'] as num?)?.toInt(),grade:double.tryParse(j['grade']?.toString()??''),maxGrade:double.tryParse(j['max_grade']?.toString()??''),teacherNote:j['teacher_note']?.toString()??'',isLate:j['is_late']==true,canGrade:j['can_grade']==true,canReview:j['can_review']==true,canReturn:j['can_return']==true);
}
class TeacherStudentStatus {
 const TeacherStudentStatus(this.data,this.students); final Map<String,dynamic> data; final List<TeacherHomeworkStudent> students; int count(String k)=>(data[k] as num?)?.toInt()??0;
 factory TeacherStudentStatus.fromJson(Map<String,dynamic> j)=>TeacherStudentStatus(j,(j['students'] as List? ?? const []).map((e)=>TeacherHomeworkStudent.fromJson(Map<String,dynamic>.from(e as Map))).toList());
}
class TeacherSubmission {
 const TeacherSubmission({required this.id,required this.studentName,required this.studentCode,required this.answer,required this.status,required this.attachments,this.grade,this.teacherNote=''});
 final int id; final String studentName,studentCode,answer,status,teacherNote; final double? grade; final List<TeacherHomeworkAttachment> attachments;
 factory TeacherSubmission.fromJson(Map<String,dynamic> j)=>TeacherSubmission(id:(j['id'] as num).toInt(),studentName:j['student_name']?.toString()??'',studentCode:j['student_code']?.toString()??'',answer:j['answer']?.toString()??'',status:j['status']?.toString()??'',grade:double.tryParse(j['grade']?.toString()??''),teacherNote:j['teacher_note']?.toString()??'',attachments:(j['attachments'] as List? ?? const []).map((e)=>TeacherHomeworkAttachment.fromJson(Map<String,dynamic>.from(e as Map))).toList());
}
