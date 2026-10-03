import 'package:dio/dio.dart';
import 'package:drift/native.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:school_saas_mobile/core/local_database/app_database.dart';
import 'package:school_saas_mobile/features/parent/data/parent_homework_repository.dart';
import 'package:school_saas_mobile/features/parent/domain/parent_homework_models.dart';
import 'package:school_saas_mobile/features/parent/presentation/parent_homework_controller.dart';
import 'package:school_saas_mobile/features/parent/presentation/parent_homework_screens.dart';
import 'package:school_saas_mobile/features/parent_shell/parent_shell.dart';

const scope = CacheScope(
  localUserKey: 'user:7',
  membershipId: 41,
  academicYearKey: '8',
);

Map<String, dynamic> homeworkJson({
  int id = 24,
  String completion = 'submitted',
  String? submissionStatus = 'submitted',
}) =>
    {
      'id': id,
      'title': 'حل تمارين الفصل',
      'description': 'حل الأسئلة من الكتاب',
      'subject_name': 'الرياضيات',
      'teacher': 'أ. أحمد',
      'status': 'published',
      'submission_type': 'text',
      'published_at': '2026-09-20T08:00:00Z',
      'due_date': '2026-10-10T20:00:00Z',
      'completion_status': completion,
      'submission_status': submissionStatus,
      'submitted_at': '2026-10-02T09:30:00Z',
      'graded_at': completion == 'graded' ? '2026-10-03T10:00:00Z' : null,
      'grade': completion == 'graded' ? '18.00' : null,
      'max_grade': '20.00',
      'teacher_note': completion == 'returned' ? 'راجع الإجابة' : '',
      'is_overdue': completion == 'overdue',
      'attachments': [
        {
          'id': 3,
          'original_name': 'worksheet.pdf',
          'file': '/media/worksheet.pdf',
          'content_type': 'application/pdf',
          'file_size': 1200,
        }
      ],
    };

Map<String, dynamic> submissionJson(String status) => {
      'id': 9,
      'homework': 24,
      'student_id': 1,
      'answer': 'إجابة الطالب',
      'status': status,
      'submitted_at': '2026-10-02T09:30:00Z',
      'grade': status == 'graded' ? '18.00' : null,
      'teacher_note': status == 'returned' ? 'راجع الإجابة' : '',
      'graded_at': status == 'graded' ? '2026-10-03T10:00:00Z' : null,
      'returned_at': status == 'returned' ? '2026-10-03T10:00:00Z' : null,
      'is_late': false,
      'attachments': const [],
    };

Widget app(Widget child) => MaterialApp(
      home: Directionality(
        textDirection: TextDirection.rtl,
        child: Scaffold(body: SafeArea(child: child)),
      ),
    );

void main() {
  test('list uses exact parent-child endpoint and active academic year',
      () async {
    final requests = <RequestOptions>[];
    final dio = Dio()
      ..interceptors.add(InterceptorsWrapper(onRequest: (options, handler) {
        requests.add(options);
        handler.resolve(Response(
          requestOptions: options,
          data: {
            'count': 1,
            'results': [homeworkJson()]
          },
        ));
      }));
    final db = AppDatabase.forTesting(NativeDatabase.memory());
    addTearDown(db.close);

    final data = await ParentHomeworkRepository(dio, db).refreshList(scope, 1);

    expect(requests.single.path, 'parents/me/children/1/homework/');
    expect(requests.single.queryParameters['academic_year_id'], 8);
    expect(data.items.single.title, 'حل تمارين الفصل');
  });

  test('detail requests only the selected child submission', () async {
    final requests = <RequestOptions>[];
    final dio = Dio()
      ..interceptors.add(InterceptorsWrapper(onRequest: (options, handler) {
        requests.add(options);
        handler.resolve(Response(
          requestOptions: options,
          data: {
            'count': 1,
            'results': [submissionJson('returned')]
          },
        ));
      }));
    final db = AppDatabase.forTesting(NativeDatabase.memory());
    addTearDown(db.close);
    final item = ParentHomework.fromJson(homeworkJson(completion: 'returned'));

    final detail =
        await ParentHomeworkRepository(dio, db).refreshDetail(scope, 1, item);

    expect(requests.single.path, 'homework-submissions/');
    expect(
        requests.single.queryParameters, containsPair('homework_id', item.id));
    expect(requests.single.queryParameters, containsPair('student_id', 1));
    expect(detail.submission?.answer, 'إجابة الطالب');
    expect(detail.submission?.teacherNote, 'راجع الإجابة');
  });

  test('preserves every backend homework lifecycle status', () {
    const statuses = [
      'not_started',
      'draft',
      'submitted',
      'returned',
      'reviewed',
      'graded',
      'overdue',
      'closed_without_submission',
      'view_only',
    ];
    expect(
      statuses
          .map((status) => ParentHomework.fromJson(
                homeworkJson(completion: status),
              ).completionStatus.apiValue)
          .toList(),
      statuses,
    );
  });

  test('list cache is isolated by child membership and academic year',
      () async {
    final dio = Dio()
      ..interceptors.add(InterceptorsWrapper(onRequest: (options, handler) {
        handler.resolve(Response(
          requestOptions: options,
          data: {
            'count': 1,
            'results': [homeworkJson()]
          },
        ));
      }));
    final db = AppDatabase.forTesting(NativeDatabase.memory());
    addTearDown(db.close);
    final repository = ParentHomeworkRepository(dio, db);
    await repository.refreshList(scope, 1);

    expect(await repository.readList(scope, 2), isNull);
    expect(
      await repository.readList(
        const CacheScope(
          localUserKey: 'user:99',
          membershipId: 41,
          academicYearKey: '8',
        ),
        1,
      ),
      isNull,
    );
    expect(
      await repository.readList(
        const CacheScope(
          localUserKey: 'user:7',
          membershipId: 99,
          academicYearKey: '8',
        ),
        1,
      ),
      isNull,
    );
    expect(
      await repository.readList(
        const CacheScope(
          localUserKey: 'user:7',
          membershipId: 41,
          academicYearKey: '9',
        ),
        1,
      ),
      isNull,
    );
  });

  test('detail cache is isolated by selected child', () async {
    final dio = Dio()
      ..interceptors.add(InterceptorsWrapper(onRequest: (options, handler) {
        handler.resolve(Response(
          requestOptions: options,
          data: {
            'count': 1,
            'results': [submissionJson('reviewed')]
          },
        ));
      }));
    final db = AppDatabase.forTesting(NativeDatabase.memory());
    addTearDown(db.close);
    final repository = ParentHomeworkRepository(dio, db);
    final item = ParentHomework.fromJson(homeworkJson(completion: 'reviewed'));
    await repository.refreshDetail(scope, 1, item);

    expect(await repository.readDetail(scope, 1, item.id), isNotNull);
    expect(await repository.readDetail(scope, 2, item.id), isNull);
  });

  test('offline fallback uses only matching child cache', () async {
    final db = AppDatabase.forTesting(NativeDatabase.memory());
    addTearDown(db.close);
    final online = Dio()
      ..interceptors.add(InterceptorsWrapper(onRequest: (options, handler) {
        handler.resolve(Response(
          requestOptions: options,
          data: {
            'count': 1,
            'results': [homeworkJson()]
          },
        ));
      }));
    await ParentHomeworkRepository(online, db).refreshList(scope, 1);
    final offline = Dio()
      ..interceptors.add(InterceptorsWrapper(onRequest: (options, handler) {
        handler.reject(DioException(
          requestOptions: options,
          type: DioExceptionType.connectionError,
        ));
      }));

    final cached =
        await ParentHomeworkRepository(offline, db).loadList(scope, 1);
    expect(cached.offline, isTrue);
    expect(ParentHomeworkRepository(offline, db).loadList(scope, 2),
        throwsA(isA<DioException>()));
  });

  testWidgets('list renders loading error empty offline and historical states',
      (tester) async {
    await tester.pumpWidget(app(ParentHomeworkListScreen(
      state: const ParentHomeworkLoading(),
      childName: 'أحمد',
      historical: false,
      onRefresh: () async {},
      onOpen: (_) {},
    )));
    expect(find.byType(CircularProgressIndicator), findsOneWidget);

    await tester.pumpWidget(app(ParentHomeworkListScreen(
      state: const ParentHomeworkFailure('تعذر تحميل الواجبات'),
      childName: 'أحمد',
      historical: false,
      onRefresh: () async {},
      onOpen: (_) {},
    )));
    expect(find.text('إعادة المحاولة'), findsOneWidget);

    await tester.pumpWidget(app(ParentHomeworkListScreen(
      state: ParentHomeworkReady(ParentHomeworkListData(
        const [],
        DateTime.utc(2026, 10, 3),
        offline: true,
      )),
      childName: 'أحمد',
      historical: true,
      onRefresh: () async {},
      onOpen: (_) {},
    )));
    expect(find.text('لا توجد واجبات'), findsOneWidget);
    expect(find.textContaining('بيانات محفوظة'), findsAtLeastNWidgets(1));
    expect(find.textContaining('للقراءة فقط'), findsOneWidget);
  });

  testWidgets('detail displays answer review grade and attachments read-only',
      (tester) async {
    final item = ParentHomework.fromJson(homeworkJson(completion: 'graded'));
    final detail = ParentHomeworkDetailData(
      item,
      ParentHomeworkSubmission.fromJson(submissionJson('graded')),
      DateTime.utc(2026, 10, 3),
    );
    await tester.pumpWidget(app(ParentHomeworkDetailScreen(
      state: ParentHomeworkDetailReady(detail),
      childName: 'أحمد',
      historical: false,
      onRefresh: () async {},
    )));

    expect(find.text('إجابة الطالب'), findsOneWidget);
    expect(find.textContaining('18'), findsAtLeastNWidgets(1));
    expect(find.text('worksheet.pdf'), findsOneWidget);
    expect(find.byType(TextField), findsNothing);
  });

  testWidgets('Parent navigation adds Homework only', (tester) async {
    await tester.pumpWidget(app(ParentBottomNavigation(
      selectedIndex: 0,
      onSelected: (_) {},
    )));
    for (final label in [
      'الرئيسية',
      'الجدول',
      'الحضور',
      'الواجبات',
      'المزيد'
    ]) {
      expect(find.text(label), findsOneWidget);
    }
    for (final deferred in ['النتائج', 'الرسائل', 'الإشعارات']) {
      expect(find.text(deferred), findsNothing);
    }
  });
}
