import 'package:dio/dio.dart';
import 'package:drift/native.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:school_saas_mobile/core/local_database/app_database.dart';
import 'package:school_saas_mobile/features/parent/data/parent_communications_repository.dart';
import 'package:school_saas_mobile/features/parent/domain/parent_communication_models.dart';
import 'package:school_saas_mobile/features/parent/presentation/parent_communications_controller.dart';
import 'package:school_saas_mobile/features/parent/presentation/parent_communications_screens.dart';
import 'package:school_saas_mobile/features/parent_shell/parent_shell.dart';

const scope = CacheScope(
  localUserKey: 'user:7',
  membershipId: 41,
  academicYearKey: '8',
);

Map<String, dynamic> notificationJson({bool read = false}) => {
      'id': 1,
      'notification_type': 'homework_graded',
      'title': 'تم تصحيح الواجب',
      'body': 'يمكنك مراجعة النتيجة',
      'is_read': read,
      'read_at': read ? '2026-10-17T08:00:00Z' : null,
      'created_at': '2026-10-17T07:00:00Z',
      'membership_id': 41,
      'action': null,
    };

Map<String, dynamic> announcementJson({bool read = false}) => {
      'id': 11,
      'title': 'اجتماع أولياء الأمور',
      'body': 'يوم الأحد الساعة العاشرة',
      'status': 'published',
      'priority': 'high',
      'published_at': '2026-10-17T07:00:00Z',
      'attachments': const [],
      'receipt': {'is_read': read, 'read_at': null},
      'permissions': {'can_inquire': true},
    };

Map<String, dynamic> conversationJson({int id = 21, int unread = 2}) => {
      'id': id,
      'conversation_type': 'teacher_parent',
      'subject': 'متابعة أحمد',
      'status': 'open',
      'category': '',
      'participants_summary': [
        {'role': 'teacher', 'display_name': 'أ. أحمد'}
      ],
      'last_message_preview': 'يرجى متابعة الواجب',
      'last_message_at': '2026-10-17T07:00:00Z',
      'unread_messages_count': unread,
      'can_reply': true,
      'updated_at': '2026-10-17T07:00:00Z',
    };

Map<String, dynamic> messageJson({int id = 31, String body = 'مرحبًا'}) => {
      'id': id,
      'conversation': 21,
      'sender': {'role': 'teacher', 'display_name': 'أ. أحمد'},
      'body': body,
      'created_at': '2026-10-17T07:00:00Z',
      'attachments_count': 0,
    };

Widget app(Widget child) => MaterialApp(
      home: Directionality(
        textDirection: TextDirection.rtl,
        child: Scaffold(body: SafeArea(child: child)),
      ),
    );

void main() {
  test('notification list and canonical mark-read use membership endpoints',
      () async {
    final requests = <RequestOptions>[];
    final dio = Dio()
      ..interceptors.add(InterceptorsWrapper(onRequest: (options, handler) {
        requests.add(options);
        handler.resolve(Response(
          requestOptions: options,
          data: options.path.endsWith('/read/')
              ? notificationJson(read: true)
              : {
                  'count': 1,
                  'results': [notificationJson()]
                },
        ));
      }));
    final db = AppDatabase.forTesting(NativeDatabase.memory());
    addTearDown(db.close);
    final repository = ParentCommunicationsRepository(dio, db);

    final list = await repository.refreshNotifications(scope);
    final read =
        await repository.markNotificationRead(scope, list.items.single);

    expect(requests.map((e) => e.path),
        ['notifications/', 'notifications/1/read/']);
    expect(read.items.single.isRead, isTrue);
    expect((await repository.readNotifications(scope))!.items.single.isRead,
        isTrue);
  });

  test('mark-all uses the canonical membership action and updates local cache',
      () async {
    final requests = <RequestOptions>[];
    final dio = Dio()
      ..interceptors.add(InterceptorsWrapper(onRequest: (options, handler) {
        requests.add(options);
        handler.resolve(Response(
          requestOptions: options,
          data: options.path == 'notifications/read-all/'
              ? {'updated_count': 1}
              : {
                  'results': [notificationJson()]
                },
        ));
      }));
    final db = AppDatabase.forTesting(NativeDatabase.memory());
    addTearDown(db.close);
    final repository = ParentCommunicationsRepository(dio, db);
    await repository.refreshNotifications(scope);

    final data = await repository.markAllNotificationsRead(scope);

    expect(requests.last.path, 'notifications/read-all/');
    expect(data.items.single.isRead, isTrue);
    expect((await repository.readNotifications(scope))!.unreadCount, 0);
  });

  test('notification cache never crosses membership or academic year',
      () async {
    final dio = Dio()
      ..interceptors.add(InterceptorsWrapper(onRequest: (options, handler) {
        handler.resolve(Response(requestOptions: options, data: {
          'count': 1,
          'results': [notificationJson()]
        }));
      }));
    final db = AppDatabase.forTesting(NativeDatabase.memory());
    addTearDown(db.close);
    final repository = ParentCommunicationsRepository(dio, db);
    await repository.refreshNotifications(scope);

    expect(await repository.readNotifications(scope), isNotNull);
    expect(
        await repository.readNotifications(const CacheScope(
          localUserKey: 'user:8',
          membershipId: 41,
          academicYearKey: '8',
        )),
        isNull);
    expect(
        await repository.readNotifications(const CacheScope(
          localUserKey: 'user:7',
          membershipId: 99,
          academicYearKey: '8',
        )),
        isNull);
    expect(
        await repository.readNotifications(const CacheScope(
          localUserKey: 'user:7',
          membershipId: 41,
          academicYearKey: '9',
        )),
        isNull);
  });

  test('authorization failure never becomes cached notification success',
      () async {
    final db = AppDatabase.forTesting(NativeDatabase.memory());
    addTearDown(db.close);
    final seedDio = Dio()
      ..interceptors.add(InterceptorsWrapper(onRequest: (options, handler) {
        handler.resolve(Response(requestOptions: options, data: {
          'results': [notificationJson()]
        }));
      }));
    await ParentCommunicationsRepository(seedDio, db)
        .refreshNotifications(scope);
    final deniedDio = Dio()
      ..interceptors.add(InterceptorsWrapper(onRequest: (options, handler) {
        handler.reject(DioException.badResponse(
          statusCode: 403,
          requestOptions: options,
          response: Response(requestOptions: options, statusCode: 403),
        ));
      }));
    final repository = ParentCommunicationsRepository(deniedDio, db);

    await expectLater(
        repository.loadNotifications(scope), throwsA(isA<DioException>()));
    final cached = await repository.readNotifications(scope);
    await expectLater(
        repository.markNotificationRead(scope, cached!.items.single),
        throwsA(isA<DioException>()));
    expect((await repository.readNotifications(scope))!.items.single.isRead,
        isFalse);
  });

  test('announcements parse authorized receipt and canonical read state',
      () async {
    final dio = Dio()
      ..interceptors.add(InterceptorsWrapper(onRequest: (options, handler) {
        handler.resolve(Response(
          requestOptions: options,
          data: options.path.endsWith('/read/')
              ? {
                  'announcement_id': 11,
                  'is_read': true,
                  'read_at': '2026-10-17T08:00:00Z'
                }
              : {
                  'count': 1,
                  'results': [announcementJson()]
                },
        ));
      }));
    final db = AppDatabase.forTesting(NativeDatabase.memory());
    addTearDown(db.close);
    final repository = ParentCommunicationsRepository(dio, db);
    final list = await repository.refreshAnnouncements(scope);

    final read =
        await repository.markAnnouncementRead(scope, list.items.single);

    expect(list.items.single.canInquire, isTrue);
    expect(read.items.single.isRead, isTrue);
    expect((await repository.readAnnouncements(scope))!.items.single.isRead,
        isTrue);
  });

  test(
      'authorized announcement inquiry uses selected child and canonical result',
      () async {
    RequestOptions? request;
    final dio = Dio()
      ..interceptors.add(InterceptorsWrapper(onRequest: (options, handler) {
        request = options;
        handler.resolve(Response(
          requestOptions: options,
          data: conversationJson(id: 44, unread: 0),
        ));
      }));
    final db = AppDatabase.forTesting(NativeDatabase.memory());
    addTearDown(db.close);
    final repository = ParentCommunicationsRepository(dio, db);

    final conversation = await repository.inquireAnnouncement(11, 73);

    expect(conversation.id, 44);
    expect(conversation.type, 'teacher_parent');
    expect(request!.path, 'announcements/11/inquiry/');
    expect(request!.data, {'student_id': 73});
  });

  test('conversation list detail read and canonical send are scoped by id',
      () async {
    final requests = <RequestOptions>[];
    final dio = Dio()
      ..interceptors.add(InterceptorsWrapper(onRequest: (options, handler) {
        requests.add(options);
        final data = switch ((options.method, options.path)) {
          ('GET', 'conversations/') => {
              'count': 1,
              'results': [conversationJson()]
            },
          ('GET', 'conversations/21/messages/') => {
              'results': [messageJson()]
            },
          ('POST', 'conversations/21/read/') => {
              'last_read_at': '2026-10-17T08:00:00Z'
            },
          ('POST', 'conversations/21/messages/') =>
            messageJson(id: 32, body: 'رد ولي الأمر'),
          _ => throw StateError(options.path),
        };
        handler.resolve(Response(requestOptions: options, data: data));
      }));
    final db = AppDatabase.forTesting(NativeDatabase.memory());
    addTearDown(db.close);
    final repository = ParentCommunicationsRepository(dio, db);
    final list = await repository.refreshConversations(scope);
    final messages = await repository.loadMessages(scope, 21);
    final read =
        await repository.markConversationRead(scope, list.items.single);
    final sent = await repository.sendMessage(scope, 21, 'رد ولي الأمر');

    expect(messages.single.body, 'مرحبًا');
    expect(read.items.single.unread, 0);
    expect(sent.last.body, 'رد ولي الأمر');
    expect(requests.last.data, {'body': 'رد ولي الأمر'});
  });

  test('support creation uses scoped backend workflow without recipient ids',
      () async {
    RequestOptions? request;
    final dio = Dio()
      ..interceptors.add(InterceptorsWrapper(onRequest: (options, handler) {
        request = options;
        handler.resolve(Response(
          requestOptions: options,
          data: conversationJson(id: 51, unread: 0)
            ..['conversation_type'] = 'school_support',
        ));
      }));
    final db = AppDatabase.forTesting(NativeDatabase.memory());
    addTearDown(db.close);
    final repository = ParentCommunicationsRepository(dio, db);

    final result =
        await repository.createSupport(scope, 'مشكلة تقنية', 'technical_issue');

    expect(result.items.single.id, 51);
    expect(request!.path, 'conversations/start/');
    expect(request!.data, {
      'conversation_type': 'school_support',
      'subject': 'مشكلة تقنية',
      'category': 'technical_issue',
      'priority': 'normal',
    });
  });

  test('message cache is isolated by conversation and context', () async {
    final dio = Dio()
      ..interceptors.add(InterceptorsWrapper(onRequest: (options, handler) {
        handler.resolve(Response(requestOptions: options, data: {
          'results': [messageJson()]
        }));
      }));
    final db = AppDatabase.forTesting(NativeDatabase.memory());
    addTearDown(db.close);
    final repository = ParentCommunicationsRepository(dio, db);
    await repository.loadMessages(scope, 21);

    expect(await repository.readMessages(scope, 21), isNotNull);
    expect(await repository.readMessages(scope, 22), isNull);
    expect(
        await repository.readMessages(
            const CacheScope(
              localUserKey: 'user:8',
              membershipId: 41,
              academicYearKey: '8',
            ),
            21),
        isNull);
  });

  test('controller blocks duplicate send and preserves failed draft', () async {
    final repository = _FakeRepository();
    addTearDown(repository.database.close);
    final controller = ParentConversationsController(repository, scope);
    await controller.load();
    await controller.open(repository.conversation);

    final first = controller.send('نص محفوظ');
    final second = controller.send('مكرر');
    await Future.wait([first, second]);

    expect(repository.sendCalls, 1);
    final state = controller.state as ParentConversationsReady;
    expect(state.draft, 'نص محفوظ');
    expect(state.detailError, isNotNull);
  });

  test('historical controller blocks reply before repository mutation',
      () async {
    final repository = _FakeRepository();
    addTearDown(repository.database.close);
    final controller =
        ParentConversationsController(repository, scope, historical: true);
    await controller.load();
    await controller.open(repository.conversation);

    await controller.send('لا يجب إرساله');
    await controller.createSupport('طلب ممنوع', 'general');

    expect(repository.sendCalls, 0);
    expect(repository.supportCalls, 0);
  });

  testWidgets('surfaces render loading empty error and historical read-only',
      (tester) async {
    await tester.pumpWidget(app(ParentNotificationsScreen(
      state: const ParentNotificationsLoading(),
      historical: false,
      onRefresh: () async {},
      onRead: (_) async {},
      onReadAll: () async {},
    )));
    expect(find.byType(CircularProgressIndicator), findsOneWidget);

    await tester.pumpWidget(app(ParentAnnouncementsScreen(
      state: const ParentAnnouncementsFailure('تعذر تحميل الإعلانات'),
      historical: false,
      onRefresh: () async {},
      onRead: (_) async {},
      onOpen: (_) {},
    )));
    expect(find.text('إعادة المحاولة'), findsOneWidget);

    await tester.pumpWidget(app(ParentConversationsScreen(
      state: ParentConversationsReady(ParentConversationData(
          const [], DateTime.utc(2026, 10, 17),
          offline: true)),
      historical: true,
      onRefresh: () async {},
      onOpen: (_) async {},
      onCreateSupport: (_, __) async {},
    )));
    expect(find.text('لا توجد محادثات'), findsOneWidget);
    expect(find.textContaining('بيانات محفوظة'), findsOneWidget);
    expect(find.textContaining('للقراءة فقط'), findsOneWidget);
    expect(find.text('طلب دعم جديد'), findsNothing);
  });

  testWidgets('conversation detail disables reply in historical context',
      (tester) async {
    final conversation = ParentConversation.fromJson(conversationJson());
    await tester.pumpWidget(app(ParentConversationDetailScreen(
      conversation: conversation,
      messages: [ParentMessage.fromJson(messageJson())],
      historical: true,
      busy: false,
      error: null,
      draft: '',
      onDraftChanged: (_) {},
      onSend: () async {},
    )));
    expect(find.text('مرحبًا'), findsOneWidget);
    expect(find.byType(TextField), findsNothing);
    expect(find.textContaining('للقراءة فقط'), findsOneWidget);
  });

  testWidgets('More exposes three communication destinations', (tester) async {
    await tester.pumpWidget(app(ParentCommunicationLinks(
      onNotifications: () {},
      onAnnouncements: () {},
      onMessages: () {},
    )));
    for (final label in ['الإشعارات', 'الإعلانات', 'الرسائل']) {
      expect(find.text(label), findsOneWidget);
    }
  });

  testWidgets('primary Parent navigation remains M1 through M4 only',
      (tester) async {
    await tester.pumpWidget(app(ParentBottomNavigation(
      selectedIndex: 0,
      onSelected: (_) {},
    )));
    for (final label in [
      'الرئيسية',
      'الجدول',
      'الحضور',
      'الواجبات',
      'النتائج',
      'المزيد'
    ]) {
      expect(find.text(label), findsOneWidget);
    }
    for (final secondary in ['الإشعارات', 'الإعلانات', 'الرسائل']) {
      expect(find.text(secondary), findsNothing);
    }
  });
}

class _FakeRepository extends ParentCommunicationsRepository {
  _FakeRepository()
      : super(Dio(), AppDatabase.forTesting(NativeDatabase.memory()));
  int sendCalls = 0;
  int supportCalls = 0;
  final conversation = ParentConversation.fromJson(conversationJson());

  @override
  Future<ParentConversationData> loadConversations(CacheScope scope) async =>
      ParentConversationData([conversation], DateTime.utc(2026, 10, 17));

  @override
  Future<List<ParentMessage>> loadMessages(CacheScope scope, int id) async =>
      [ParentMessage.fromJson(messageJson())];

  @override
  Future<ParentConversationData> markConversationRead(
          CacheScope scope, ParentConversation item) async =>
      ParentConversationData(
          [item.copyWith(unread: 0)], DateTime.utc(2026, 10, 17));

  @override
  Future<List<ParentMessage>> sendMessage(
      CacheScope scope, int id, String body) async {
    sendCalls++;
    await Future<void>.delayed(const Duration(milliseconds: 20));
    throw DioException(requestOptions: RequestOptions(path: 'send'));
  }

  @override
  Future<ParentConversationData> createSupport(
      CacheScope scope, String subject, String category) async {
    supportCalls++;
    return ParentConversationData([conversation], DateTime.utc(2026, 10, 17));
  }
}
