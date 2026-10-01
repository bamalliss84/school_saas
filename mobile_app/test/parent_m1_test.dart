import 'package:dio/dio.dart';
import 'package:drift/native.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:school_saas_mobile/core/local_database/app_database.dart';
import 'package:school_saas_mobile/core/models/school_context.dart';
import 'package:school_saas_mobile/app/app.dart';
import 'package:school_saas_mobile/app/session/app_session.dart';
import 'package:school_saas_mobile/core/models/auth_models.dart';
import 'package:school_saas_mobile/features/parent/data/parent_repository.dart';
import 'package:school_saas_mobile/features/parent/domain/parent_models.dart';
import 'package:school_saas_mobile/features/parent/presentation/parent_controller.dart';
import 'package:school_saas_mobile/features/parent/presentation/parent_home.dart';
import 'package:school_saas_mobile/features/parent_shell/parent_shell.dart';

const scopeA =
    CacheScope(localUserKey: 'user:7', membershipId: 41, academicYearKey: '8');
const scopeB =
    CacheScope(localUserKey: 'user:7', membershipId: 52, academicYearKey: '9');
const activeContext = SchoolContext(
    membershipId: 41,
    schoolName: 'مدرسة النور',
    role: 'parent',
    status: 'active',
    accessMode: 'active',
    canWrite: true,
    academicYearId: 8,
    academicYearName: '2026/2027');
const historicalContext = SchoolContext(
    membershipId: 52,
    schoolName: 'مدرسة الأمل',
    role: 'parent',
    status: 'historical',
    accessMode: 'historical',
    canWrite: false,
    academicYearId: 9,
    academicYearName: '2025/2026');

Map<String, dynamic> childJson(int id, String name) => {
      'student': {
        'id': id,
        'student_code': 'ST-$id',
        'full_name': name,
        'gender': 'male',
        'is_active': true,
        'school': {'id': 3, 'name': 'مدرسة النور'},
        'current_enrollment': null
      },
      'relationship_type': 'father',
      'is_primary': id == 1,
    };

Map<String, dynamic> enrollmentJson(int id, String classroom) => {
      'id': id,
      'school': {'id': 3, 'name': 'مدرسة النور'},
      'academic_year': {'id': 8, 'name': '2026/2027'},
      'classroom': {'id': 11, 'name': classroom},
      'section': {'id': 12, 'name': 'أ'},
      'status': 'active',
      'is_current': true,
      'start_date': '2026-08-01',
      'end_date': null,
    };

ParentFoundationData foundation(
    {List<ParentChild>? children, int? selected, bool offline = false}) {
  final rows = children ??
      [
        ParentChild.fromJson(childJson(1, 'أحمد سالم')),
        ParentChild.fromJson(childJson(2, 'ريم سالم'))
      ];
  return ParentFoundationData(
    children: rows,
    selectedChildId: selected ?? (rows.isEmpty ? null : rows.first.id),
    histories: rows.isEmpty
        ? const {}
        : {
            rows.first.id: [
              ParentEnrollment.fromJson(enrollmentJson(91, 'الصف السادس'))
            ]
          },
    lastUpdated: DateTime.utc(2026, 10, 2),
    offline: offline,
  );
}

Widget app(Widget child) => MaterialApp(
    home: Directionality(
        textDirection: TextDirection.rtl,
        child: Scaffold(body: SafeArea(child: child))));

class FakeParentRepository implements ParentFoundationDataSource {
  FakeParentRepository(this.next);
  ParentFoundationData next;
  Object? loadError;
  final selected = <int>[];
  @override
  Future<ParentFoundationData> load(CacheScope scope) async {
    if (loadError case final error?) throw error;
    return next;
  }

  @override
  Future<ParentFoundationData> refresh(CacheScope scope) async => load(scope);
  @override
  Future<ParentFoundationData> selectChild(
      CacheScope scope, int childId) async {
    selected.add(childId);
    next = next.copyWith(selectedChildId: childId);
    return next;
  }
}

void main() {
  test('parent role resolves to the real ParentShell', () {
    expect(parentShellForMembership(41), isA<ParentShell>());
  });

  test('parent child model parses only the proven backend response', () {
    final child = ParentChild.fromJson(childJson(1, 'أحمد سالم'));
    expect(child.id, 1);
    expect(child.studentCode, 'ST-1');
    expect(child.relationship, 'father');
    expect(child.isPrimary, isTrue);
  });

  test('repository loads children and selected child academic history',
      () async {
    final requests = <RequestOptions>[];
    final dio = Dio()
      ..interceptors.add(InterceptorsWrapper(onRequest: (options, handler) {
        requests.add(options);
        final data = options.path == 'parents/me/children/'
            ? {
                'count': 2,
                'results': [childJson(1, 'أحمد سالم'), childJson(2, 'ريم سالم')]
              }
            : [enrollmentJson(91, 'الصف السادس')];
        handler.resolve(Response(requestOptions: options, data: data));
      }));
    final db = AppDatabase.forTesting(NativeDatabase.memory());
    addTearDown(db.close);
    final data = await ParentRepository(dio, db).refresh(scopeA);
    expect(data.children, hasLength(2));
    expect(data.selectedChildId, 1);
    expect(data.selectedEnrollment?.classroomName, 'الصف السادس');
    final history =
        requests.singleWhere((item) => item.path.contains('academic-history'));
    expect(history.path, 'parents/me/children/1/academic-history/');
    expect(history.queryParameters['school_membership_id'], 41);
    expect(history.queryParameters['academic_year_id'], 8);
  });

  test('selection persists inside its CacheScope and never leaks contexts',
      () async {
    final db = AppDatabase.forTesting(NativeDatabase.memory());
    addTearDown(db.close);
    final dio = Dio()
      ..interceptors.add(InterceptorsWrapper(onRequest: (options, handler) {
        final data = options.path == 'parents/me/children/'
            ? [childJson(1, 'أحمد'), childJson(2, 'ريم')]
            : [enrollmentJson(91, 'الصف السادس')];
        handler.resolve(Response(requestOptions: options, data: data));
      }));
    final repository = ParentRepository(dio, db);
    await repository.refresh(scopeA);
    await repository.selectChild(scopeA, 2);
    expect((await repository.read(scopeA))?.selectedChildId, 2);
    expect(await repository.read(scopeB), isNull);
  });

  test('cached children remain available during offline load', () async {
    final db = AppDatabase.forTesting(NativeDatabase.memory());
    addTearDown(db.close);
    final online = Dio()
      ..interceptors.add(InterceptorsWrapper(onRequest: (options, handler) {
        final data = options.path == 'parents/me/children/'
            ? [childJson(1, 'أحمد')]
            : [enrollmentJson(91, 'الصف السادس')];
        handler.resolve(Response(requestOptions: options, data: data));
      }));
    await ParentRepository(online, db).refresh(scopeA);
    final offline = Dio()
      ..interceptors.add(InterceptorsWrapper(
          onRequest: (options, handler) => handler.reject(DioException(
              requestOptions: options,
              type: DioExceptionType.connectionError))));
    final data = await ParentRepository(offline, db).load(scopeA);
    expect(data.offline, isTrue);
    expect(data.selectedChild?.fullName, 'أحمد');
  });

  test('controller switches child safely', () async {
    final repository = FakeParentRepository(foundation());
    final controller = ParentController(repository, scopeA);
    await controller.load();
    expect((controller.state as ParentReady).data.selectedChildId, 1);
    await controller.selectChild(2);
    expect(repository.selected, [2]);
    expect((controller.state as ParentReady).data.selectedChildId, 2);
  });

  test('controller exposes load errors without fake data', () async {
    final repository = FakeParentRepository(foundation())
      ..loadError = StateError('failed');
    final controller = ParentController(repository, scopeA);
    await controller.load();
    expect(controller.state, isA<ParentFailure>());
  });

  testWidgets('home shows loading empty and retryable error states',
      (tester) async {
    await tester.pumpWidget(app(ParentHome(
        state: const ParentLoading(),
        contextInfo: activeContext,
        onSelectChild: (_) async {},
        onRefresh: () async {})));
    expect(find.byType(CircularProgressIndicator), findsOneWidget);
    await tester.pumpWidget(app(ParentHome(
        state: ParentReady(foundation(children: const [])),
        contextInfo: activeContext,
        onSelectChild: (_) async {},
        onRefresh: () async {})));
    expect(find.text('لا يوجد أبناء مرتبطون بهذا السياق'), findsOneWidget);
    await tester.pumpWidget(app(ParentHome(
        state: const ParentFailure('تعذر تحميل الأبناء'),
        contextInfo: activeContext,
        onSelectChild: (_) async {},
        onRefresh: () async {})));
    expect(find.text('إعادة المحاولة'), findsOneWidget);
  });

  testWidgets('one child home shows identity and contextual enrollment',
      (tester) async {
    final child = ParentChild.fromJson(childJson(1, 'أحمد سالم'));
    await tester.pumpWidget(app(ParentHome(
        state: ParentReady(foundation(children: [child])),
        contextInfo: activeContext,
        onSelectChild: (_) async {},
        onRefresh: () async {})));
    expect(find.text('أحمد سالم'), findsAtLeastNWidgets(1));
    expect(find.text('الصف السادس'), findsOneWidget);
    expect(find.text('أ'), findsOneWidget);
    expect(find.byType(DropdownButton<int>), findsNothing);
  });

  testWidgets('multiple children can switch from the home selector',
      (tester) async {
    int? selected;
    await tester.pumpWidget(app(ParentHome(
        state: ParentReady(foundation()),
        contextInfo: activeContext,
        onSelectChild: (value) async => selected = value,
        onRefresh: () async {})));
    await tester.tap(find.byKey(const Key('parent-child-selector')));
    await tester.pumpAndSettle();
    await tester.tap(find.text('ريم سالم').last);
    await tester.pumpAndSettle();
    expect(selected, 2);
  });

  testWidgets('historical and offline states are explicit', (tester) async {
    await tester.pumpWidget(app(ParentHome(
        state: ParentReady(foundation(offline: true)),
        contextInfo: historicalContext,
        onSelectChild: (_) async {},
        onRefresh: () async {})));
    expect(find.textContaining('للقراءة فقط'), findsOneWidget);
    expect(find.textContaining('بيانات محفوظة'), findsAtLeastNWidgets(1));
  });

  testWidgets('parent context switch uses canonical membership selection',
      (tester) async {
    int? selected;
    const user = AuthenticatedUser(
      id: 7,
      username: 'parent',
      fullName: 'ولي الأمر',
      role: 'parent',
    );
    await tester.pumpWidget(app(ParentMore(
      session: const AppSession(
        SessionStatus.authenticated,
        user: user,
        context: activeContext,
        contexts: [activeContext, historicalContext],
      ),
      onSelectContext: (context) async => selected = context.membershipId,
      onLogout: () async {},
    )));
    await tester.tap(find.text('مدرسة الأمل'));
    await tester.pumpAndSettle();
    expect(selected, 52);
  });

  testWidgets('offline parent context switching stays disabled',
      (tester) async {
    var calls = 0;
    const user = AuthenticatedUser(
      id: 7,
      username: 'parent',
      fullName: 'ولي الأمر',
      role: 'parent',
    );
    await tester.pumpWidget(app(ParentMore(
      session: const AppSession(
        SessionStatus.authenticated,
        user: user,
        context: activeContext,
        contexts: [activeContext, historicalContext],
        offline: true,
      ),
      onSelectContext: (_) async => calls++,
      onLogout: () async {},
    )));
    await tester.tap(find.text('مدرسة الأمل'));
    await tester.pump();
    expect(calls, 0);
    expect(find.textContaining('لا يمكن تغيير المدرسة'), findsOneWidget);
  });
}
