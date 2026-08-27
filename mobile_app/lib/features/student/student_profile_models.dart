class StudentProfile {
  const StudentProfile(
      {required this.id,
      required this.fullName,
      required this.studentCode,
      required this.schoolName,
      this.academicYearName,
      this.classroomName,
      this.sectionName});
  final int id;
  final String fullName, studentCode, schoolName;
  final String? academicYearName, classroomName, sectionName;
  factory StudentProfile.fromJson(Map<String, dynamic> json) {
    final school = json['school'] is Map ? json['school'] as Map : const {};
    final enrollment = json['current_enrollment'] is Map
        ? json['current_enrollment'] as Map
        : const {};
    return StudentProfile(
      id: (json['id'] as num?)?.toInt() ?? 0,
      fullName: (json['full_name'] ?? '').toString(),
      studentCode: (json['student_code'] ?? '').toString(),
      schoolName: (school['name'] ?? '').toString(),
      academicYearName: _nestedName(enrollment['academic_year']),
      classroomName: _nestedName(enrollment['classroom']),
      sectionName: _nestedName(enrollment['section']),
    );
  }
}

class StudentAcademicHistoryItem {
  const StudentAcademicHistoryItem(
      {required this.id,
      required this.schoolName,
      required this.academicYearName,
      required this.status,
      required this.isCurrent,
      this.classroomName,
      this.sectionName});
  final int id;
  final String schoolName, academicYearName, status;
  final bool isCurrent;
  final String? classroomName, sectionName;
  factory StudentAcademicHistoryItem.fromJson(Map<String, dynamic> json) =>
      StudentAcademicHistoryItem(
        id: (json['id'] as num?)?.toInt() ?? 0,
        schoolName: _nestedName(json['school']) ?? '',
        academicYearName: _nestedName(json['academic_year']) ?? '',
        classroomName: _nestedName(json['classroom']),
        sectionName: _nestedName(json['section']),
        status: (json['status'] ?? '').toString(),
        isCurrent: json['is_current'] == true,
      );
}

class StudentSchoolSummary {
  const StudentSchoolSummary(
      {required this.membershipId,
      required this.schoolName,
      required this.accessMode,
      required this.isCurrent});
  final int membershipId;
  final String schoolName, accessMode;
  final bool isCurrent;
  factory StudentSchoolSummary.fromJson(Map<String, dynamic> json) {
    final school = json['school'] is Map ? json['school'] as Map : const {};
    return StudentSchoolSummary(
      membershipId: (json['membership_id'] as num?)?.toInt() ?? 0,
      schoolName: (school['name'] ?? '').toString(),
      accessMode: (json['access_mode'] ?? '').toString(),
      isCurrent: json['is_current'] == true,
    );
  }
}

String? _nestedName(Object? value) {
  if (value is! Map) return null;
  final name = value['name']?.toString().trim();
  return name == null || name.isEmpty ? null : name;
}
