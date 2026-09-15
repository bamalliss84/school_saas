import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:school_saas_mobile/features/teacher/homework/data/teacher_homework_repository.dart';
import 'package:school_saas_mobile/features/teacher/homework/domain/teacher_homework_models.dart';
import 'package:school_saas_mobile/features/teacher/homework/presentation/teacher_homework_controller.dart';
import 'package:school_saas_mobile/features/teacher/homework/presentation/teacher_homework_screen.dart';

Map<String, dynamic> submissionJson({String status = 'submitted'}) => {
      'id': 31,
      'student_name': 'الطالب أحمد',
      'student_code': 'S-31',
      'answer': 'إجابة الطالب',
      'status': status,
      'grade': status == 'graded' ? '8' : null,
      'teacher_note': status == 'reviewed' ? 'تمت المراجعة' : '',
      'attachments': const [],
    };

Map<String, dynamic> studentJson({
  String status = 'submitted',
  bool canGrade = false,
  bool canReview = false,
  bool canReturn = true,
  String? maxGrade,
}) =>
    {
      'student_name': 'الطالب أحمد',
      'student_code': 'S-31',
      'status': status,
      'submission_id': 31,
      'grade': status == 'graded' ? '8' : null,
      'max_grade': maxGrade,
      'teacher_note': status == 'reviewed' ? 'تمت المراجعة' : '',
      'is_late': false,
      'can_grade': canGrade,
      'can_review': canReview,
      'can_return': canReturn,
    };

TeacherHomework homework({
  String? maxGrade,
  String submissionType = 'text',
}) =>
    TeacherHomework.fromJson({
      'id': 7,
      'teacher_assignment': 3,
      'title': 'واجب تكويني',
      'description': '',
      'subject_name': 'الرياضيات',
      'classroom_id': 6,
      'section_id': 1,
      'status': 'published',
      'submission_type': submissionType,
      'due_date': '2026-09-20T10:00:00Z',
      'max_grade': maxGrade,
      'can_edit': false,
      'can_publish': false,
      'can_close': true,
      'attachments': const [],
    });

Dio rosterDio({String status = 'not_started'}) {
  final dio = Dio(BaseOptions(baseUrl: 'https://example.test/api/v1/'));
  dio.interceptors.add(InterceptorsWrapper(onRequest: (options, handler) {
    handler.resolve(Response<Map<String, dynamic>>(
      requestOptions: options,
      statusCode: 200,
      data: {
        'total_students': 1,
        'not_started_count': status == 'not_started' ? 1 : 0,
        'pending_grading_count': status == 'submitted' ? 1 : 0,
        'reviewed_count': 0,
        'students': [
          studentJson(
            status: status,
            canReturn: status == 'submitted',
          ),
        ],
      },
    ));
  }));
  return dio;
}

Future<void> pumpRoster(
  WidgetTester tester, {
  required TeacherHomework item,
  String status = 'not_started',
}) async {
  await tester.pumpWidget(ProviderScope(
    overrides: [
      teacherHomeworkRepositoryProvider.overrideWithValue(
        TeacherHomeworkRepository(rosterDio(status: status)),
      ),
    ],
    child: MaterialApp(
      home: TeacherHomeworkStudents(homework: item, historical: false),
    ),
  ));
  await tester.pumpAndSettle();
}

Dio fakeDio({String submissionStatus = 'submitted'}) {
  final dio = Dio(BaseOptions(baseUrl: 'https://example.test/api/v1/'));
  dio.interceptors.add(InterceptorsWrapper(onRequest: (options, handler) {
    handler.resolve(Response<Map<String, dynamic>>(
      requestOptions: options,
      statusCode: 200,
      data: submissionJson(status: submissionStatus),
    ));
  }));
  return dio;
}

Future<void> pumpSubmission(
  WidgetTester tester, {
  required TeacherHomeworkStudent student,
  required TeacherHomework item,
  String submissionStatus = 'submitted',
}) async {
  await tester.pumpWidget(ProviderScope(
    overrides: [
      teacherHomeworkRepositoryProvider.overrideWithValue(
        TeacherHomeworkRepository(fakeDio(
          submissionStatus: submissionStatus,
        )),
      ),
    ],
    child: MaterialApp(
      home: TeacherSubmissionScreen(
        student: student,
        homework: item,
        historical: false,
      ),
    ),
  ));
  await tester.pumpAndSettle();
}

void main() {
  test('teacher roster parses reviewed lifecycle projections', () {
    final status = TeacherStudentStatus.fromJson({
      'reviewed_count': 1,
      'students': [studentJson(status: 'reviewed')],
    });
    expect(status.count('reviewed_count'), 1);
    expect(status.students.single.status, 'reviewed');
    expect(status.students.single.canReview, isFalse);
    expect(status.students.single.canReturn, isTrue);
  });

  test('review repository uses review endpoint and teacher-note-only payload',
      () async {
    late RequestOptions request;
    final dio = Dio(BaseOptions(baseUrl: 'https://example.test/api/v1/'));
    dio.interceptors.add(InterceptorsWrapper(onRequest: (options, handler) {
      request = options;
      handler.resolve(Response<Map<String, dynamic>>(
        requestOptions: options,
        statusCode: 200,
        data: submissionJson(status: 'reviewed'),
      ));
    }));
    final result = await TeacherHomeworkRepository(dio).review(31, 'جيد');
    expect(request.method, 'POST');
    expect(request.path, 'homework-submissions/31/review/');
    expect(request.data, {'teacher_note': 'جيد'});
    expect(result.status, 'reviewed');
    expect(result.grade, isNull);
  });

  testWidgets('submitted ungraded work shows review without numeric grade',
      (tester) async {
    await pumpSubmission(
      tester,
      student: TeacherHomeworkStudent.fromJson(
        studentJson(canReview: true),
      ),
      item: homework(),
    );
    expect(find.text('اعتماد المراجعة'), findsOneWidget);
    expect(find.textContaining('الدرجة من'), findsNothing);
    expect(find.text('ملاحظات المعلم'), findsOneWidget);
    expect(find.text('إعادة للتعديل'), findsOneWidget);
  });

  testWidgets('reviewed work hides review and keeps backend-authorized return',
      (tester) async {
    await pumpSubmission(
      tester,
      student: TeacherHomeworkStudent.fromJson(
        studentJson(status: 'reviewed'),
      ),
      item: homework(),
      submissionStatus: 'reviewed',
    );
    expect(find.text('تمت المراجعة'), findsWidgets);
    expect(find.text('اعتماد المراجعة'), findsNothing);
    expect(find.text('إعادة للتعديل'), findsOneWidget);
    expect(find.textContaining('الدرجة من'), findsNothing);
  });

  testWidgets('graded homework preserves numeric grading flow', (tester) async {
    await pumpSubmission(
      tester,
      student: TeacherHomeworkStudent.fromJson(studentJson(
        canGrade: true,
        maxGrade: '10',
      )),
      item: homework(maxGrade: '10'),
    );
    expect(find.text('حفظ التصحيح'), findsOneWidget);
    expect(find.text('الدرجة من 10.0'), findsOneWidget);
    expect(find.text('اعتماد المراجعة'), findsNothing);
  });

  testWidgets('view-only roster shows non-submission semantics',
      (tester) async {
    await pumpRoster(
      tester,
      item: homework(submissionType: 'none'),
    );
    expect(find.text('لا يتطلب تسليم'), findsWidgets);
    expect(find.text('لم يبدأ'), findsNothing);
  });

  testWidgets('normal roster preserves backend submission status',
      (tester) async {
    await pumpRoster(
      tester,
      item: homework(),
      status: 'submitted',
    );
    expect(find.text('تم التسليم'), findsWidgets);
    expect(find.text('لا يتطلب تسليم'), findsNothing);
  });
}
