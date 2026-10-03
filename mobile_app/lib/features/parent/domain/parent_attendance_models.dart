enum ParentAttendanceStatus {
  present('present', 'حاضر'),
  absent('absent', 'غائب'),
  late('late', 'متأخر'),
  excused('excused', 'بعذر');

  const ParentAttendanceStatus(this.apiValue, this.arabicLabel);
  final String apiValue;
  final String arabicLabel;

  static ParentAttendanceStatus fromApi(Object? value) => values.firstWhere(
        (item) => item.apiValue == value,
        orElse: () => present,
      );
}

class ParentAttendanceRecord {
  const ParentAttendanceRecord({
    required this.id,
    required this.date,
    required this.status,
    required this.termName,
    required this.note,
  });

  final int id;
  final DateTime date;
  final ParentAttendanceStatus status;
  final String termName;
  final String note;

  factory ParentAttendanceRecord.fromJson(Map<String, dynamic> json) =>
      ParentAttendanceRecord(
        id: (json['id'] as num?)?.toInt() ?? 0,
        date: DateTime.parse(json['attendance_date'].toString()),
        status: ParentAttendanceStatus.fromApi(json['status']),
        termName: _map(json['academic_term_detail'])['name']?.toString() ?? '',
        note: json['note']?.toString() ?? '',
      );
}

class ParentAttendanceData {
  const ParentAttendanceData({
    required this.studentId,
    required this.studentName,
    required this.totalRecords,
    required this.presentCount,
    required this.absentCount,
    required this.lateCount,
    required this.excusedCount,
    required this.attendancePercentage,
    required this.records,
    required this.lastUpdated,
    this.offline = false,
  });

  final int studentId;
  final String studentName;
  final int totalRecords;
  final int presentCount;
  final int absentCount;
  final int lateCount;
  final int excusedCount;
  final double attendancePercentage;
  final List<ParentAttendanceRecord> records;
  final DateTime lastUpdated;
  final bool offline;

  factory ParentAttendanceData.fromJson(
    Map<String, dynamic> json,
    DateTime lastUpdated, {
    bool offline = false,
  }) {
    final student = _map(json['student']);
    return ParentAttendanceData(
      studentId: (student['id'] as num?)?.toInt() ?? 0,
      studentName: student['full_name']?.toString() ?? '',
      totalRecords: (json['total_records'] as num?)?.toInt() ?? 0,
      presentCount: (json['present_count'] as num?)?.toInt() ?? 0,
      absentCount: (json['absent_count'] as num?)?.toInt() ?? 0,
      lateCount: (json['late_count'] as num?)?.toInt() ?? 0,
      excusedCount: (json['excused_count'] as num?)?.toInt() ?? 0,
      attendancePercentage:
          (json['attendance_percentage'] as num?)?.toDouble() ?? 0,
      records: (json['records'] as List? ?? const [])
          .whereType<Map>()
          .map((item) => ParentAttendanceRecord.fromJson(
              Map<String, dynamic>.from(item)))
          .toList(growable: false),
      lastUpdated: lastUpdated,
      offline: offline,
    );
  }

  ParentAttendanceData copyWith({bool? offline}) => ParentAttendanceData(
        studentId: studentId,
        studentName: studentName,
        totalRecords: totalRecords,
        presentCount: presentCount,
        absentCount: absentCount,
        lateCount: lateCount,
        excusedCount: excusedCount,
        attendancePercentage: attendancePercentage,
        records: records,
        lastUpdated: lastUpdated,
        offline: offline ?? this.offline,
      );
}

Map<String, dynamic> _map(Object? value) =>
    value is Map ? Map<String, dynamic>.from(value) : <String, dynamic>{};
