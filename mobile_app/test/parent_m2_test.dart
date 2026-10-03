import 'package:dio/dio.dart';
import 'package:drift/native.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:school_saas_mobile/core/local_database/app_database.dart';
import 'package:school_saas_mobile/features/parent/data/parent_attendance_repository.dart';
import 'package:school_saas_mobile/features/parent/data/parent_timetable_repository.dart';
import 'package:school_saas_mobile/features/parent/domain/parent_attendance_models.dart';
import 'package:school_saas_mobile/features/parent/domain/parent_timetable_models.dart';
import 'package:school_saas_mobile/features/parent/presentation/parent_m2_controller.dart';
import 'package:school_saas_mobile/features/parent/presentation/parent_m2_screens.dart';
import 'package:school_saas_mobile/features/parent_shell/parent_shell.dart';

const scope = CacheScope(localUserKey: 'user:7', membershipId: 41, academicYearKey: '8');

Map<String, dynamic> entryJson(int id, String subject) => {
  'id': id, 'weekday': 1, 'teacher': 'أ. أحمد', 'subject': subject,
  'classroom': 'السادس', 'section': 'أ', 'status': 'upcoming',
  'period_detail': {'id': 3, 'name': 'الحصة الأولى', 'sequence': 1, 'start_time': '07:30:00', 'end_time': '08:15:00', 'kind': 'lesson'},
};

Map<String, dynamic> weekJson(String subject) => {
  'week_start': '2026-09-27',
  'days': [{'date': '2026-09-28', 'weekday': 1, 'entries': [entryJson(1, subject)]}],
};

Map<String, dynamic> attendanceJson(String status) => {
  'student': {'id': 1, 'student_code': 'ST-1', 'full_name': 'أحمد سالم'},
  'period': {'date_from': null, 'date_to': null}, 'total_records': 1,
  'present_count': status == 'present' ? 1 : 0,
  'absent_count': status == 'absent' ? 1 : 0,
  'late_count': status == 'late' ? 1 : 0,
  'excused_count': status == 'excused' ? 1 : 0,
  'attendance_percentage': status == 'absent' ? 0.0 : 100.0,
  'records': [{
    'id': 10, 'student_enrollment': 21,
    'student': {'id': 1, 'student_code': 'ST-1', 'full_name': 'أحمد سالم'},
    'teacher_assignment': 31, 'academic_term': 5,
    'academic_term_detail': {'id': 5, 'name': 'الفصل الأول'},
    'attendance_date': '2026-09-28', 'status': status, 'note': '',
  }],
};

Widget app(Widget child) => MaterialApp(home: Directionality(textDirection: TextDirection.rtl, child: Scaffold(body: SafeArea(child: child))));

void main() {
  test('timetable uses parent-authorized student_id and isolates child cache', () async {
    final requests = <RequestOptions>[];
    final dio = Dio()..interceptors.add(InterceptorsWrapper(onRequest: (options, handler) {
      requests.add(options); handler.resolve(Response(requestOptions: options, data: weekJson('الرياضيات')));
    }));
    final db = AppDatabase.forTesting(NativeDatabase.memory()); addTearDown(db.close);
    final repository = ParentTimetableRepository(dio, db); await repository.refresh(scope, 1);
    expect(requests.single.path, 'timetable/week/'); expect(requests.single.queryParameters['student_id'], 1);
    expect((await repository.read(scope, 1))?.week.days.single.entries.single.subject, 'الرياضيات');
    expect(await repository.read(scope, 2), isNull);
    expect(await repository.read(const CacheScope(localUserKey: 'user:7', membershipId: 99, academicYearKey: '8'), 1), isNull);
  });

  test('timetable uses only the matching cached child when offline', () async {
    final db = AppDatabase.forTesting(NativeDatabase.memory()); addTearDown(db.close);
    final online = Dio()..interceptors.add(InterceptorsWrapper(onRequest: (options, handler) => handler.resolve(Response(requestOptions: options, data: weekJson('العلوم')))));
    await ParentTimetableRepository(online, db).refresh(scope, 1);
    final offline = Dio()..interceptors.add(InterceptorsWrapper(onRequest: (options, handler) => handler.reject(DioException(requestOptions: options, type: DioExceptionType.connectionError))));
    final data = await ParentTimetableRepository(offline, db).load(scope, 1);
    expect(data.offline, isTrue); expect(data.week.days.single.entries.single.subject, 'العلوم');
    expect(ParentTimetableRepository(offline, db).load(scope, 2), throwsA(isA<DioException>()));
  });

  test('attendance uses child summary and selected academic year', () async {
    final requests = <RequestOptions>[];
    final dio = Dio()..interceptors.add(InterceptorsWrapper(onRequest: (options, handler) {
      requests.add(options); handler.resolve(Response(requestOptions: options, data: attendanceJson('late')));
    }));
    final db = AppDatabase.forTesting(NativeDatabase.memory()); addTearDown(db.close);
    final data = await ParentAttendanceRepository(dio, db).refresh(scope, 1);
    expect(requests.single.path, 'attendance/student/1/summary/'); expect(requests.single.queryParameters['academic_year_id'], 8);
    expect(data.records.single.status, ParentAttendanceStatus.late); expect(data.attendancePercentage, 100);
  });

  test('all backend attendance statuses retain exact semantics', () {
    expect(['present', 'absent', 'late', 'excused'].map((status) => ParentAttendanceData.fromJson(attendanceJson(status), DateTime.utc(2026, 10, 2)).records.single.status.apiValue).toList(), ['present', 'absent', 'late', 'excused']);
  });

  test('attendance cache cannot leak between children or memberships', () async {
    final dio = Dio()..interceptors.add(InterceptorsWrapper(onRequest: (options, handler) => handler.resolve(Response(requestOptions: options, data: attendanceJson('present')))));
    final db = AppDatabase.forTesting(NativeDatabase.memory()); addTearDown(db.close);
    final repository = ParentAttendanceRepository(dio, db); await repository.refresh(scope, 1);
    expect(await repository.read(scope, 2), isNull);
    expect(await repository.read(const CacheScope(localUserKey: 'user:7', membershipId: 99, academicYearKey: '8'), 1), isNull);
  });

  test('attendance uses only the matching cached child when offline', () async {
    final db = AppDatabase.forTesting(NativeDatabase.memory()); addTearDown(db.close);
    final online = Dio()..interceptors.add(InterceptorsWrapper(onRequest: (options, handler) => handler.resolve(Response(requestOptions: options, data: attendanceJson('absent')))));
    await ParentAttendanceRepository(online, db).refresh(scope, 1);
    final offline = Dio()..interceptors.add(InterceptorsWrapper(onRequest: (options, handler) => handler.reject(DioException(requestOptions: options, type: DioExceptionType.connectionError))));
    final data = await ParentAttendanceRepository(offline, db).load(scope, 1);
    expect(data.offline, isTrue); expect(data.records.single.status, ParentAttendanceStatus.absent);
    expect(ParentAttendanceRepository(offline, db).load(scope, 2), throwsA(isA<DioException>()));
  });

  testWidgets('timetable renders loading empty error and historical states', (tester) async {
    await tester.pumpWidget(app(ParentTimetableScreen(state: const ParentTimetableLoading(), childName: 'أحمد', historical: false, onRefresh: () async {})));
    expect(find.byType(CircularProgressIndicator), findsOneWidget);
    await tester.pumpWidget(app(ParentTimetableScreen(state: const ParentTimetableFailure('تعذر تحميل الجدول'), childName: 'أحمد', historical: false, onRefresh: () async {})));
    expect(find.text('إعادة المحاولة'), findsOneWidget);
    final empty = ParentTimetableData.fromJson({'week_start': '2026-09-27', 'days': const []}, DateTime.utc(2026, 10, 2));
    await tester.pumpWidget(app(ParentTimetableScreen(state: ParentTimetableReady(empty), childName: 'أحمد', historical: true, onRefresh: () async {})));
    expect(find.text('لا توجد حصص في هذا الأسبوع'), findsOneWidget); expect(find.textContaining('للقراءة فقط'), findsOneWidget);
  });

  testWidgets('attendance renders backend summary and status label', (tester) async {
    final data = ParentAttendanceData.fromJson(attendanceJson('excused'), DateTime.utc(2026, 10, 2));
    await tester.pumpWidget(app(ParentAttendanceScreen(state: ParentAttendanceReady(data), childName: 'أحمد', historical: false, onRefresh: () async {})));
    expect(find.text('بعذر'), findsOneWidget); expect(find.text('100%'), findsOneWidget);
  });

  testWidgets('attendance renders loading empty error and offline states', (tester) async {
    await tester.pumpWidget(app(ParentAttendanceScreen(state: const ParentAttendanceLoading(), childName: 'أحمد', historical: false, onRefresh: () async {})));
    expect(find.byType(CircularProgressIndicator), findsOneWidget);
    await tester.pumpWidget(app(ParentAttendanceScreen(state: const ParentAttendanceFailure('تعذر تحميل الحضور'), childName: 'أحمد', historical: false, onRefresh: () async {})));
    expect(find.text('إعادة المحاولة'), findsOneWidget);
    final empty = ParentAttendanceData.fromJson({...attendanceJson('present'), 'total_records': 0, 'records': const []}, DateTime.utc(2026, 10, 2), offline: true);
    await tester.pumpWidget(app(ParentAttendanceScreen(state: ParentAttendanceReady(empty), childName: 'أحمد', historical: false, onRefresh: () async {})));
    expect(find.text('لا توجد سجلات حضور'), findsOneWidget); expect(find.textContaining('بيانات محفوظة'), findsAtLeastNWidgets(1));
  });

  testWidgets('Parent navigation exposes only M1 and M2 destinations', (tester) async {
    await tester.pumpWidget(app(ParentBottomNavigation(selectedIndex: 0, onSelected: (_) {})));
    for (final label in ['الرئيسية', 'الجدول', 'الحضور', 'المزيد']) { expect(find.text(label), findsOneWidget); }
    for (final deferred in ['الواجبات', 'النتائج', 'الرسائل']) { expect(find.text(deferred), findsNothing); }
  });
}
