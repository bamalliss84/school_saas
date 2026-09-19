class StudentResult {
  const StudentResult({
    required this.id,
    required this.examId,
    required this.examTitle,
    required this.subject,
    required this.examDate,
    required this.examTypeId,
    required this.examTypeName,
    required this.examTypeCode,
    required this.totalMarks,
    required this.status,
    required this.academicTermId,
    required this.academicTermName,
    required this.isPublished,
    this.score,
    this.percentage,
    this.remarks = '',
    this.publishedAt,
  });

  final int id;
  final int examId;
  final String examTitle;
  final String subject;
  final DateTime examDate;
  final int examTypeId;
  final String examTypeName;
  final String examTypeCode;
  final double totalMarks;
  final double? score;
  final double? percentage;
  final String status;
  final int academicTermId;
  final String academicTermName;
  final String remarks;
  final bool isPublished;
  final DateTime? publishedAt;

  bool get hasScore => status == 'present' && score != null;
  String get scoreLabel =>
      hasScore ? '${_number(score!)} من ${_number(totalMarks)}' : _statusLabel(status);
  String get percentageLabel =>
      hasScore && percentage != null ? '${_number(percentage!)}%' : '';

  factory StudentResult.fromJson(Map<String, dynamic> json) => StudentResult(
        id: (json['id'] as num).toInt(),
        examId: (json['exam'] as num).toInt(),
        examTitle: json['exam_title']?.toString() ?? '',
        subject: json['subject_name']?.toString() ?? '',
        examDate: DateTime.parse(json['exam_date'].toString()),
        examTypeId: (json['exam_type_id'] as num?)?.toInt() ?? 0,
        examTypeName: json['exam_type_name']?.toString() ?? '',
        examTypeCode: json['exam_type_code']?.toString() ?? '',
        totalMarks: double.tryParse(json['total_marks']?.toString() ?? '') ?? 0,
        score: double.tryParse(json['score']?.toString() ?? ''),
        percentage: double.tryParse(json['percentage']?.toString() ?? ''),
        status: json['status']?.toString() ?? 'not_graded',
        academicTermId: (json['academic_term_id'] as num?)?.toInt() ?? 0,
        academicTermName: json['academic_term_name']?.toString() ?? '',
        remarks: json['remarks']?.toString() ?? '',
        isPublished: json['is_published'] == true,
        publishedAt: _date(json['published_at']),
      );
}

String _number(double value) =>
    value == value.roundToDouble() ? value.toInt().toString() : value.toStringAsFixed(1);

String _statusLabel(String status) => switch (status) {
      'absent' => 'غائب',
      'excused' => 'غياب بعذر',
      'exempted' => 'معفي',
      _ => 'لم ترصد الدرجة',
    };

DateTime? _date(Object? value) =>
    value == null ? null : DateTime.tryParse(value.toString());
