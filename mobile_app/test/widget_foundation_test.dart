import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:school_saas_mobile/app/app.dart';

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
}
