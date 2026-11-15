import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:school_saas_mobile/features/authentication/presentation/change_password_screen.dart';

Widget app(Widget child) =>
    MaterialApp(home: Directionality(textDirection: TextDirection.rtl, child: child));

void main() {
  testWidgets('validates, submits and then signs out', (tester) async {
    final calls = <List<String>>[];
    var signedOut = false;
    await tester.pumpWidget(app(ChangePasswordScreen(
      onSubmit: (current, next) async => calls.add([current, next]),
      onDone: () async => signedOut = true,
    )));
    await tester.enterText(find.byKey(const Key('cp-current')), 'old-pass-1');
    await tester.enterText(find.byKey(const Key('cp-new')), 'Strong-Pass-1');
    await tester.enterText(find.byKey(const Key('cp-confirm')), 'Other-Pass-1');
    await tester.tap(find.text('حفظ'));
    await tester.pump();
    expect(find.text('كلمتا المرور غير متطابقتين.'), findsOneWidget);
    expect(calls, isEmpty);
    await tester.enterText(find.byKey(const Key('cp-confirm')), 'Strong-Pass-1');
    await tester.tap(find.text('حفظ'));
    await tester.pumpAndSettle();
    expect(calls.single, ['old-pass-1', 'Strong-Pass-1']);
    expect(find.byKey(const Key('change-password-done')), findsOneWidget);
    await tester.tap(find.text('تسجيل الدخول من جديد'));
    await tester.pumpAndSettle();
    expect(signedOut, isTrue);
  });

  testWidgets('shows a failure message and keeps the form', (tester) async {
    await tester.pumpWidget(app(ChangePasswordScreen(
      onSubmit: (_, __) async => throw Exception('offline'),
      onDone: () async {},
    )));
    await tester.enterText(find.byKey(const Key('cp-current')), 'x');
    await tester.enterText(find.byKey(const Key('cp-new')), 'Strong-Pass-1');
    await tester.enterText(find.byKey(const Key('cp-confirm')), 'Strong-Pass-1');
    await tester.tap(find.text('حفظ'));
    await tester.pumpAndSettle();
    expect(find.textContaining('تعذر تغيير كلمة المرور'), findsOneWidget);
  });
}
