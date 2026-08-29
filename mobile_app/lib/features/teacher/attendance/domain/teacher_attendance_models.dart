const teacherAttendanceStatuses = <String>[
  'present',
  'absent',
  'late',
  'excused',
];

String teacherAttendanceLabel(String status) => switch (status) {
      'present' => 'حاضر',
      'absent' => 'غائب',
      'late' => 'متأخر',
      'excused' => 'بعذر',
      _ => status,
    };

class TeacherAttendanceDraft {
  const TeacherAttendanceDraft({
    required this.enrollmentId,
    required this.originalStatus,
    required this.pendingStatus,
    required this.originalNote,
    required this.pendingNote,
  });

  final int enrollmentId;
  final String? originalStatus;
  final String? pendingStatus;
  final String originalNote;
  final String pendingNote;

  bool get isDirty =>
      originalStatus != pendingStatus || originalNote != pendingNote;

  TeacherAttendanceDraft copyWith({
    String? pendingStatus,
    String? pendingNote,
  }) =>
      TeacherAttendanceDraft(
        enrollmentId: enrollmentId,
        originalStatus: originalStatus,
        pendingStatus: pendingStatus ?? this.pendingStatus,
        originalNote: originalNote,
        pendingNote: pendingNote ?? this.pendingNote,
      );

  Map<String, dynamic> toRequestJson() => {
        'student_enrollment_id': enrollmentId,
        'status': pendingStatus,
        'note': pendingNote,
      };
}

class TeacherAttendanceSaveResult {
  const TeacherAttendanceSaveResult({
    required this.success,
    required this.created,
    required this.updated,
    required this.total,
    required this.academicTermId,
    required this.academicTermName,
  });

  final bool success;
  final int created;
  final int updated;
  final int total;
  final int academicTermId;
  final String academicTermName;

  factory TeacherAttendanceSaveResult.fromJson(Map<String, dynamic> json) {
    final term = json['academic_term'] is Map
        ? Map<String, dynamic>.from(json['academic_term'] as Map)
        : const <String, dynamic>{};
    return TeacherAttendanceSaveResult(
      success: json['success'] as bool? ?? false,
      created: (json['created'] as num?)?.toInt() ?? 0,
      updated: (json['updated'] as num?)?.toInt() ?? 0,
      total: (json['total'] as num?)?.toInt() ?? 0,
      academicTermId: (term['id'] as num?)?.toInt() ?? 0,
      academicTermName: term['name']?.toString() ?? '',
    );
  }
}
