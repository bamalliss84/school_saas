const teacherResultStatusLabels = <String, String>{
  'not_graded': 'غير مصحح',
  'present': 'حاضر',
  'absent': 'غائب',
  'excused': 'بعذر',
  'exempted': 'معفى',
};

const teacherResultWorkflowLabels = <String, String>{
  'draft': 'مسودة',
  'submitted': 'مرسل للاعتماد',
  'approved': 'معتمد',
  'rejected': 'معاد للمراجعة',
};

class TeacherExamType {
  const TeacherExamType({
    required this.id,
    required this.name,
    required this.code,
    required this.maxScore,
    required this.active,
  });

  final int id;
  final String name;
  final String code;
  final double maxScore;
  final bool active;

  factory TeacherExamType.fromJson(Map<String, dynamic> json) => TeacherExamType(
        id: (json['id'] as num).toInt(),
        name: json['name']?.toString() ?? '',
        code: json['code']?.toString() ?? '',
        maxScore: double.tryParse(json['max_score']?.toString() ?? '') ?? 0,
        active: json['is_active'] == true,
      );
}

class TeacherExam {
  const TeacherExam({
    required this.id,
    required this.academicYearId,
    required this.academicTermId,
    required this.assignmentId,
    required this.examTypeId,
    required this.title,
    required this.examDate,
    required this.totalMarks,
    required this.status,
    required this.classroomId,
    required this.sectionId,
    required this.subjectId,
    this.notes = '',
  });

  final int id;
  final int academicYearId;
  final int academicTermId;
  final int assignmentId;
  final int examTypeId;
  final int classroomId;
  final int sectionId;
  final int subjectId;
  final String title;
  final DateTime examDate;
  final double totalMarks;
  final String status;
  final String notes;

  bool get editable => status == 'draft';

  factory TeacherExam.fromJson(Map<String, dynamic> json) => TeacherExam(
        id: (json['id'] as num).toInt(),
        academicYearId: (json['academic_year'] as num).toInt(),
        academicTermId: (json['academic_term'] as num).toInt(),
        assignmentId: (json['teacher_assignment'] as num).toInt(),
        examTypeId: (json['exam_type'] as num).toInt(),
        title: json['title']?.toString() ?? '',
        examDate: DateTime.parse(json['exam_date'].toString()),
        totalMarks: double.tryParse(json['total_marks']?.toString() ?? '') ?? 0,
        status: json['status']?.toString() ?? 'draft',
        notes: json['notes']?.toString() ?? '',
        classroomId: (json['classroom_id'] as num?)?.toInt() ?? 0,
        sectionId: (json['section_id'] as num?)?.toInt() ?? 0,
        subjectId: (json['subject_id'] as num?)?.toInt() ?? 0,
      );
}

class TeacherExamResult {
  const TeacherExamResult({
    required this.id,
    required this.examId,
    required this.enrollmentId,
    required this.studentName,
    required this.studentCode,
    required this.status,
    required this.workflowStatus,
    this.score,
    this.remarks = '',
  });

  final int id;
  final int examId;
  final int enrollmentId;
  final String studentName;
  final String studentCode;
  final double? score;
  final String status;
  final String remarks;
  final String workflowStatus;

  bool get editable => workflowStatus == 'draft';
  bool get submittable => workflowStatus == 'draft' && status != 'not_graded';

  factory TeacherExamResult.fromJson(Map<String, dynamic> json) => TeacherExamResult(
        id: (json['id'] as num).toInt(),
        examId: (json['exam'] as num).toInt(),
        enrollmentId: (json['student_enrollment'] as num).toInt(),
        studentName: json['student_name']?.toString() ?? '',
        studentCode: json['student_code']?.toString() ?? '',
        score: double.tryParse(json['score']?.toString() ?? ''),
        status: json['status']?.toString() ?? 'not_graded',
        remarks: json['remarks']?.toString() ?? '',
        workflowStatus: json['workflow_status']?.toString() ?? 'draft',
      );
}

class TeacherExamResultDraft {
  const TeacherExamResultDraft({
    required this.enrollmentId,
    required this.status,
    this.resultId,
    this.score,
    this.remarks = '',
  });

  final int enrollmentId;
  final int? resultId;
  final String status;
  final double? score;
  final String remarks;

  Map<String, dynamic> toJson() => {
        'student_enrollment': enrollmentId,
        'status': status,
        'score': status == 'present' ? score : null,
        'remarks': remarks,
      };
}

class TeacherExamResultEditState {
  TeacherExamResultEditState({
    required this.enrollmentId,
    required this.status,
    required this.scoreText,
    required this.remarks,
    required this.workflowStatus,
    this.resultId,
  });

  factory TeacherExamResultEditState.fromResult({
    required int enrollmentId,
    TeacherExamResult? result,
  }) =>
      TeacherExamResultEditState(
        enrollmentId: enrollmentId,
        resultId: result?.id,
        status: result?.status ?? 'not_graded',
        scoreText: result?.score?.toString() ?? '',
        remarks: result?.remarks ?? '',
        workflowStatus: result?.workflowStatus ?? 'draft',
      );

  final int enrollmentId;
  int? resultId;
  String status;
  String scoreText;
  String remarks;
  String workflowStatus;

  bool get usesScore => status == 'present';
  bool get editable => workflowStatus == 'draft' || workflowStatus == 'rejected';
  bool get submittable =>
      resultId != null && workflowStatus == 'draft' && status != 'not_graded';

  void selectStatus(String value) {
    status = value;
    if (!usesScore) scoreText = '';
  }

  void applyCanonical(TeacherExamResult result) {
    resultId = result.id;
    status = result.status;
    scoreText = result.score?.toString() ?? '';
    remarks = result.remarks;
    workflowStatus = result.workflowStatus;
  }

  TeacherExamResultDraft toDraft() => TeacherExamResultDraft(
        enrollmentId: enrollmentId,
        resultId: resultId,
        status: status,
        score: usesScore ? double.tryParse(scoreText) : null,
        remarks: remarks,
      );
}
