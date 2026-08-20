enum StudentAttendanceStatus { present, absent, late, excused }

extension StudentAttendanceStatusX on StudentAttendanceStatus {
  String get apiValue => name;
  String get label => switch (this) {
        StudentAttendanceStatus.present => 'حاضر',
        StudentAttendanceStatus.absent => 'غائب',
        StudentAttendanceStatus.late => 'متأخر',
        StudentAttendanceStatus.excused => 'بعذر',
      };
}

StudentAttendanceStatus _status(Object? value) => switch (value?.toString()) {
      'absent' => StudentAttendanceStatus.absent,
      'late' => StudentAttendanceStatus.late,
      'excused' => StudentAttendanceStatus.excused,
      _ => StudentAttendanceStatus.present,
    };

class AttendanceTerm {
  const AttendanceTerm({
    required this.id,
    required this.name,
    required this.type,
    required this.startDate,
    required this.endDate,
    required this.isActive,
  });
  final int id;
  final String name;
  final String type;
  final DateTime startDate;
  final DateTime endDate;
  final bool isActive;

  factory AttendanceTerm.fromJson(Map<String, dynamic> json) => AttendanceTerm(
        id: (json['id'] as num).toInt(),
        name: json['name']?.toString() ?? '',
        type: json['term_type']?.toString() ?? '',
        startDate: DateTime.parse(json['start_date'].toString()),
        endDate: DateTime.parse(json['end_date'].toString()),
        isActive: json['is_active'] == true,
      );
}

class StudentAttendanceRecord {
  const StudentAttendanceRecord({
    required this.id,
    required this.date,
    required this.status,
    required this.termId,
    required this.termName,
    this.note = '',
  });
  final int id;
  final DateTime date;
  final StudentAttendanceStatus status;
  final int termId;
  final String termName;
  final String note;

  factory StudentAttendanceRecord.fromJson(Map<String, dynamic> json) {
    final term = Map<String, dynamic>.from(
        (json['academic_term_detail'] as Map?) ?? const <String, dynamic>{});
    return StudentAttendanceRecord(
      id: (json['id'] as num).toInt(),
      date: DateTime.parse(json['attendance_date'].toString()),
      status: _status(json['status']),
      termId: (json['academic_term'] as num?)?.toInt() ?? 0,
      termName: term['name']?.toString() ?? '',
      note: json['note']?.toString() ?? '',
    );
  }
}

class AttendanceSummary {
  const AttendanceSummary({
    required this.total,
    required this.present,
    required this.absent,
    required this.late,
    required this.excused,
  });
  final int total;
  final int present;
  final int absent;
  final int late;
  final int excused;

  int get attended => present + late;
  double get percentage => total == 0 ? 0 : attended * 100 / total;
}

class StudentAttendanceData {
  const StudentAttendanceData({
    required this.studentName,
    required this.studentCode,
    required this.academicYearName,
    required this.terms,
    required this.records,
    required this.lastUpdated,
    this.offline = false,
  });
  final String studentName;
  final String studentCode;
  final String academicYearName;
  final List<AttendanceTerm> terms;
  final List<StudentAttendanceRecord> records;
  final DateTime lastUpdated;
  final bool offline;

  factory StudentAttendanceData.fromJson(
      Map<String, dynamic> json, DateTime syncedAt, {bool offline = false}) {
    final student = Map<String, dynamic>.from(
        (json['student'] as Map?) ?? const <String, dynamic>{});
    final year = Map<String, dynamic>.from(
        (json['academic_year'] as Map?) ?? const <String, dynamic>{});
    return StudentAttendanceData(
      studentName: student['full_name']?.toString() ?? '',
      studentCode: student['student_code']?.toString() ?? '',
      academicYearName: year['name']?.toString() ?? '',
      terms: ((json['terms'] as List?) ?? const [])
          .map((e) => AttendanceTerm.fromJson(Map<String, dynamic>.from(e as Map)))
          .toList(),
      records: ((json['records'] as List?) ?? const [])
          .map((e) => StudentAttendanceRecord.fromJson(Map<String, dynamic>.from(e as Map)))
          .toList(),
      lastUpdated: syncedAt,
      offline: offline,
    );
  }

  StudentAttendanceData copyWith({bool? offline}) => StudentAttendanceData(
        studentName: studentName,
        studentCode: studentCode,
        academicYearName: academicYearName,
        terms: terms,
        records: records,
        lastUpdated: lastUpdated,
        offline: offline ?? this.offline,
      );
}
