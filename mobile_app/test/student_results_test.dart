import 'package:flutter_test/flutter_test.dart';
import 'package:school_saas_mobile/features/student/results/domain/result_models.dart';

void main() {
  test('student result parses score total percentage and feedback contract', () {
    final result = StudentResult.fromJson({
      'id': 7,
      'exam': 3,
      'exam_title': 'اختبار منتصف الفصل',
      'subject_name': 'الرياضيات',
      'exam_date': '2026-08-19',
      'exam_type_id': 5,
      'exam_type_name': 'اختبار منتصف الفصل',
      'exam_type_code': 'MIDTERM',
      'total_marks': '20.00',
      'score': '18.00',
      'percentage': '90.00',
      'status': 'present',
      'academic_term_id': 2,
      'academic_term_name': 'الفصل الدراسي الأول',
      'remarks': 'أداء ممتاز',
      'is_published': true,
      'published_at': '2026-08-22T08:00:00Z',
    });

    expect(result.scoreLabel, '18 / 20');
    expect(result.percentageLabel, '90%');
    expect(result.examTypeName, 'اختبار منتصف الفصل');
    expect(result.examTypeCode, 'MIDTERM');
    expect(result.remarks, 'أداء ممتاز');
    expect(result.isPublished, isTrue);
  });

  test('student result shows attendance-style result status without fake score', () {
    final result = StudentResult.fromJson({
      'id': 8,
      'exam': 4,
      'exam_title': 'اختبار قصير',
      'subject_name': 'العلوم',
      'exam_date': '2026-08-20',
      'exam_type_id': 6,
      'exam_type_name': 'اختبار قصير',
      'exam_type_code': 'QUIZ',
      'total_marks': '10.00',
      'score': null,
      'percentage': null,
      'status': 'absent',
      'academic_term_id': 2,
      'academic_term_name': 'الفصل الدراسي الأول',
      'is_published': true,
    });
    expect(result.scoreLabel, 'غائب');
    expect(result.percentageLabel, '');
  });
}
