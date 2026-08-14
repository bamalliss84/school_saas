import 'package:dio/dio.dart';
import 'package:drift/native.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:school_saas_mobile/core/design_system/app_theme.dart';
import 'package:school_saas_mobile/core/design_system/components.dart';
import 'package:school_saas_mobile/core/local_database/app_database.dart';
import 'package:school_saas_mobile/core/preferences/font_preferences.dart';
import 'package:school_saas_mobile/features/student/timetable/data/timetable_repository.dart';
import 'package:school_saas_mobile/features/student/timetable/domain/timetable_models.dart';
import 'package:school_saas_mobile/features/student/timetable/presentation/timetable_screens.dart';

Map<String, dynamic> lesson([int id = 1]) => {
      'id': id,
      'weekday': 0,
      'teacher': 'معلم الرياضيات',
      'subject': 'الرياضيات',
      'classroom': 'السادس',
      'section': 'أ',
      'status': 'upcoming',
      'period_detail': {
        'id': id,
        'name': 'الحصة الأولى',
        'sequence': id,
        'start_time': '08:00:00',
        'end_time': '08:45:00',
        'kind': 'lesson'
      }
    };

Map<String, dynamic> payload(String key) {
  if (key == 'today') {
    return {
      'date': '2026-08-14',
      'entries': [lesson()],
      'periods': [
        lesson()['period_detail'],
        {
          'id': 9,
          'name': 'الفسحة',
          'sequence': 2,
          'start_time': '08:45:00',
          'end_time': '09:00:00',
          'kind': 'break'
        }
      ]
    };
  }
  if (key == 'week') {
    return {
      'week_start': '2026-08-09',
      'days': List.generate(
          7,
          (i) => {
                'date': '2026-08-${(9 + i).toString().padLeft(2, '0')}',
                'weekday': i,
                'entries': i == 0 ? [lesson()] : []
              })
    };
  }
  return {
    'date': '2026-08-14',
    key == 'current' ? 'current_entry' : 'next_entry': null
  };
}

void main() {
  test('typed parsing supports null current and next', () {
    expect(TodayTimetable.fromJson(payload('today')).entries.single.subject,
        'الرياضيات');
    expect(nullableEntry(payload('current'), 'current_entry'), isNull);
    expect(nullableEntry(payload('next'), 'next_entry'), isNull);
  });

  test('timetable repository caches and isolates membership', () async {
    final db = AppDatabase.forTesting(NativeDatabase.memory());
    addTearDown(db.close);
    const a = CacheScope(
        localUserKey: 'user:1', membershipId: 1, academicYearKey: '7');
    const b = CacheScope(
        localUserKey: 'user:1', membershipId: 2, academicYearKey: '7');
    final repo = StudentTimetableRepository(Dio(), db,
        fetcher: (key) async => payload(key));
    expect((await repo.refresh(a)).fromCache, isFalse);
    expect((await repo.readCache(a))!.today.entries, hasLength(1));
    expect(await repo.readCache(b), isNull);
  });

  test('remote failure preserves old timetable cache', () async {
    final db = AppDatabase.forTesting(NativeDatabase.memory());
    addTearDown(db.close);
    const scope = CacheScope(
        localUserKey: 'user:1', membershipId: 1, academicYearKey: '7');
    await StudentTimetableRepository(Dio(), db,
        fetcher: (key) async => payload(key)).refresh(scope);
    final failing = StudentTimetableRepository(Dio(), db,
        fetcher: (_) async => throw Exception('offline'));
    expect(() => failing.refresh(scope), throwsException);
    expect((await failing.readCache(scope))!.today.entries.single.subject,
        'الرياضيات');
  });

  testWidgets('break rendering is distinct', (tester) async {
    final period = TodayTimetable.fromJson(payload('today')).periods.last;
    await tester.pumpWidget(MaterialApp(
        home: Directionality(
            textDirection: TextDirection.rtl,
            child: Scaffold(body: BreakCard(period: period)))));
    expect(find.byIcon(Icons.local_cafe_outlined), findsOneWidget);
    expect(find.text('الفسحة'), findsOneWidget);
  });

  testWidgets('long Arabic lesson tolerates 150 percent scale', (tester) async {
    final model = TimetableEntryModel.fromJson({
      ...lesson(),
      'subject': 'مادة اللغة العربية والدراسات الأدبية الطويلة'
    });
    await tester.pumpWidget(MaterialApp(
        home: MediaQuery(
            data: const MediaQueryData(textScaler: TextScaler.linear(1.5)),
            child: Directionality(
                textDirection: TextDirection.rtl,
                child: Scaffold(body: LessonCard(entry: model))))));
    expect(tester.takeException(), isNull);
  });

  testWidgets('context and offline treatment tolerate 150 percent scale',
      (tester) async {
    await tester.binding.setSurfaceSize(const Size(360, 640));
    addTearDown(() => tester.binding.setSurfaceSize(null));
    for (final font in AppFont.values) {
      await tester.pumpWidget(MaterialApp(
        theme: buildAppTheme(font),
        home: const MediaQuery(
          data: MediaQueryData(textScaler: TextScaler.linear(1.5)),
          child: Directionality(
            textDirection: TextDirection.rtl,
            child: Scaffold(
              body: SafeArea(
                child: Column(children: [
                  StudentAppHeader(
                    studentName: 'عبدالرحمن محمد عبدالرحمن العبدلي',
                    schoolName: 'مدرسة النور الأهلية النموذجية للتعليم',
                    academicYear: '2026/2027',
                  ),
                  OfflineCacheBanner(),
                ]),
              ),
            ),
          ),
        ),
      ));
      expect(tester.takeException(), isNull, reason: font.label);
    }
  });
}
