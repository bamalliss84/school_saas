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
import 'package:school_saas_mobile/features/student/timetable/presentation/timetable_controller.dart';
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
    const otherYear = CacheScope(
        localUserKey: 'user:1', membershipId: 1, academicYearKey: '8');
    expect(await repo.readCache(otherYear), isNull);
  });

  test('today lessons and week days are parsed in chronological order', () {
    final late = lesson(2);
    final early = lesson(1);
    final today = TodayTimetable.fromJson({
      'date': '2026-08-14',
      'entries': [late, early],
      'periods': [late['period_detail'], early['period_detail']],
    });
    final week = WeekTimetable.fromJson({
      'week_start': '2026-08-09',
      'days': [
        {'date': '2026-08-10', 'weekday': 1, 'entries': []},
        {'date': '2026-08-09', 'weekday': 0, 'entries': []},
      ],
    });
    expect(today.entries.map((item) => item.id), [1, 2]);
    expect(today.periods.map((item) => item.id), [1, 2]);
    expect(week.days.map((item) => item.weekday), [0, 1]);
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

  test('controller shows cached offline data then clears offline on recovery',
      () async {
    final db = AppDatabase.forTesting(NativeDatabase.memory());
    addTearDown(db.close);
    const scope = CacheScope(
        localUserKey: 'user:1', membershipId: 1, academicYearKey: '7');
    var offline = false;
    final repository = StudentTimetableRepository(
      Dio(),
      db,
      fetcher: (key) async {
        if (offline) {
          throw DioException(
            requestOptions: RequestOptions(path: key),
            type: DioExceptionType.connectionError,
          );
        }
        return payload(key);
      },
    );
    final controller = TimetableController(repository, scope);
    addTearDown(controller.dispose);
    await controller.load();
    expect((controller.state as TimetableReady).offline, isFalse);
    offline = true;
    await controller.load();
    expect((controller.state as TimetableReady).offline, isTrue);
    offline = false;
    await controller.load();
    expect((controller.state as TimetableReady).offline, isFalse);
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

  testWidgets('today marks only backend current and next lessons',
      (tester) async {
    final current =
        TimetableEntryModel.fromJson({...lesson(1), 'status': 'current'});
    final next = TimetableEntryModel.fromJson({...lesson(2)});
    final data = _data(
      todayEntries: [current, next],
      periods: [current.period, next.period],
      current: current,
      next: next,
    );
    await tester.pumpWidget(_screen(data));
    expect(find.text('الآن'), findsOneWidget);
    expect(find.text('التالية'), findsOneWidget);
  });

  testWidgets('home does not invent missing current or next lessons',
      (tester) async {
    final data = _data(current: null, next: null);
    await tester.pumpWidget(_home(data));
    expect(find.text('لا توجد حصة حالية'), findsOneWidget);
    expect(find.text('لا توجد حصة قادمة'), findsOneWidget);
    expect(find.text('الآن'), findsNothing);
    expect(find.text('التالية'), findsNothing);
  });

  testWidgets('empty configured day differs from unconfigured timetable',
      (tester) async {
    final period = TimetablePeriod.fromJson(
        lesson()['period_detail'] as Map<String, dynamic>);
    await tester.pumpWidget(_screen(_data(periods: [period])));
    expect(find.text('لا توجد حصص اليوم'), findsOneWidget);

    await tester.pumpWidget(_screen(_data(periods: const [])));
    await tester.pump();
    expect(find.text('لم يتم إعداد الجدول الدراسي لهذا السياق بعد'),
        findsOneWidget);
  });

  testWidgets('week identifies today and handles an empty selected day',
      (tester) async {
    await tester.pumpWidget(_screen(_data(
      periods: [
        TimetablePeriod.fromJson(
            lesson()['period_detail'] as Map<String, dynamic>)
      ],
    )));
    await tester.tap(find.text('الأسبوع'));
    await tester.pumpAndSettle();
    expect(find.text('الجمعة • اليوم'), findsOneWidget);
    expect(find.text('لا توجد حصص في هذا اليوم'), findsOneWidget);
  });

  testWidgets('week selector keeps every RTL day fully reachable at 320x480',
      (tester) async {
    tester.view.physicalSize = const Size(320, 480);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);
    final data = _data(periods: [
      TimetablePeriod.fromJson(
          lesson()['period_detail'] as Map<String, dynamic>)
    ]);
    await tester.pumpWidget(MaterialApp(
      home: MediaQuery(
        data: const MediaQueryData(textScaler: TextScaler.linear(1.5)),
        child: Directionality(
          textDirection: TextDirection.rtl,
          child: Scaffold(
            body: StudentTimetableScreen(
              data: data,
              onRefresh: () async {},
            ),
          ),
        ),
      ),
    ));
    await tester.tap(find.text('الأسبوع'));
    await tester.pumpAndSettle();

    for (var weekday = 0; weekday < 7; weekday++) {
      final chip = find.byKey(ValueKey('week-day-$weekday'));
      expect(chip, findsOneWidget);
      await tester.ensureVisible(chip);
      await tester.pump();
      final bounds = tester.getRect(chip);
      expect(bounds.left, greaterThanOrEqualTo(0));
      expect(bounds.right, lessThanOrEqualTo(320));
      expect(bounds.width, greaterThan(0));
    }
    expect(find.text('الجمعة • اليوم'), findsOneWidget);
    expect(tester.takeException(), isNull);
  });

  testWidgets('historical timetable is explicitly view only', (tester) async {
    await tester.pumpWidget(_screen(_data(), historical: true));
    expect(find.text('عرض فقط'), findsOneWidget);
    expect(find.text('جدول السنة الدراسية السابقة'), findsOneWidget);
    expect(find.byType(TextField), findsNothing);
  });

  testWidgets('timetable back action closes the nested screen', (tester) async {
    var closed = false;
    await tester.pumpWidget(_screen(_data(), onBack: () => closed = true));
    await tester.tap(find.byTooltip('رجوع'));
    expect(closed, isTrue);
  });

  testWidgets('full timetable fits 320x480 at 150 percent with long labels',
      (tester) async {
    tester.view.physicalSize = const Size(320, 480);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);
    final entry = TimetableEntryModel.fromJson({
      ...lesson(1),
      'subject': 'اللغة العربية والدراسات الأدبية ذات الاسم الطويل جدًا',
      'teacher': 'الأستاذ عبدالرحمن محمد عبدالرحمن العبدلي',
      'classroom': 'الصف السادس الابتدائي النموذجي',
      'section': 'الشعبة الألف ذات الاسم الطويل',
      'status': 'current',
    });
    await tester.pumpWidget(MaterialApp(
      home: MediaQuery(
        data: const MediaQueryData(textScaler: TextScaler.linear(1.5)),
        child: Directionality(
          textDirection: TextDirection.rtl,
          child: Scaffold(
            body: StudentTimetableScreen(
              data: _data(
                todayEntries: [entry],
                periods: [entry.period],
                current: entry,
              ),
              onRefresh: () async {},
              onBack: () {},
            ),
          ),
        ),
      ),
    ));
    expect(find.text('جدولي'), findsOneWidget);
    expect(find.text('الآن'), findsOneWidget);
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

  testWidgets(
      'home is compact and safe with empty current and long next lesson',
      (tester) async {
    tester.view.physicalSize = const Size(320, 480);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);
    final next = TimetableEntryModel.fromJson({
      ...lesson(3),
      'subject': 'اللغة العربية والدراسات الأدبية ذات الاسم الطويل جدًا',
      'teacher': 'الأستاذ عبدالرحمن محمد عبدالرحمن العبدلي',
    });
    final data = StudentTimetableData(
      today: TodayTimetable.fromJson(payload('today')),
      week: WeekTimetable.fromJson(payload('week')),
      current: null,
      next: next,
      lastUpdated: DateTime(2026, 8, 22),
      fromCache: false,
    );

    await tester.pumpWidget(MaterialApp(
      home: MediaQuery(
        data: const MediaQueryData(textScaler: TextScaler.linear(1.5)),
        child: Directionality(
          textDirection: TextDirection.rtl,
          child: Scaffold(
            body: StudentHomeScreen(
              data: data,
              studentName: 'عبدالرحمن محمد عبدالرحمن العبدلي',
              schoolName: 'مدرسة النور الأهلية النموذجية للتعليم',
              academicYear: '2026/2027',
              onOpenTimetable: () {},
              onOpenAttendance: () {},
            ),
          ),
        ),
      ),
    ));

    await tester.scrollUntilVisible(
      find.text('حصصي اليوم'),
      160,
      scrollable: find.byType(Scrollable).first,
    );
    await tester.pump();
    expect(find.text('حصصي اليوم'), findsOneWidget);
    expect(find.text('لا توجد حصة حالية'), findsOneWidget);
    expect(tester.takeException(), isNull);
  });
}

StudentTimetableData _data({
  List<TimetableEntryModel> todayEntries = const [],
  List<TimetablePeriod>? periods,
  TimetableEntryModel? current,
  TimetableEntryModel? next,
}) {
  final days = List.generate(
    7,
    (index) => TimetableDay(
      date: DateTime(2026, 8, 9 + index),
      weekday: index,
      entries: index == 5 ? todayEntries : const [],
    ),
  );
  return StudentTimetableData(
    today: TodayTimetable(
      date: DateTime(2026, 8, 14),
      entries: todayEntries,
      periods: periods ?? todayEntries.map((item) => item.period).toList(),
    ),
    week: WeekTimetable(weekStart: DateTime(2026, 8, 9), days: days),
    current: current,
    next: next,
    lastUpdated: DateTime(2026, 8, 14),
    fromCache: false,
  );
}

Widget _screen(
  StudentTimetableData data, {
  bool historical = false,
  VoidCallback? onBack,
}) =>
    MaterialApp(
      home: Directionality(
        textDirection: TextDirection.rtl,
        child: Scaffold(
          body: StudentTimetableScreen(
            data: data,
            historical: historical,
            onBack: onBack,
            onRefresh: () async {},
          ),
        ),
      ),
    );

Widget _home(StudentTimetableData data) => MaterialApp(
      home: Directionality(
        textDirection: TextDirection.rtl,
        child: Scaffold(
          body: StudentHomeScreen(
            data: data,
            studentName: 'طالب',
            schoolName: 'المدرسة',
            academicYear: '2026/2027',
            onOpenTimetable: () {},
            onOpenAttendance: () {},
          ),
        ),
      ),
    );
