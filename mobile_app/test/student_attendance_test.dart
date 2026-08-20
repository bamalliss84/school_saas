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
    expect(find.text('حاضر 1'), findsOneWidget);
    expect(find.text('غائب 1'), findsOneWidget);
    expect(find.text('متأخر 1'), findsOneWidget);
    expect(find.text('بعذر 1'), findsOneWidget);
  });
}
