import 'package:dio/dio.dart';
import 'package:drift/native.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:school_saas_mobile/app/session/app_session.dart';
import 'package:school_saas_mobile/core/local_database/app_database.dart';
import 'package:school_saas_mobile/core/models/auth_models.dart';
import 'package:school_saas_mobile/core/models/school_context.dart';
import 'package:school_saas_mobile/features/parent/data/parent_communications_repository.dart';
import 'package:school_saas_mobile/features/parent/presentation/parent_communications_controller.dart';
import 'package:school_saas_mobile/features/parent/presentation/parent_communications_screens.dart';
import 'package:school_saas_mobile/features/parent/presentation/parent_history_screen.dart';
import 'package:school_saas_mobile/features/parent_shell/parent_shell.dart';

const scope = CacheScope(localUserKey: 'user:7', membershipId: 41, academicYearKey: '8');
const parentCtx = SchoolContext(
    membershipId: 41, schoolName: 'مدرسة النور', role: 'parent', status: 'active',
    accessMode: 'active', canWrite: true, academicYearId: 8, academicYearName: '2026/2027');
const teacherCtx = SchoolContext(
    membershipId: 77, schoolName: 'مدرسة الفجر', role: 'teacher', status: 'active',
    accessMode: 'active', canWrite: true, academicYearId: 3, academicYearName: '2026/2027');
const user = AuthenticatedUser(id: 7, username: 'ali', fullName: 'علي', role: 'teacher');

Widget app(Widget child) => MaterialApp(
    home: Directionality(textDirection: TextDirection.rtl, child: Scaffold(body: child)));

Map<String, dynamic> conversationJson(int id, String subject) => {
      'id': id, 'subject': subject, 'conversation_type': 'teacher_parent', 'status': 'open',
      'unread_count': 0, 'last_message_preview': '', 'participants': [], 'updated_at': '2026-11-15T08:00:00Z',
    };

void main() {
  testWidgets('a teacher who is also a parent can switch to the teacher role from the parent app',
      (tester) async {
    SchoolContext? selected;
    await tester.pumpWidget(app(ParentMore(
      session: const AppSession(SessionStatus.authenticated,
          user: user, context: parentCtx, contexts: [parentCtx, teacherCtx]),
      onSelectContext: (context) async => selected = context,
      onLogout: () async {},
    )));
    expect(find.text('المدرسة والدور'), findsOneWidget);
    expect(find.textContaining('معلم'), findsWidgets);
    await tester.tap(find.text('مدرسة الفجر'));
    await tester.pumpAndSettle();
    expect(selected?.role, 'teacher');
  });

  test('role labels are Arabic', () {
    expect(roleLabel('parent'), 'ولي أمر');
    expect(roleLabel('teacher'), 'معلم');
    expect(roleLabel('school_admin'), 'مدير المدرسة');
  });

  test('teacher options come from safe discovery and start a private teacher_parent conversation',
      () async {
    final requests = <RequestOptions>[];
    final dio = Dio()
      ..interceptors.add(InterceptorsWrapper(onRequest: (options, handler) {
        requests.add(options);
        if (options.path == 'communication/recipient-options/') {
          handler.resolve(Response(requestOptions: options, data: {
            'results': [
              {'display_name': 'أ. سعيد', 'role': 'teacher', 'subject': 'الرياضيات',
               'teacher_assignment_id': 31, 'recipient_ref': 'signed'},
            ],
          }));
        } else {
          handler.resolve(Response(requestOptions: options, data: conversationJson(5, 'مستوى الرياضيات')));
        }
      }));
    final db = AppDatabase.forTesting(NativeDatabase.memory());
    addTearDown(db.close);
    final repository = ParentCommunicationsRepository(dio, db);
    final teachers = await repository.teachersFor(1);
    expect(requests.first.queryParameters['student_id'], 1);
    expect(teachers.single.name, 'أ. سعيد');
    final data = await repository.startWithTeacher(scope, childId: 1, assignmentId: 31, subject: 'مستوى الرياضيات');
    final body = requests.last.data as Map;
    expect(requests.last.path, 'conversations/start/');
    expect(body['conversation_type'], 'teacher_parent');
    expect(body['student_id'], 1);
    expect(body['teacher_assignment_id'], 31);
    expect(body.containsKey('parent_membership_id'), isFalse);
    expect(data.items.single.subject, 'مستوى الرياضيات');
  });

  testWidgets('conversations screen walks the parent through choosing a teacher', (tester) async {
    ParentTeacherOption? chosen;
    String? subject;
    final ready = ParentConversationsReady(
        ParentConversationData(const [], DateTime.now().toUtc()));
    await tester.pumpWidget(app(ParentConversationsScreen(
      state: ready,
      historical: false,
      childName: 'أحمد',
      onRefresh: () async {},
      onOpen: (_) async {},
      onCreateSupport: (_, __) async {},
      onLoadTeachers: () async => const [
        ParentTeacherOption(name: 'أ. سعيد', subject: 'الرياضيات', assignmentId: 31),
      ],
      onStartWithTeacher: (teacher, text) async {
        chosen = teacher;
        subject = text;
      },
    )));
    await tester.tap(find.byKey(const Key('parent-message-teacher')));
    await tester.pumpAndSettle();
    expect(find.text('اختر معلم أحمد'), findsOneWidget);
    await tester.tap(find.text('أ. سعيد'));
    await tester.pumpAndSettle();
    await tester.enterText(find.byKey(const Key('parent-teacher-subject')), 'الواجب');
    await tester.tap(find.text('بدء المحادثة'));
    await tester.pumpAndSettle();
    expect(chosen?.assignmentId, 31);
    expect(subject, 'الواجب');
  });

  testWidgets('historical context hides the new-conversation actions', (tester) async {
    await tester.pumpWidget(app(ParentConversationsScreen(
      state: ParentConversationsReady(ParentConversationData(const [], DateTime.now().toUtc())),
      historical: true,
      onRefresh: () async {},
      onOpen: (_) async {},
      onCreateSupport: (_, __) async {},
      onLoadTeachers: () async => const [],
      onStartWithTeacher: (_, __) async {},
    )));
    expect(find.byKey(const Key('parent-message-teacher')), findsNothing);
  });

  testWidgets('study record lists current and previous schools and opens the old one read-only',
      (tester) async {
    int? opened;
    final schools = parseChildSchools([
      {'school': {'id': 1, 'name': 'مدرسة النور'}, 'access_mode': 'read_write', 'is_current': true,
       'membership_id': 41, 'academic_years': [{'id': 8, 'name': '2026/2027'}]},
      {'school': {'id': 2, 'name': 'مدرسة الأمل'}, 'access_mode': 'read_only', 'is_current': false,
       'membership_id': 52, 'academic_years': [{'id': 5, 'name': '2024/2025'}, {'id': 6, 'name': '2025/2026'}]},
    ]);
    await tester.pumpWidget(MaterialApp(home: ParentChildHistoryScreen(
      childName: 'أحمد',
      currentMembershipId: 41,
      load: () async => schools,
      onOpenSchool: (id) async => opened = id,
    )));
    await tester.pumpAndSettle();
    expect(find.text('المدرسة الحالية'), findsOneWidget);
    expect(find.text('مدرسة سابقة'), findsOneWidget);
    expect(find.textContaining('2024/2025'), findsOneWidget);
    await tester.tap(find.textContaining('للقراءة فقط'));
    await tester.pumpAndSettle();
    expect(opened, 52);
  });
}
