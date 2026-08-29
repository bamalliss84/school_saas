class TeacherBrief {
  const TeacherBrief({required this.id, required this.name, this.code = ''});

  final int id;
  final String name;
  final String code;

  factory TeacherBrief.fromJson(Map<String, dynamic> json) => TeacherBrief(
        id: (json['id'] as num).toInt(),
        name: json['name']?.toString() ?? '',
        code: json['code']?.toString() ?? '',
      );
}

class TeacherAssignmentSummary {
  const TeacherAssignmentSummary({
    required this.id,
    required this.academicYear,
    required this.classroom,
    required this.section,
    required this.subject,
    required this.isCurrent,
    this.startDate,
    this.endDate,
  });

  final int id;
  final TeacherBrief academicYear;
  final TeacherBrief classroom;
  final TeacherBrief section;
  final TeacherBrief subject;
  final bool isCurrent;
  final String? startDate;
  final String? endDate;

  factory TeacherAssignmentSummary.fromJson(Map<String, dynamic> json) =>
      TeacherAssignmentSummary(
        id: (json['id'] as num).toInt(),
        academicYear: TeacherBrief.fromJson(_map(json['academic_year'])),
        classroom: TeacherBrief.fromJson(_map(json['classroom'])),
        section: TeacherBrief.fromJson(_map(json['section'])),
        subject: TeacherBrief.fromJson(_map(json['subject'])),
        isCurrent: json['is_current'] as bool? ?? false,
        startDate: json['start_date']?.toString(),
        endDate: json['end_date']?.toString(),
      );
}

class TeacherRosterAttendance {
  const TeacherRosterAttendance({
    required this.status,
    required this.date,
    this.note = '',
  });

  final String status;
  final String date;
  final String note;

  factory TeacherRosterAttendance.fromJson(Map<String, dynamic> json) =>
      TeacherRosterAttendance(
        status: json['status']?.toString() ?? '',
        date: json['attendance_date']?.toString() ?? '',
        note: json['note']?.toString() ?? '',
      );
}

class TeacherRosterStudent {
  const TeacherRosterStudent({
    required this.enrollmentId,
    required this.id,
    required this.fullName,
    this.studentCode = '',
    this.gender = '',
    this.photoUrl,
    this.attendance,
  });

  final int enrollmentId;
  final int id;
  final String fullName;
  final String studentCode;
  final String gender;
  final String? photoUrl;
  final TeacherRosterAttendance? attendance;

  factory TeacherRosterStudent.fromJson(Map<String, dynamic> json) {
    final student = _map(json['student']);
    final attendance = json['attendance'];
    return TeacherRosterStudent(
      enrollmentId: (json['student_enrollment_id'] as num).toInt(),
      id: (student['id'] as num).toInt(),
      fullName: student['full_name']?.toString() ?? '',
      studentCode: student['student_code']?.toString() ?? '',
      gender: student['gender']?.toString() ?? '',
      photoUrl: student['photo_url']?.toString(),
      attendance: attendance is Map
          ? TeacherRosterAttendance.fromJson(
              Map<String, dynamic>.from(attendance),
            )
          : null,
    );
  }
}

class TeacherAssignmentRoster {
  const TeacherAssignmentRoster({
    required this.assignmentId,
    required this.academicYear,
    required this.classroom,
    required this.section,
    required this.subject,
    required this.date,
    required this.totalStudents,
    required this.recordedCount,
    required this.students,
  });

  final int assignmentId;
  final TeacherBrief academicYear;
  final TeacherBrief classroom;
  final TeacherBrief section;
  final TeacherBrief subject;
  final DateTime date;
  final int totalStudents;
  final int recordedCount;
  final List<TeacherRosterStudent> students;

  factory TeacherAssignmentRoster.fromJson(Map<String, dynamic> json) =>
      TeacherAssignmentRoster(
        assignmentId: (json['assignment_id'] as num).toInt(),
        academicYear: TeacherBrief.fromJson(_map(json['academic_year'])),
        classroom: TeacherBrief.fromJson(_map(json['classroom'])),
        section: TeacherBrief.fromJson(_map(json['section'])),
        subject: TeacherBrief.fromJson(_map(json['subject'])),
        date: DateTime.parse(json['date'].toString()),
        totalStudents: (json['total_students'] as num).toInt(),
        recordedCount: (json['recorded_count'] as num).toInt(),
        students: (json['roster'] as List? ?? const [])
            .map((item) => TeacherRosterStudent.fromJson(
                  Map<String, dynamic>.from(item as Map),
                ))
            .toList(growable: false),
      );
}

Map<String, dynamic> _map(dynamic value) =>
    Map<String, dynamic>.from(value as Map);
