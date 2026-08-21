import 'package:dio/dio.dart';
import 'package:drift/native.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:school_saas_mobile/core/local_database/app_database.dart';
import 'package:school_saas_mobile/features/student/attendance/data/attendance_repository.dart';
import 'package:school_saas_mobile/features/student/attendance/domain/attendance_models.dart';
import 'package:school_saas_mobile/features/student/attendance/presentation/attendance_controller.dart';
import 'package:school_saas_mobile/features/student/attendance/presentation/attendance_screens.dart';

Map<String, dynamic> attendancePayload() => {
  'student': {'id': 1, 'student_code': 'DEMO-S001', 'full_name': 'طالب تجريبي'},
  'academic_year': {'id': 2, 'name': '2025/2026'},
  'terms': [
    {'id': 7, 'name': 'الفصل الثالث', 'term_type': 'term_3',
     'start_date': '2026-05-01', 'end_date': '2026-08-31', 'is_active': true}
  ],
  'records': [
    {'id': 1, 'attendance_date': '2026-08-20', 'status': 'present', 'note': '',
     'academic_term': 7, 'academic_term_detail': {'name': 'الفصل الثالث'}},
    {'id': 2, 'attendance_date': '2026-08-19', 'status': 'absent', 'note': 'غياب',
     'academic_term': 7, 'academic_term_detail': {'name': 'الفصل الثالث'}},
    {'id': 3, 'attendance_date': '2026-08-18', 'status': 'late', 'note': 'تأخر',
     'academic_term': 7, 'academic_term_detail': {'name': 'الفصل الثالث'}},
    {'id': 4, 'attendance_date': '2026-08-17', 'status': 'excused', 'note': 'عذر',
     'academic_term': 7, 'academic_term_detail': {'name': 'الفصل الثالث'}},
  ],
};

void main() {
  test('attendance parses all backend statuses and computes percentage', () {
    final data = StudentAttendanceData.fromJson(attendancePayload(), DateTime.utc(2026, 8, 20));
    final state = AttendanceReady(data);
    expect(state.summary.total, 4);
    expect(state.summary.present, 1);
    expect(state.summary.absent, 1);
    expect(state.summary.late, 1);
    expect(state.summary.excused, 1);
    expect(state.summary.percentage, 50);
  });

  test('attendance term filter uses cached record term id', () {
    final data = StudentAttendanceData.fromJson(attendancePayload(), DateTime.utc(2026, 8, 20));
    final state = AttendanceReady(data, filterKey: 'term:7');
    expect(state.visible.length, 4);
    expect(state.visible.every((row) => row.termId == 7), isTrue);
  });


  test('attendance offline cache stays isolated by user membership and year', () async {
    final db = AppDatabase.forTesting(NativeDatabase.memory());
    addTearDown(db.close);
    const a = CacheScope(localUserKey: 'user:1', membershipId: 10, academicYearKey: '2026');
    const b = CacheScope(localUserKey: 'user:1', membershipId: 11, academicYearKey: '2026');
    await db.putContext(
      scope: a,
      resourceId: 'student_attendance_v1',
      payload: attendancePayload(),
      isHistorical: false,
      syncedAt: DateTime.utc(2026, 8, 20),
    );
    final repository = StudentAttendanceRepository(Dio(), db);
    expect((await repository.read(a))?.records.length, 4);
    expect(await repository.read(b), isNull);
  });

  testWidgets('attendance screen shows summary statuses and read-only records', (tester) async {
    final data = StudentAttendanceData.fromJson(attendancePayload(), DateTime.utc(2026, 8, 20));
    await tester.pumpWidget(MaterialApp(home: Scaffold(body: StudentAttendanceScreen(
      state: AttendanceReady(data), historical: false,
      onFilter: (_) {}, onOpen: (_) {}, onRefresh: () async {}, onBack: () {},
    ))));
    expect(find.text('نسبة الحضور'), findsOneWidget);
    expect(find.text('حاضر'), findsWidgets);
    expect(find.text('غائب'), findsWidgets);
    expect(find.text('متأخر'), findsWidgets);
    expect(find.text('بعذر'), findsWidgets);
  });

  testWidgets('attendance loading and error closure states render safely', (tester) async {
    await tester.binding.setSurfaceSize(const Size(320, 480));
    addTearDown(() => tester.binding.setSurfaceSize(null));

    Widget scaled(Widget child) => MaterialApp(
          home: MediaQuery(
            data: const MediaQueryData(
              size: Size(320, 480),
              textScaler: TextScaler.linear(1.5),
            ),
            child: Scaffold(body: child),
          ),
        );

    await tester.pumpWidget(scaled(const StudentAttendanceLoadingView()));
    expect(find.byType(StudentAttendanceLoadingView), findsOneWidget);
    expect(tester.takeException(), isNull);

    var retried = false;
    await tester.pumpWidget(scaled(StudentAttendanceOfflineEmptyView(
      onRetry: () async { retried = true; },
      onBack: () {},
    )));
    expect(find.text('لا تتوفر بيانات الحضور دون اتصال'), findsOneWidget);
    expect(find.text('إعادة المحاولة'), findsOneWidget);
    expect(tester.takeException(), isNull);

    retried = false;
    await tester.pumpWidget(scaled(StudentAttendanceErrorView(
      message: 'تعذر الاتصال بالخادم',
      onRetry: () async { retried = true; },
      onBack: () {},
    )));
    expect(find.text('تعذر تحميل سجل الحضور'), findsOneWidget);
    expect(find.text('إعادة المحاولة'), findsOneWidget);
    expect(tester.takeException(), isNull);
    await tester.tap(find.text('إعادة المحاولة'));
    await tester.pump();
    expect(retried, isTrue);
  });
  testWidgets('attendance ready and detail tolerate compact 150 percent scale',
      (tester) async {
    await tester.binding.setSurfaceSize(const Size(320, 480));
    addTearDown(() => tester.binding.setSurfaceSize(null));
    final data = StudentAttendanceData.fromJson(
      attendancePayload(),
      DateTime.utc(2026, 8, 20),
    );

    Widget scaled(Widget child) => MaterialApp(
          home: MediaQuery(
            data: const MediaQueryData(
              size: Size(320, 480),
              textScaler: TextScaler.linear(1.5),
            ),
            child: Directionality(
              textDirection: TextDirection.rtl,
              child: Scaffold(body: child),
            ),
          ),
        );

    await tester.pumpWidget(scaled(StudentAttendanceScreen(
      state: AttendanceReady(data),
      historical: false,
      onFilter: (_) {},
      onOpen: (_) {},
      onRefresh: () async {},
      onBack: () {},
    )));
    expect(tester.takeException(), isNull);

    await tester.pumpWidget(scaled(StudentAttendanceDetailScreen(
      record: data.records.first,
      historical: true,
      onBack: () {},
    )));
    expect(find.text('للعرض فقط'), findsOneWidget);
    expect(tester.takeException(), isNull);
  });

}
