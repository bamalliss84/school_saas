class ParentResult {
  const ParentResult({
    required this.id,
    required this.examId,
    required this.enrollmentId,
    required this.examTitle,
    required this.subject,
    required this.examDate,
    required this.examTypeName,
    required this.totalMarks,
    required this.status,
    required this.termName,
    required this.isPublished,
    this.score,
    this.percentage,
    this.remarks = '',
    this.publishedAt,
  });

  final int id;
  final int examId;
  final int enrollmentId;
  final String examTitle;
  final String subject;
  final DateTime examDate;
  final String examTypeName;
  final double totalMarks;
  final double? score;
  final double? percentage;
  final String status;
  final String termName;
  final String remarks;
  final bool isPublished;
  final DateTime? publishedAt;

  bool get hasScore => status == 'present' && score != null;
  String get scoreLabel => hasScore
      ? '${_number(score!)} من ${_number(totalMarks)}'
      : switch (status) {
          'absent' => 'غائب',
          'excused' => 'غياب بعذر',
          'exempted' => 'معفي',
          _ => 'لم ترصد الدرجة',
        };
  String get percentageLabel =>
      hasScore && percentage != null ? '${_number(percentage!)}%' : '';

  factory ParentResult.fromJson(Map<String, dynamic> json) => ParentResult(
        id: (json['id'] as num).toInt(),
        examId: (json['exam'] as num).toInt(),
        enrollmentId: (json['student_enrollment'] as num).toInt(),
        examTitle: json['exam_title']?.toString() ?? '',
        subject: json['subject_name']?.toString() ?? '',
        examDate: DateTime.parse(json['exam_date'].toString()),
        examTypeName: json['exam_type_name']?.toString() ?? '',
        totalMarks:
            double.tryParse(json['total_marks']?.toString() ?? '') ?? 0,
        score: double.tryParse(json['score']?.toString() ?? ''),
        percentage: double.tryParse(json['percentage']?.toString() ?? ''),
        status: json['status']?.toString() ?? 'not_graded',
        termName: json['academic_term_name']?.toString() ?? '',
        remarks: json['remarks']?.toString() ?? '',
        isPublished: json['is_published'] == true,
        publishedAt: _date(json['published_at']),
      );

  Map<String, Object?> toJson() => {
        'id': id,
        'exam': examId,
        'student_enrollment': enrollmentId,
        'exam_title': examTitle,
        'subject_name': subject,
        'exam_date': examDate.toIso8601String().split('T').first,
        'exam_type_name': examTypeName,
        'total_marks': totalMarks,
        'score': score,
        'percentage': percentage,
        'status': status,
        'academic_term_name': termName,
        'remarks': remarks,
        'is_published': isPublished,
        'published_at': publishedAt?.toIso8601String(),
      };
}

String _number(double value) => value == value.roundToDouble()
    ? value.toInt().toString()
    : value.toStringAsFixed(1);

DateTime? _date(Object? value) =>
    value == null ? null : DateTime.tryParse(value.toString());
