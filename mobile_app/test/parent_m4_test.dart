import 'package:dio/dio.dart';
import 'package:drift/native.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:school_saas_mobile/core/local_database/app_database.dart';
import 'package:school_saas_mobile/features/parent/data/parent_results_repository.dart';
import 'package:school_saas_mobile/features/parent/domain/parent_result_models.dart';
import 'package:school_saas_mobile/features/parent/presentation/parent_results_controller.dart';
import 'package:school_saas_mobile/features/parent/presentation/parent_results_screens.dart';
import 'package:school_saas_mobile/features/parent_shell/parent_shell.dart';

const scope = CacheScope(
  localUserKey: 'user:7',
  membershipId: 41,
  academicYearKey: '8',
);

Map<String, dynamic> resultJson({
  int id = 51,
  int enrollmentId = 101,
  String status = 'present',
  Object? score = '17.00',
  bool published = true,
  String workflowStatus = 'approved',
}) =>
    {
      'id': id,
      'exam': 12,
      'exam_title': 'اختبار منتصف الفصل',
      'student_enrollment': enrollmentId,
      'student_name': 'أحمد محمد',
      'student_code': 'A01',
      'subject_name': 'الرياضيات',
      'exam_date': '2026-09-20',
      'exam_type_id': 3,
      'exam_type_name': 'منتصف الفصل',
      'exam_type_code': 'MID',
      'total_marks': '20.00',
      'percentage': status == 'present' ? '85.00' : null,
      'academic_term_id': 6,
      'academic_term_name': 'الفصل الأول',
      'score': score,
      'status': status,
      'remarks': 'أداء جيد',
      'workflow_status': workflowStatus,
      'is_published': published,
      'published_at': '2026-09-22T08:00:00Z',
    };

Widget app(Widget child) => MaterialApp(
      home: Directionality(
        textDirection: TextDirection.rtl,
        child: Scaffold(body: SafeArea(child: child)),
      ),
    );

void main() {
  test(
      'loads selected child academic-year enrollment and ignores matching-date rows from other enrollments',
      () async {
    final requests = <RequestOptions>[];
    final dio = Dio()
      ..interceptors.add(InterceptorsWrapper(onRequest: (options, handler) {
        requests.add(options);
        handler.resolve(Response(
          requestOptions: options,
          data: {
            'count': 4,
            'results': [
              resultJson(),
              resultJson(id: 52, enrollmentId: 202),
              resultJson(id: 53, published: false),
              resultJson(id: 54, workflowStatus: 'pending_approval'),
            ],
          },
        ));
      }));
    final db = AppDatabase.forTesting(NativeDatabase.memory());
    addTearDown(db.close);

    final data = await ParentResultsRepository(dio, db)
        .refresh(scope, childId: 1, enrollmentId: 101);

    expect(
        requests.single.path, 'exam-results/reports/student/1/transcript/');
    expect(requests.single.method, 'GET');
    expect(data.items.map((item) => item.id), [51]);
    final cached = await ParentResultsRepository(dio, db)
        .read(scope, childId: 1, enrollmentId: 101);
    expect(cached!.items.map((item) => item.id), [51]);
  });

  test('parses scored and special-status results without fabricating zero', () {
    final present = ParentResult.fromJson(resultJson());
    final absent = ParentResult.fromJson(
      resultJson(status: 'absent', score: null),
    );
    expect(present.scoreLabel, '17 من 20');
    expect(absent.score, isNull);
    expect(absent.scoreLabel, 'غائب');
    expect(absent.scoreLabel, isNot(contains('0')));
  });

  test('cache is isolated by user membership year child and enrollment',
      () async {
    final dio = Dio()
      ..interceptors.add(InterceptorsWrapper(onRequest: (options, handler) {
        handler.resolve(Response(
          requestOptions: options,
          data: {
            'count': 1,
            'results': [resultJson()]
          },
        ));
      }));
    final db = AppDatabase.forTesting(NativeDatabase.memory());
    addTearDown(db.close);
    final repository = ParentResultsRepository(dio, db);
    await repository.refresh(scope, childId: 1, enrollmentId: 101);

    expect(await repository.read(scope, childId: 1, enrollmentId: 101),
        isNotNull);
    expect(await repository.read(scope, childId: 2, enrollmentId: 202), isNull);
    expect(await repository.read(scope, childId: 1, enrollmentId: 999), isNull);
    expect(
      await repository.read(
        const CacheScope(
          localUserKey: 'user:7',
          membershipId: 99,
          academicYearKey: '8',
        ),
        childId: 1,
        enrollmentId: 101,
      ),
      isNull,
    );
    expect(
      await repository.read(
        const CacheScope(
          localUserKey: 'user:7',
          membershipId: 41,
          academicYearKey: '9',
        ),
        childId: 1,
        enrollmentId: 101,
      ),
      isNull,
    );
  });

  test('offline fallback never crosses the selected child cache', () async {
    final db = AppDatabase.forTesting(NativeDatabase.memory());
    addTearDown(db.close);
    final online = Dio()
      ..interceptors.add(InterceptorsWrapper(onRequest: (options, handler) {
        handler.resolve(Response(
          requestOptions: options,
          data: {
            'count': 1,
            'results': [resultJson()]
          },
        ));
      }));
    await ParentResultsRepository(online, db)
        .refresh(scope, childId: 1, enrollmentId: 101);
    final offline = Dio()
      ..interceptors.add(InterceptorsWrapper(onRequest: (options, handler) {
        handler.reject(DioException(
          requestOptions: options,
          type: DioExceptionType.connectionError,
        ));
      }));
    final repository = ParentResultsRepository(offline, db);

    final cached =
        await repository.load(scope, childId: 1, enrollmentId: 101);
    expect(cached.offline, isTrue);
    expect(
      repository.load(scope, childId: 2, enrollmentId: 202),
      throwsA(isA<DioException>()),
    );
  });

  testWidgets('renders loading error empty offline and historical states',
      (tester) async {
    await tester.pumpWidget(app(ParentResultsScreen(
      state: const ParentResultsLoading(),
      childName: 'أحمد',
      historical: false,
      onRefresh: () async {},
      onOpen: (_) {},
    )));
    expect(find.byType(CircularProgressIndicator), findsOneWidget);

    await tester.pumpWidget(app(ParentResultsScreen(
      state: const ParentResultsFailure('تعذر تحميل النتائج'),
      childName: 'أحمد',
      historical: false,
      onRefresh: () async {},
      onOpen: (_) {},
    )));
    expect(find.text('إعادة المحاولة'), findsOneWidget);

    await tester.pumpWidget(app(ParentResultsScreen(
      state: ParentResultsReady(ParentResultsData(
        const [],
        DateTime.utc(2026, 10, 12),
        offline: true,
      )),
      childName: 'أحمد',
      historical: true,
      onRefresh: () async {},
      onOpen: (_) {},
    )));
    expect(find.text('لا توجد نتائج منشورة'), findsOneWidget);
    expect(find.textContaining('بيانات محفوظة'), findsAtLeastNWidgets(1));
    expect(find.textContaining('للقراءة فقط'), findsOneWidget);
  });

  testWidgets('detail presents official result read-only', (tester) async {
    final result = ParentResult.fromJson(resultJson());
    await tester.pumpWidget(app(ParentResultDetailScreen(
      result: result,
      historical: false,
    )));
    expect(find.text('اختبار منتصف الفصل'), findsOneWidget);
    expect(find.text('الرياضيات'), findsOneWidget);
    expect(find.text('17 من 20'), findsOneWidget);
    expect(find.text('أداء جيد'), findsOneWidget);
    expect(find.byType(TextField), findsNothing);
    expect(find.byType(FilledButton), findsNothing);
  });

  testWidgets('Parent navigation includes Results before More', (tester) async {
    await tester.pumpWidget(app(ParentBottomNavigation(
      selectedIndex: 0,
      onSelected: (_) {},
    )));
    final labels = ['الرئيسية', 'الجدول', 'الحضور', 'الواجبات', 'النتائج', 'المزيد'];
    for (final label in labels) {
      expect(find.text(label), findsOneWidget);
    }
    expect(
      tester.getCenter(find.text('النتائج')).dx,
      greaterThan(tester.getCenter(find.text('المزيد')).dx),
    );
  });
}
