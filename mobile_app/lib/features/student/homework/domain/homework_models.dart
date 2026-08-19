class HomeworkAttachment {
  const HomeworkAttachment({
    required this.id,
    required this.name,
    required this.url,
    required this.contentType,
    required this.fileSize,
  });

  final int id;
  final String name;
  final String url;
  final String contentType;
  final int fileSize;

  factory HomeworkAttachment.fromJson(Map<String, dynamic> json) =>
      HomeworkAttachment(
        id: json['id'] as int,
        name: json['original_name']?.toString() ?? '',
        url: json['file']?.toString() ?? '',
        contentType: json['content_type']?.toString() ?? '',
        fileSize: (json['file_size'] as num?)?.toInt() ?? 0,
      );
}

class HomeworkSubmissionModel {
  const HomeworkSubmissionModel({
    required this.id,
    required this.answer,
    required this.status,
    required this.canEdit,
    required this.canSubmit,
    this.grade,
    this.teacherNote = '',
    this.submittedAt,
    this.gradedAt,
    this.returnedAt,
    this.attachments = const [],
  });

  final int id;
  final String answer;
  final String status;
  final bool canEdit;
  final bool canSubmit;
  final double? grade;
  final String teacherNote;
  final DateTime? submittedAt;
  final DateTime? gradedAt;
  final DateTime? returnedAt;
  final List<HomeworkAttachment> attachments;

  factory HomeworkSubmissionModel.fromJson(Map<String, dynamic> json) =>
      HomeworkSubmissionModel(
        id: json['id'] as int,
        answer: json['answer']?.toString() ?? '',
        status: json['status']?.toString() ?? 'draft',
        canEdit: json['can_edit'] == true,
        canSubmit: json['can_submit'] == true,
        grade: double.tryParse(json['grade']?.toString() ?? ''),
        teacherNote: json['teacher_note']?.toString() ?? '',
        submittedAt: _date(json['submitted_at']),
        gradedAt: _date(json['graded_at']),
        returnedAt: _date(json['returned_at']),
        attachments: (json['attachments'] as List? ?? const [])
            .map((item) => HomeworkAttachment.fromJson(
                Map<String, dynamic>.from(item as Map)))
            .toList(),
      );
}

class StudentHomework {
  const StudentHomework({
    required this.id,
    required this.title,
    required this.description,
    required this.subject,
    required this.classroomId,
    required this.sectionId,
    required this.teacher,
    required this.dueDate,
    required this.completionStatus,
    required this.canCreateDraft,
    required this.canFinalSubmit,
    required this.attachments,
    this.maxGrade,
    this.grade,
    this.teacherNote = '',
    this.submission,
  });

  final int id;
  final String title;
  final String description;
  final String subject;
  final int classroomId;
  final int sectionId;
  final String teacher;
  final DateTime dueDate;
  final String completionStatus;
  final bool canCreateDraft;
  final bool canFinalSubmit;
  final List<HomeworkAttachment> attachments;
  final double? maxGrade;
  final double? grade;
  final String teacherNote;
  final HomeworkSubmissionModel? submission;

  bool get canEditDraft =>
      canCreateDraft || submission?.canEdit == true || canFinalSubmit;

  StudentHomework withSubmission(HomeworkSubmissionModel? value) =>
      StudentHomework(
        id: id,
        title: title,
        description: description,
        subject: subject,
        classroomId: classroomId,
        sectionId: sectionId,
        teacher: teacher,
        dueDate: dueDate,
        completionStatus: completionStatus,
        canCreateDraft: canCreateDraft,
        canFinalSubmit: canFinalSubmit,
        attachments: attachments,
        maxGrade: maxGrade,
        grade: grade,
        teacherNote: teacherNote,
        submission: value,
      );

  factory StudentHomework.fromJson(Map<String, dynamic> json) =>
      StudentHomework(
        id: json['id'] as int,
        title: json['title']?.toString() ?? '',
        description: json['description']?.toString() ?? '',
        subject: json['subject_name']?.toString() ?? '',
        classroomId: (json['classroom_id'] as num?)?.toInt() ?? 0,
        sectionId: (json['section_id'] as num?)?.toInt() ?? 0,
        teacher: json['teacher']?.toString() ?? '',
        dueDate: DateTime.parse(json['due_date'].toString()),
        completionStatus:
            json['completion_status']?.toString() ?? 'not_started',
        canCreateDraft: json['can_create_draft'] == true,
        canFinalSubmit: json['can_final_submit'] == true,
        attachments: (json['attachments'] as List? ?? const [])
            .map((item) => HomeworkAttachment.fromJson(
                Map<String, dynamic>.from(item as Map)))
            .toList(),
        maxGrade: double.tryParse(json['max_grade']?.toString() ?? ''),
        grade: double.tryParse(json['grade']?.toString() ?? ''),
        teacherNote: json['teacher_note']?.toString() ?? '',
      );
}

class HomeworkLocalDraft {
  const HomeworkLocalDraft({
    this.answer = '',
    this.studentNote = '',
    this.localFiles = const [],
    this.updatedAt,
  });

  final String answer;
  final String studentNote;
  final List<String> localFiles;
  final DateTime? updatedAt;
}

DateTime? _date(Object? value) =>
    value == null ? null : DateTime.tryParse(value.toString());
