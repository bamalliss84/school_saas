import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:school_saas_mobile/app/app.dart';
import 'package:school_saas_mobile/core/design_system/components.dart';
import 'package:school_saas_mobile/core/design_system/app_theme.dart';
import 'package:school_saas_mobile/core/preferences/font_preferences.dart';
import 'package:school_saas_mobile/features/student/results/data/results_repository.dart';
import 'package:school_saas_mobile/features/student/results/presentation/results_controller.dart';
import 'package:school_saas_mobile/features/student/results/presentation/results_screens.dart';
import 'package:school_saas_mobile/features/student_shell/student_shell.dart';

Widget rtl(Widget child) => ProviderScope(
    child: MaterialApp(
        home: Directionality(textDirection: TextDirection.rtl, child: child)));

void main() {
  testWidgets('login is Arabic and task focused', (tester) async {
    await tester.pumpWidget(rtl(const LoginScreen()));
    expect(find.text('مدرستي'), findsOneWidget);
    expect(find.text('رقم الجوال أو البريد الإلكتروني'), findsOneWidget);
    expect(find.text('تسجيل الدخول'), findsOneWidget);
  });

  testWidgets('historical banner clearly states read-only mode',
      (tester) async {
    await tester.pumpWidget(rtl(const Scaffold(body: HistoricalBanner())));
    expect(find.text('سياق تاريخي — العرض فقط'), findsOneWidget);
  });

  testWidgets('student navigation uses the accepted five destinations',
      (tester) async {
    await tester.pumpWidget(rtl(StudentBottomNavigation(
      selectedIndex: 0,
      onSelected: (_) {},
    )));
    for (final label in [
      'الرئيسية',
      'الواجبات',
      'النتائج',
      'الرسائل',
      'المزيد'
    ]) {
      expect(find.text(label), findsOneWidget);
    }
  });

  testWidgets('long Arabic school name tolerates 150 percent text scaling',
      (tester) async {
    await tester.pumpWidget(MediaQuery(
      data: const MediaQueryData(textScaler: TextScaler.linear(1.5)),
      child: rtl(const Scaffold(
        body: SafeArea(
          child: StudentAppHeader(
            studentName: 'طالب باسم عربي طويل للاختبار دون تجاوز حدود الشاشة',
            schoolName: 'مدرسة المستقبل العالمية للتعليم الأساسي والثانوي',
          ),
        ),
      )),
    ));
    expect(tester.takeException(), isNull);
  });

  test('last updated formatter is human readable', () {
    final now = DateTime(2026, 8, 14, 10, 35);
    expect(formatLastUpdated(now, now), 'آخر تحديث الآن');
    expect(formatLastUpdated(now.subtract(const Duration(minutes: 5)), now),
        'آخر تحديث منذ 5 دقائق');
  });
  test('selected Arabic font is preserved across customized text styles', () {
    for (final font in AppFont.values) {
      final theme = buildAppTheme(font);
      expect(theme.textTheme.headlineMedium?.fontFamily, font.family);
      expect(theme.textTheme.titleMedium?.fontFamily, font.family);
      expect(theme.textTheme.bodyMedium?.fontFamily, font.family);
      expect(theme.textTheme.labelLarge?.fontFamily, font.family);
    }
  });

  testWidgets('results screen does not render its own offline banner',
      (tester) async {
    final state = ResultsReady(StudentResultsData(
      const [],
      DateTime(2026, 8, 19, 10),
      offline: true,
    ));
    await tester.pumpWidget(rtl(Scaffold(
      body: StudentResultsScreen(
        state: state,
        historical: false,
        onTerm: (_) {},
        onSubject: (_) {},
        onExamType: (_) {},
        onOpen: (_) {},
        onRefresh: () async {},
      ),
    )));
    expect(find.byType(OfflineCacheBanner), findsNothing);
    expect(find.text('لا توجد نتائج منشورة'), findsOneWidget);
  });

}
