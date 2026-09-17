import 'package:flutter_test/flutter_test.dart';
import 'package:school_saas_mobile/features/teacher/exams/domain/teacher_exam_models.dart';

void main() {
  test('teacher exam parses the canonical exam contract', () {
    final exam = TeacherExam.fromJson({
      'id': 41,
      'academic_year': 7,
      'academic_term': 9,
      'teacher_assignment': 12,
      'exam_type': 3,
      'title': 'اختبار قصير',
      'exam_date': '2026-09-20',
      'total_marks': '20.00',
      'status': 'draft',
      'notes': 'الفصل الأول',
      'classroom_id': 5,
      'section_id': 6,
      'subject_id': 8,
    });

    expect(exam.id, 41);
    expect(exam.assignmentId, 12);
    expect(exam.totalMarks, 20);
    expect(exam.status, 'draft');
  });

  test('teacher result preserves status and workflow fields', () {
    final result = TeacherExamResult.fromJson({
      'id': 91,
      'exam': 41,
      'student_enrollment': 101,
      'student_name': 'طالب تجريبي',
      'student_code': 'S-1',
      'score': null,
      'status': 'excused',
      'remarks': 'عذر معتمد',
      'workflow_status': 'draft',
    });

    expect(result.status, 'excused');
    expect(result.score, isNull);
    expect(result.editable, isTrue);
  });

  test('all five result statuses map to Arabic labels', () {
    expect(teacherResultStatusLabels.keys, {
      'not_graded',
      'present',
      'absent',
      'excused',
      'exempted',
    });
  });

  group('teacher result local edit state', () {
    TeacherExamResultEditState presentDraft() => TeacherExamResultEditState(
          enrollmentId: 101,
          resultId: 91,
          status: 'present',
          scoreText: '17.5',
          remarks: 'ملاحظة',
          workflowStatus: 'draft',
        );

    for (final status in const ['absent', 'excused', 'exempted']) {
      test('present to $status hides score and emits a null score', () {
        final draft = presentDraft()..selectStatus(status);

        expect(draft.usesScore, isFalse);
        expect(draft.scoreText, isEmpty);
        expect(draft.toDraft().score, isNull);
      });

      test('$status to present immediately enables an empty score', () {
        final draft = presentDraft()
          ..selectStatus(status)
          ..selectStatus('present');

        expect(draft.usesScore, isTrue);
        expect(draft.scoreText, isEmpty);
      });
    }

    test('present owns its numeric payload score', () {
      final draft = presentDraft();

      expect(draft.usesScore, isTrue);
      expect(draft.toDraft().score, 17.5);
    });

    test('multiple status toggles never restore a stale score', () {
      final draft = presentDraft()
        ..selectStatus('absent')
        ..selectStatus('present')
        ..selectStatus('excused')
        ..selectStatus('present')
        ..selectStatus('exempted');

      expect(draft.usesScore, isFalse);
      expect(draft.scoreText, isEmpty);
      expect(draft.toDraft().score, isNull);
    });

    test('canonical submitted response immediately makes state read only', () {
      final draft = presentDraft();
      draft.applyCanonical(TeacherExamResult(
        id: 91,
        examId: 41,
        enrollmentId: 101,
        studentName: 'طالب تجريبي',
        studentCode: 'S-1',
        status: 'present',
        workflowStatus: 'submitted',
        score: 17.5,
      ));

      expect(draft.workflowStatus, 'submitted');
      expect(draft.editable, isFalse);
      expect(draft.submittable, isFalse);
    });

    test('failed submit leaves the existing editable draft unchanged', () {
      final draft = presentDraft();

      expect(draft.workflowStatus, 'draft');
      expect(draft.editable, isTrue);
      expect(draft.scoreText, '17.5');
    });

    test('ordinary canonical save remains an editable draft', () {
      final draft = presentDraft();
      draft.applyCanonical(TeacherExamResult(
        id: 91,
        examId: 41,
        enrollmentId: 101,
        studentName: 'طالب تجريبي',
        studentCode: 'S-1',
        status: 'present',
        workflowStatus: 'draft',
        score: 17.5,
      ));

      expect(draft.workflowStatus, 'draft');
      expect(draft.editable, isTrue);
      expect(draft.submittable, isTrue);
    });
  });
}
