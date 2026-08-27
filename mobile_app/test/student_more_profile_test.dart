import 'package:dio/dio.dart';
import 'package:drift/native.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:school_saas_mobile/core/local_database/app_database.dart';
import 'package:school_saas_mobile/core/models/school_context.dart';
import 'package:school_saas_mobile/features/student/student_profile_controller.dart';
import 'package:school_saas_mobile/features/student/student_profile_models.dart';
import 'package:school_saas_mobile/features/student/student_profile_repository.dart';
import 'package:school_saas_mobile/features/student/student_profile_screens.dart';

const currentContext = SchoolContext(
  membershipId: 10,
  schoolName: 'مدرسة النور الدولية ذات الاسم الطويل',
  role: 'student',
  status: 'active',
  accessMode: 'active',
  canWrite: true,
  academicYearName: '2026/2027',
  academicYearId: 4,
);

const historicalContext = SchoolContext(
  membershipId: 20,
  schoolName: 'مدرسة الأمل',
  role: 'student',
  status: 'historical',
  accessMode: 'historical',
  canWrite: false,
  academicYearName: '2025/2026',
  academicYearId: 3,
);

Map<String, dynamic> profileJson() => {
      'id': 7,
      'student_code': 'ST-0085',
      'full_name': 'محمد أحمد عبدالله صاحب الاسم العربي الطويل جدًا',
      'school': {'id': 1, 'name': currentContext.schoolName},
      'current_enrollment': {
        'academic_year': {'id': 4, 'name': '2026/2027'},
        'classroom': {'id': 2, 'name': 'الصف الثامن المتقدم طويل الاسم'},
        'section': {'id': 3, 'name': 'الشعبة ألف الدولية'},
      },
    };

Map<String, dynamic> historyJson() => {
      'id': 31,
      'school': {'id': 1, 'name': 'مدرسة النور'},
      'academic_year': {'id': 3, 'name': '2025/2026'},
      'classroom': {'id': 1, 'name': 'الصف السابع'},
      'section': {'id': 2, 'name': 'ب'},
      'status': 'completed',
      'is_current': false,
    };

StudentMoreData moreData({List<StudentAcademicHistoryItem>? history}) =>
    StudentMoreData(
      profile: StudentProfile.fromJson(profileJson()),
      schools: const [
        StudentSchoolSummary(
          membershipId: 10,
          schoolName: 'مدرسة النور',
          accessMode: 'read_write',
          isCurrent: true,
        ),
      ],
      history: history ?? [StudentAcademicHistoryItem.fromJson(historyJson())],
      lastUpdated: DateTime.utc(2026, 8, 27),
    );

Widget app(Widget child, {double scale = 1}) => MaterialApp(
      home: MediaQuery(
        data: MediaQueryData(textScaler: TextScaler.linear(scale)),
        child: Directionality(
          textDirection: TextDirection.rtl,
          child: Scaffold(body: SafeArea(child: child)),
        ),
      ),
    );

void main() {
  test('profile models parse only real backend fields', () {
    final profile = StudentProfile.fromJson(profileJson());
    expect(profile.studentCode, 'ST-0085');
    expect(profile.academicYearName, '2026/2027');
    expect(profile.classroomName, contains('الثامن'));
    expect(profile.sectionName, contains('ألف'));
  });

  test('repository loads the three real endpoints with selected membership',
      () async {
    final requested = <RequestOptions>[];
    final dio = Dio();
    dio.interceptors.add(InterceptorsWrapper(onRequest: (options, handler) {
      requested.add(options);
      final data = switch (options.path) {
        'students/me/profile/' => profileJson(),
        'students/me/schools/' => [
            {
              'membership_id': 10,
              'school': {'id': 1, 'name': 'مدرسة النور'},
              'access_mode': 'read_write',
              'is_current': true,
            }
          ],
        _ => [historyJson()],
      };
      handler.resolve(Response(requestOptions: options, data: data));
    }));
    final db = AppDatabase.forTesting(NativeDatabase.memory());
    addTearDown(db.close);
    const scope = CacheScope(
        localUserKey: 'user:1', membershipId: 10, academicYearKey: '4');
    final data = await StudentProfileRepository(dio, db).refresh(scope);
    expect(data.profile.fullName, contains('محمد'));
    expect(data.history.single.schoolName, 'مدرسة النور');
    final historyRequest =
        requested.singleWhere((item) => item.path.contains('academic-history'));
    expect(historyRequest.queryParameters['school_membership_id'], 10);
  });

  test('profile cache is isolated by user membership and academic year',
      () async {
    final db = AppDatabase.forTesting(NativeDatabase.memory());
    addTearDown(db.close);
    const first = CacheScope(
        localUserKey: 'user:1', membershipId: 10, academicYearKey: '4');
    const other = CacheScope(
        localUserKey: 'user:1', membershipId: 20, academicYearKey: '3');
    await db.putContext(
      scope: first,
      resourceId: StudentProfileRepository.resourceId,
      payload: {
        'profile': profileJson(),
        'schools': const [],
        'history': [historyJson()],
      },
      isHistorical: false,
      syncedAt: DateTime.utc(2026, 8, 27),
    );
    final repository = StudentProfileRepository(Dio(), db);
    expect((await repository.read(first))?.profile.studentCode, 'ST-0085');
    expect(await repository.read(other), isNull);
  });

  testWidgets(
      'More renders required destinations and hides single-context switch',
      (tester) async {
    await tester.pumpWidget(app(StudentMoreScreen(
      studentName: 'محمد أحمد',
      schoolName: 'مدرسة النور',
      canChangeContext: false,
      onProfile: () {},
      onContext: () {},
      onHistory: () {},
      onAppearance: () {},
      onHelp: () {},
      onAbout: () {},
      onLogout: () {},
    )));
    for (final label in [
      'ملفي',
      'السجل الدراسي',
      'المظهر',
      'المساعدة',
      'حول التطبيق',
      'تسجيل الخروج'
    ]) {
      expect(find.text(label), findsOneWidget);
    }
    expect(find.text('المدرسة والسياق'), findsNothing);
  });

  testWidgets(
      'More exposes canonical context action only for multiple contexts',
      (tester) async {
    await tester.pumpWidget(app(StudentMoreScreen(
      studentName: 'محمد',
      schoolName: 'مدرسة النور',
      canChangeContext: true,
      onProfile: () {},
      onContext: () {},
      onHistory: () {},
      onAppearance: () {},
      onHelp: () {},
      onAbout: () {},
      onLogout: () {},
    )));
    expect(find.text('المدرسة والسياق'), findsOneWidget);
  });

  testWidgets('More logout and nested Back invoke existing shell actions',
      (tester) async {
    var loggedOut = false;
    var backed = false;
    await tester.pumpWidget(app(StudentMoreScreen(
      studentName: 'محمد',
      schoolName: 'مدرسة النور',
      canChangeContext: false,
      onProfile: () {},
      onContext: () {},
      onHistory: () {},
      onAppearance: () {},
      onHelp: () {},
      onAbout: () {},
      onLogout: () => loggedOut = true,
    )));
    await tester.scrollUntilVisible(
      find.text('تسجيل الخروج'),
      200,
      scrollable: find.byType(Scrollable).first,
    );
    await tester.pumpAndSettle();
    await tester.tap(find.text('تسجيل الخروج'));
    expect(loggedOut, isTrue);

    await tester.pumpWidget(app(StudentAboutScreen(
      onBack: () => backed = true,
    )));
    await tester.tap(find.byIcon(Icons.arrow_forward));
    expect(backed, isTrue);
  });

  testWidgets(
      'profile renders loading error empty-safe and backend data states',
      (tester) async {
    await tester.pumpWidget(app(StudentProfileScreen(
      state: const StudentProfileLoading(),
      contextInfo: currentContext,
      onBack: () {},
      onRetry: () async {},
    )));
    expect(find.byType(LinearProgressIndicator), findsOneWidget);

    await tester.pumpWidget(app(StudentProfileScreen(
      state: const StudentProfileFailure('تعذر تحميل الملف'),
      contextInfo: currentContext,
      onBack: () {},
      onRetry: () async {},
    )));
    expect(find.text('إعادة المحاولة'), findsOneWidget);

    await tester.pumpWidget(app(StudentProfileScreen(
      state: StudentProfileReady(moreData()),
      contextInfo: currentContext,
      onBack: () {},
      onRetry: () async {},
    )));
    expect(find.text('ST-0085'), findsOneWidget);
    expect(find.text('2026/2027'), findsOneWidget);
    expect(find.textContaining('الصف الثامن'), findsOneWidget);
  });

  testWidgets(
      'historical profile is labeled read-only and hides current enrollment',
      (tester) async {
    await tester.pumpWidget(app(StudentProfileScreen(
      state: StudentProfileReady(moreData()),
      contextInfo: historicalContext,
      onBack: () {},
      onRetry: () async {},
    )));
    expect(find.text('أرشيف / للقراءة فقط'), findsNWidgets(2));
    expect(find.textContaining('الصف الثامن'), findsNothing);
    expect(find.text('مدرسة الأمل'), findsOneWidget);
  });

  testWidgets('authorized context switch is invoked', (tester) async {
    int? selected;
    await tester.pumpWidget(app(StudentContextScreen(
      current: currentContext,
      contexts: const [currentContext, historicalContext],
      offline: false,
      onBack: () {},
      onSelect: (item) async => selected = item.membershipId,
    )));
    await tester.tap(find.text('مدرسة الأمل'));
    await tester.pumpAndSettle();
    expect(selected, 20);
  });

  testWidgets(
      'failed switch keeps old context visible with Arabic retry message',
      (tester) async {
    await tester.pumpWidget(app(StudentContextScreen(
      current: currentContext,
      contexts: const [currentContext, historicalContext],
      offline: false,
      onBack: () {},
      onSelect: (_) async => throw Exception('network'),
    )));
    await tester.tap(find.text('مدرسة الأمل'));
    await tester.pumpAndSettle();
    expect(find.textContaining('ما زلت في السياق السابق'), findsOneWidget);
    expect(find.byIcon(Icons.check_circle), findsOneWidget);
  });

  testWidgets('offline context switching remains disabled', (tester) async {
    var calls = 0;
    await tester.pumpWidget(app(StudentContextScreen(
      current: currentContext,
      contexts: const [currentContext, historicalContext],
      offline: true,
      onBack: () {},
      onSelect: (_) async => calls++,
    )));
    await tester.tap(find.text('مدرسة الأمل'));
    await tester.pump();
    expect(calls, 0);
    expect(find.textContaining('لا يوجد اتصال بالإنترنت'), findsOneWidget);
  });

  testWidgets('academic history renders real records and clean empty state',
      (tester) async {
    await tester.pumpWidget(app(StudentAcademicHistoryScreen(
      state: StudentProfileReady(moreData()),
      onBack: () {},
      onRetry: () async {},
    )));
    expect(find.text('مدرسة النور'), findsOneWidget);
    expect(find.text('2025/2026'), findsOneWidget);
    expect(find.textContaining('الصف السابع'), findsOneWidget);

    await tester.pumpWidget(app(StudentAcademicHistoryScreen(
      state: StudentProfileReady(moreData(history: const [])),
      onBack: () {},
      onRetry: () async {},
    )));
    expect(find.text('لا يوجد سجل دراسي سابق'), findsOneWidget);
  });

  testWidgets('Help routes to existing support and About stays compact',
      (tester) async {
    var support = false;
    await tester.pumpWidget(app(StudentHelpScreen(
      onBack: () {},
      onSupport: () => support = true,
    )));
    await tester.tap(find.text('التواصل مع المدرسة'));
    expect(support, isTrue);

    await tester.pumpWidget(app(StudentAboutScreen(onBack: () {})));
    expect(find.text('تطبيق المدرسة'), findsOneWidget);
  });

  testWidgets(
      'long Arabic More and profile remain safe at 320x480 and 150 percent',
      (tester) async {
    tester.view.physicalSize = const Size(320, 480);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);
    await tester.pumpWidget(app(
        StudentProfileScreen(
          state: StudentProfileReady(moreData()),
          contextInfo: currentContext,
          onBack: () {},
          onRetry: () async {},
        ),
        scale: 1.5));
    await tester.drag(find.byType(ListView), const Offset(0, -300));
    await tester.pump();
    expect(find.text('ST-0085'), findsOneWidget);
    expect(tester.takeException(), isNull);
  });
}
