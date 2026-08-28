import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:file_selector/file_selector.dart';
import 'package:school_saas_mobile/features/student/communications/data/communications_repository.dart';
import 'package:school_saas_mobile/features/student/communications/domain/communication_models.dart';
import 'package:school_saas_mobile/features/student/communications/presentation/communications_screens.dart';

Widget _rtl(Widget child) => MaterialApp(
      home: Directionality(
        textDirection: TextDirection.rtl,
        child: Scaffold(body: SafeArea(child: child)),
      ),
    );

CommunicationsSnapshot _snapshot(List<CommunicationNotification> notifications,
        {bool offline = false}) =>
    CommunicationsSnapshot(
      notifications: notifications,
      announcements: const [],
      conversations: const [],
      badges: const CommunicationBadges(0, 0),
      lastUpdated: DateTime(2026, 8, 21, 10),
      offline: offline,
    );

ConversationSummary _conversation({
  required int id,
  required String type,
  required String subject,
  String status = 'open',
  String preview = '',
}) =>
    ConversationSummary(
      id: id,
      type: type,
      subject: subject,
      status: status,
      category: type == 'school_support' ? 'academic_inquiry' : '',
      unread: 0,
      canReply: true,
      participants:
          type == 'school_support' ? const [] : const ['أ. أحمد محمد'],
      preview: preview,
      updatedAt: DateTime(2026, 8, 21, 10, id),
    );

void main() {
  testWidgets('online state does not show the cached-data offline banner',
      (tester) async {
    await tester.pumpWidget(_rtl(StudentCommunicationsCenter(
      data: _snapshot(const []),
      historical: false,
      onBack: () {},
      onOpenNotification: (_) {},
      onReadAll: () {},
      onReadAnnouncement: (_) {},
      onInquireAnnouncement: (_) async {},
    )));

    expect(find.textContaining('لا يوجد اتصال بالإنترنت'), findsNothing);
  });

  testWidgets('offline cached state shows banner and recovery removes it',
      (tester) async {
    var offline = true;
    late StateSetter rebuild;

    await tester.pumpWidget(_rtl(StatefulBuilder(builder: (context, setState) {
      rebuild = setState;
      return StudentCommunicationsCenter(
        data: _snapshot(const [], offline: offline),
        historical: false,
        onBack: () {},
        onOpenNotification: (_) {},
        onReadAll: () {},
        onReadAnnouncement: (_) {},
        onInquireAnnouncement: (_) async {},
      );
    })));

    expect(find.textContaining('لا يوجد اتصال بالإنترنت'), findsOneWidget);
    rebuild(() => offline = false);
    await tester.pump();
    expect(find.textContaining('لا يوجد اتصال بالإنترنت'), findsNothing);
  });

  testWidgets('read notification remains tappable', (tester) async {
    var opened = 0;
    final notification = CommunicationNotification(
      id: 1,
      type: 'result_published',
      title: 'تم نشر نتيجة جديدة',
      body: 'يمكنك مراجعة النتيجة من التطبيق.',
      isRead: true,
      createdAt: DateTime(2026, 8, 21),
      action: const {
        'route': 'result_detail',
        'params': {'result_id': 7},
      },
    );

    await tester.pumpWidget(_rtl(StudentCommunicationsCenter(
      data: _snapshot([notification]),
      historical: false,
      onBack: () {},
      onOpenNotification: (_) => opened++,
      onReadAll: () {},
      onReadAnnouncement: (_) {},
      onInquireAnnouncement: (_) async {},
    )));

    await tester.tap(find.text('تم نشر نتيجة جديدة'));
    await tester.pump();
    expect(opened, 1);
  });

  testWidgets('historical notification remains tappable without local mutation',
      (tester) async {
    var opened = 0;
    final notification = CommunicationNotification(
      id: 2,
      type: 'result_published',
      title: 'نتيجة تاريخية',
      body: 'للعرض فقط',
      isRead: false,
      createdAt: DateTime(2025, 8, 21),
    );

    await tester.pumpWidget(_rtl(StudentCommunicationsCenter(
      data: _snapshot([notification]),
      historical: true,
      onBack: () {},
      onOpenNotification: (_) => opened++,
      onReadAll: () {},
      onReadAnnouncement: (_) {},
      onInquireAnnouncement: (_) async {},
    )));

    await tester.tap(find.text('نتيجة تاريخية'));
    await tester.pump();
    expect(opened, 1);
  });

  testWidgets('announcement detail renders body and attachments safely',
      (tester) async {
    final item = SchoolAnnouncement(
      id: 11,
      title: 'موعد الاختبارات النهائية',
      body: 'موعد الاختبارات النهائية وتفاصيل الإعلان المدرسي.',
      priority: 'high',
      publishedAt: DateTime(2026, 8, 21, 9, 30),
      isRead: false,
      canInquire: true,
      attachments: const [
        {'id': 1, 'name': 'schedule.pdf'}
      ],
    );

    await tester.pumpWidget(_rtl(StudentAnnouncementDetailScreen(
      item: item,
      historical: false,
      onBack: () {},
    )));

    expect(find.text('موعد الاختبارات النهائية'), findsOneWidget);
    expect(find.text('موعد الاختبارات النهائية وتفاصيل الإعلان المدرسي.'),
        findsOneWidget);
    expect(find.text('المرفقات (1)'), findsOneWidget);
    expect(tester.takeException(), isNull);
  });

  testWidgets('support creation entry opens sheet and reloads the real request',
      (tester) async {
    var calls = 0;
    var items = <ConversationSummary>[
      _conversation(
        id: 70,
        type: 'teacher_student',
        subject: 'أ. أحمد محمد',
        preview: 'راجع الواجب الجديد',
      ),
      _conversation(
        id: 71,
        type: 'school_support',
        subject: 'طلب سابق',
      ),
    ];

    await tester.pumpWidget(_rtl(StatefulBuilder(
      builder: (context, setState) => StudentConversationsScreen(
        items: items,
        offline: false,
        historical: false,
        onOpen: (_) {},
        onCreateSupport: (category, subject, message, attachments) async {
          calls++;
          expect(category, 'academic_inquiry');
          expect(subject, 'استفسار عن الحضور');
          expect(message, 'أرجو مراجعة سجل الحضور');
          setState(() {
            items = [
              _conversation(
                id: 72,
                type: 'school_support',
                subject: subject,
                status: 'open',
                preview: message,
              ),
              ...items,
            ];
          });
          return true;
        },
      ),
    )));

    expect(find.text('طلب دعم جديد'), findsOneWidget);
    await tester.tap(find.text('طلب دعم جديد'));
    await tester.pumpAndSettle();
    expect(find.byType(SchoolSupportSheet), findsOneWidget);

    await tester.enterText(find.byType(TextField).at(0), 'استفسار عن الحضور');
    await tester.enterText(
        find.byType(TextField).at(1), 'أرجو مراجعة سجل الحضور');
    await tester.tap(find.text('إرسال الطلب'));
    await tester.pumpAndSettle();

    expect(calls, 1);
    expect(find.byType(SchoolSupportSheet), findsNothing);
    expect(find.text('استفسار عن الحضور'), findsOneWidget);
    expect(find.text('طلب سابق'), findsOneWidget);
    expect(find.text('أ. أحمد محمد'), findsOneWidget);
  });

  testWidgets('offline and historical contexts block support creation',
      (tester) async {
    var calls = 0;
    Future<bool> create(String category, String subject, String message,
        List<XFile> attachments) async {
      calls++;
      return true;
    }

    await tester.pumpWidget(_rtl(StudentConversationsScreen(
      items: const [],
      offline: true,
      historical: false,
      onOpen: (_) {},
      onCreateSupport: create,
    )));
    await tester.tap(find.text('طلب دعم جديد'));
    await tester.pump();
    expect(find.text('يتطلب إرسال طلب دعم اتصالاً بالإنترنت.'), findsOneWidget);
    expect(find.byType(SchoolSupportSheet), findsNothing);

    await tester.pumpWidget(_rtl(StudentConversationsScreen(
      items: const [],
      offline: false,
      historical: true,
      onOpen: (_) {},
      onCreateSupport: create,
    )));
    final supportButton = find.ancestor(
      of: find.text('طلب دعم جديد'),
      matching: find.byWidgetPredicate((widget) => widget is OutlinedButton),
    );
    expect(supportButton, findsOneWidget);
    final button = tester.widget<OutlinedButton>(supportButton);
    expect(button.onPressed, isNull);
    expect(calls, 0);
  });

  testWidgets('attachment partial success is honest and never resubmits ticket',
      (tester) async {
    var calls = 0;
    await tester.pumpWidget(_rtl(StudentConversationsScreen(
      items: const [],
      offline: false,
      historical: false,
      onOpen: (_) {},
      onCreateSupport: (_, __, ___, ____) async {
        calls++;
        return false;
      },
    )));

    await tester.tap(find.text('طلب دعم جديد'));
    await tester.pumpAndSettle();
    await tester.enterText(find.byType(TextField).at(0), 'مشكلة في الملف');
    await tester.enterText(find.byType(TextField).at(1), 'تفاصيل مشكلة الملف');
    await tester.tap(find.text('إرسال الطلب'));
    await tester.pumpAndSettle();

    expect(calls, 1);
    expect(find.textContaining('تم إرسال الطلب، لكن تعذر رفع المرفق'),
        findsOneWidget);
  });

  testWidgets('support creation stays safe at 320x480 and 150 percent',
      (tester) async {
    tester.view.physicalSize = const Size(320, 480);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);

    await tester.pumpWidget(_rtl(MediaQuery(
      data: const MediaQueryData(
        textScaler: TextScaler.linear(1.5),
        viewInsets: EdgeInsets.only(bottom: 160),
      ),
      child: StudentConversationsScreen(
        items: const [],
        offline: false,
        historical: false,
        onOpen: (_) {},
        onCreateSupport: (_, __, ___, ____) async => true,
      ),
    )));
    await tester.tap(find.text('طلب دعم جديد'));
    await tester.pumpAndSettle();
    await tester.tap(find.text('استفسار دراسي'));
    await tester.pumpAndSettle();
    await tester.tap(find.text('عذر غياب').last);
    await tester.pumpAndSettle();
    await tester.enterText(find.byType(TextField).at(0),
        'استفسار عربي طويل جدًا عن بيانات الطالب وسجله الدراسي');
    await tester.enterText(find.byType(TextField).at(1),
        'وصف طويل للطلب يحتوي على التفاصيل الكاملة التي يحتاجها فريق الدعم');
    await tester.pump();

    expect(find.byType(SchoolSupportSheet), findsOneWidget);
    expect(find.text('عذر غياب'), findsOneWidget);
    expect(find.text('نوع الطلب'), findsOneWidget);
    expect(find.text('العنوان'), findsOneWidget);
    expect(find.text('وصف الطلب'), findsOneWidget);
    await tester.ensureVisible(find.text('إرسال الطلب'));
    await tester.pump();
    expect(find.text('إرسال الطلب'), findsOneWidget);
    expect(tester.takeException(), isNull);
  });

  testWidgets('messages header and support action stack without collision',
      (tester) async {
    tester.view.physicalSize = const Size(320, 480);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);

    await tester.pumpWidget(_rtl(MediaQuery(
      data: const MediaQueryData(textScaler: TextScaler.linear(1.5)),
      child: StudentConversationsScreen(
        items: [
          _conversation(
            id: 80,
            type: 'teacher_student',
            subject: 'أ. أحمد محمد',
          ),
          _conversation(
            id: 81,
            type: 'school_support',
            subject: 'طلب سابق',
          ),
        ],
        offline: false,
        historical: false,
        onOpen: (_) {},
        onCreateSupport: (_, __, ___, ____) async => true,
      ),
    )));

    final heading = tester.getRect(find.text('الرسائل'));
    final action = tester.getRect(find.text('طلب دعم جديد'));
    expect(action.top, greaterThan(heading.bottom));
    expect(find.text('أ. أحمد محمد'), findsNWidgets(2));
    expect(find.text('طلب سابق'), findsOneWidget);
    expect(tester.takeException(), isNull);
  });

  testWidgets('school support entry has support identity and backend status',
      (tester) async {
    final support = _conversation(
      id: 41,
      type: 'school_support',
      subject: 'مشكلة في تحميل الملف',
      status: 'in_progress',
      preview: 'تم تحويل الطلب إلى الإدارة',
    );

    await tester.pumpWidget(_rtl(StudentConversationsScreen(
      items: [support],
      offline: false,
      historical: false,
      onOpen: (_) {},
    )));

    expect(find.text('الدعم المدرسي'), findsOneWidget);
    expect(find.byIcon(Icons.support_agent_outlined), findsOneWidget);
    expect(find.text('مشكلة في تحميل الملف'), findsOneWidget);
    expect(find.text('تم تحويل الطلب إلى الإدارة'), findsOneWidget);
    expect(find.text('قيد المعالجة'), findsOneWidget);
  });

  testWidgets('teacher conversation keeps teacher identity', (tester) async {
    final teacher = _conversation(
      id: 42,
      type: 'teacher_student',
      subject: 'أ. أحمد محمد',
      preview: 'راجع الواجب الجديد',
    );

    await tester.pumpWidget(_rtl(StudentConversationsScreen(
      items: [teacher],
      offline: false,
      historical: false,
      onOpen: (_) {},
    )));

    expect(find.text('أ. أحمد محمد'), findsOneWidget);
    expect(find.text('الدعم المدرسي'), findsNothing);
    expect(find.byIcon(Icons.support_agent_outlined), findsNothing);
  });

  testWidgets('support tap opens the selected distinct request',
      (tester) async {
    int? openedId;
    final first = _conversation(
      id: 51,
      type: 'school_support',
      subject: 'طلب تحديث البيانات',
      status: 'open',
    );
    final second = _conversation(
      id: 52,
      type: 'school_support',
      subject: 'عذر غياب',
      status: 'closed',
    );

    await tester.pumpWidget(_rtl(StudentConversationsScreen(
      items: [first, second],
      offline: false,
      historical: false,
      onOpen: (item) => openedId = item.id,
    )));

    expect(find.text('الدعم المدرسي'), findsNWidgets(2));
    expect(find.text('طلب تحديث البيانات'), findsOneWidget);
    expect(find.text('عذر غياب'), findsOneWidget);
    expect(find.text('مفتوح'), findsOneWidget);
    expect(find.text('مغلق'), findsOneWidget);

    await tester.tap(find.text('عذر غياب'));
    await tester.pump();
    expect(openedId, 52);
  });

  testWidgets('long support subject remains safe on a narrow scaled screen',
      (tester) async {
    tester.view.physicalSize = const Size(320, 480);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);

    final support = _conversation(
      id: 61,
      type: 'school_support',
      subject:
          'استفسار طويل جدًا عن بيانات الطالب وتحديث ملفه الدراسي والمعلومات المسجلة لدى إدارة المدرسة',
      status: 'in_progress',
      preview:
          'تم استلام الطلب وسيتم التواصل مع القسم المختص بعد مراجعة البيانات',
    );

    await tester.pumpWidget(_rtl(MediaQuery(
      data: const MediaQueryData(textScaler: TextScaler.linear(1.5)),
      child: StudentConversationsScreen(
        items: [support],
        offline: false,
        historical: false,
        onOpen: (_) {},
      ),
    )));

    expect(find.text('الدعم المدرسي'), findsOneWidget);
    expect(find.text('قيد المعالجة'), findsOneWidget);
    expect(tester.takeException(), isNull);
  });
}
