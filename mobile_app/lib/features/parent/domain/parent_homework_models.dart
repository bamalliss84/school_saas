enum ParentHomeworkStatus {
  notStarted('not_started', 'لم يبدأ'),
  draft('draft', 'قيد العمل'),
  submitted('submitted', 'تم التسليم'),
  returned('returned', 'أعيد للمراجعة'),
  reviewed('reviewed', 'تمت المراجعة'),
  graded('graded', 'تم التقييم'),
  overdue('overdue', 'متأخر'),
  closedWithoutSubmission('closed_without_submission', 'مغلق دون تسليم'),
  viewOnly('view_only', 'لا يتطلب تسليم');

  const ParentHomeworkStatus(this.apiValue, this.arabicLabel);
  final String apiValue;
  final String arabicLabel;

  static ParentHomeworkStatus fromApi(Object? value) => values.firstWhere(
        (item) => item.apiValue == value,
        orElse: () => notStarted,
      );
}

class ParentHomeworkAttachment {
  const ParentHomeworkAttachment({
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

  factory ParentHomeworkAttachment.fromJson(Map<String, dynamic> json) =>
      ParentHomeworkAttachment(
        id: (json['id'] as num?)?.toInt() ?? 0,
        name: json['original_name']?.toString() ?? '',
        url: json['file']?.toString() ?? '',
        contentType: json['content_type']?.toString() ?? '',
        fileSize: (json['file_size'] as num?)?.toInt() ?? 0,
      );

  Map<String, Object?> toJson() => {
        'id': id,
        'original_name': name,
        'file': url,
        'content_type': contentType,
        'file_size': fileSize,
      };
}

class ParentHomework {
  const ParentHomework({
    required this.id,
    required this.title,
    required this.description,
    required this.subject,
    required this.teacher,
    required this.status,
    required this.submissionType,
    required this.dueDate,
    required this.completionStatus,
    required this.attachments,
    this.publishedAt,
    this.submissionStatus,
    this.submittedAt,
    this.gradedAt,
    this.grade,
    this.maxGrade,
    this.teacherNote = '',
    this.isOverdue = false,
  });

  final int id;
  final String title;
  final String description;
  final String subject;
  final String teacher;
  final String status;
  final String submissionType;
  final DateTime dueDate;
  final DateTime? publishedAt;
  final ParentHomeworkStatus completionStatus;
  final String? submissionStatus;
  final DateTime? submittedAt;
  final DateTime? gradedAt;
  final double? grade;
  final double? maxGrade;
  final String teacherNote;
  final bool isOverdue;
  final List<ParentHomeworkAttachment> attachments;

  factory ParentHomework.fromJson(Map<String, dynamic> json) => ParentHomework(
        id: (json['id'] as num?)?.toInt() ?? 0,
        title: json['title']?.toString() ?? '',
        description: json['description']?.toString() ?? '',
        subject: json['subject_name']?.toString() ?? '',
        teacher: json['teacher']?.toString() ?? '',
        status: json['status']?.toString() ?? '',
        submissionType: json['submission_type']?.toString() ?? 'text',
        dueDate: DateTime.parse(json['due_date'].toString()),
        publishedAt: _date(json['published_at']),
        completionStatus:
            ParentHomeworkStatus.fromApi(json['completion_status']),
        submissionStatus: json['submission_status']?.toString(),
        submittedAt: _date(json['submitted_at']),
        gradedAt: _date(json['graded_at']),
        grade: double.tryParse(json['grade']?.toString() ?? ''),
        maxGrade: double.tryParse(json['max_grade']?.toString() ?? ''),
        teacherNote: json['teacher_note']?.toString() ?? '',
        isOverdue: json['is_overdue'] == true,
        attachments: _attachments(json['attachments']),
      );

  Map<String, Object?> toJson() => {
        'id': id,
        'title': title,
        'description': description,
        'subject_name': subject,
        'teacher': teacher,
        'status': status,
        'submission_type': submissionType,
        'due_date': dueDate.toIso8601String(),
        'published_at': publishedAt?.toIso8601String(),
        'completion_status': completionStatus.apiValue,
        'submission_status': submissionStatus,
        'submitted_at': submittedAt?.toIso8601String(),
        'graded_at': gradedAt?.toIso8601String(),
        'grade': grade,
        'max_grade': maxGrade,
        'teacher_note': teacherNote,
        'is_overdue': isOverdue,
        'attachments': attachments.map((item) => item.toJson()).toList(),
      };
}

class ParentHomeworkSubmission {
  const ParentHomeworkSubmission({
    required this.id,
    required this.homeworkId,
    required this.studentId,
    required this.answer,
    required this.status,
    required this.attachments,
    this.submittedAt,
    this.gradedAt,
    this.returnedAt,
    this.grade,
    this.teacherNote = '',
    this.isLate = false,
  });
  final int id;
  final int homeworkId;
  final int studentId;
  final String answer;
  final String status;
  final DateTime? submittedAt;
  final DateTime? gradedAt;
  final DateTime? returnedAt;
  final double? grade;
  final String teacherNote;
  final bool isLate;
  final List<ParentHomeworkAttachment> attachments;

  factory ParentHomeworkSubmission.fromJson(Map<String, dynamic> json) =>
      ParentHomeworkSubmission(
        id: (json['id'] as num?)?.toInt() ?? 0,
        homeworkId: (json['homework'] as num?)?.toInt() ?? 0,
        studentId: (json['student_id'] as num?)?.toInt() ?? 0,
        answer: json['answer']?.toString() ?? '',
        status: json['status']?.toString() ?? '',
        submittedAt: _date(json['submitted_at']),
        gradedAt: _date(json['graded_at']),
        returnedAt: _date(json['returned_at']),
        grade: double.tryParse(json['grade']?.toString() ?? ''),
        teacherNote: json['teacher_note']?.toString() ?? '',
        isLate: json['is_late'] == true,
        attachments: _attachments(json['attachments']),
      );

  Map<String, Object?> toJson() => {
        'id': id,
        'homework': homeworkId,
        'student_id': studentId,
        'answer': answer,
        'status': status,
        'submitted_at': submittedAt?.toIso8601String(),
        'graded_at': gradedAt?.toIso8601String(),
        'returned_at': returnedAt?.toIso8601String(),
        'grade': grade,
        'teacher_note': teacherNote,
        'is_late': isLate,
        'attachments': attachments.map((item) => item.toJson()).toList(),
      };
}

List<ParentHomeworkAttachment> _attachments(Object? raw) =>
    (raw as List? ?? const [])
        .whereType<Map>()
        .map((item) =>
            ParentHomeworkAttachment.fromJson(Map<String, dynamic>.from(item)))
        .toList(growable: false);

DateTime? _date(Object? value) =>
    value == null ? null : DateTime.tryParse(value.toString());
