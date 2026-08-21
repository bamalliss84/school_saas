import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:school_saas_mobile/features/student/communications/data/communications_repository.dart';
import 'package:school_saas_mobile/features/student/communications/domain/communication_models.dart';
import 'package:school_saas_mobile/features/student/communications/presentation/communications_screens.dart';

Widget _rtl(Widget child) => MaterialApp(
      home: Directionality(
        textDirection: TextDirection.rtl,
        child: Scaffold(body: SafeArea(child: child)),
      ),
    );

CommunicationsSnapshot _snapshot(List<CommunicationNotification> notifications) =>
    CommunicationsSnapshot(
      notifications: notifications,
      announcements: const [],
      conversations: const [],
      badges: const CommunicationBadges(0, 0),
      lastUpdated: DateTime(2026, 8, 21, 10),
    );

void main() {
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
    )));

    await tester.tap(find.text('تم نشر نتيجة جديدة'));
    await tester.pump();
    expect(opened, 1);
  });

  testWidgets('historical notification remains read only', (tester) async {
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
    )));

    await tester.tap(find.text('نتيجة تاريخية'));
    await tester.pump();
    expect(opened, 0);
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
}
