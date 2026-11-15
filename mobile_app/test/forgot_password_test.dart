import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:school_saas_mobile/features/authentication/presentation/forgot_password_screen.dart';

Widget app(Widget child) =>
    MaterialApp(home: Directionality(textDirection: TextDirection.rtl, child: child));

void main() {
  testWidgets('requires an identifier and shows the generic server message', (tester) async {
    final sent = <String>[];
    await tester.pumpWidget(app(ForgotPasswordScreen(onSubmit: (value) async {
      sent.add(value);
      return 'ستصلك رسالة إذا كان الحساب موجودًا';
    })));
    await tester.tap(find.text('إرسال رابط الاستعادة'));
    await tester.pump();
    expect(find.text('أدخل اسم المستخدم أو البريد الإلكتروني.'), findsOneWidget);
    expect(sent, isEmpty);
    await tester.enterText(find.byKey(const Key('forgot-identifier')), ' parent1 ');
    await tester.tap(find.text('إرسال رابط الاستعادة'));
    await tester.pumpAndSettle();
    expect(sent, [' parent1 ']);
    expect(find.byKey(const Key('forgot-done')), findsOneWidget);
  });

  testWidgets('shows a connection error without leaving the form', (tester) async {
    await tester.pumpWidget(app(ForgotPasswordScreen(onSubmit: (_) async => throw Exception('offline'))));
    await tester.enterText(find.byKey(const Key('forgot-identifier')), 'x');
    await tester.tap(find.text('إرسال رابط الاستعادة'));
    await tester.pumpAndSettle();
    expect(find.textContaining('تعذر إرسال الطلب'), findsOneWidget);
    expect(find.byKey(const Key('forgot-identifier')), findsOneWidget);
  });
}
