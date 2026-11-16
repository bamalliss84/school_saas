import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:school_saas_mobile/app/bootstrap.dart';
import 'package:school_saas_mobile/core/config/app_environment.dart';

void main() {
  test('debug and test builds accept the local development server', () {
    expect(
        AppEnvironment.releaseProblem('http://10.0.2.2:8000/api/v1/',
            isRelease: false),
        isNull);
  });

  test('release builds require a real HTTPS server', () {
    expect(
        AppEnvironment.releaseProblem('https://school.example.com/api/v1/',
            isRelease: true),
        isNull);
    for (final bad in [
      'http://school.example.com/api/v1/',
      'http://10.0.2.2:8000/api/v1/',
      'https://localhost/api/v1/',
      'https://10.0.2.2/api/v1/',
      'not a url',
      '',
    ]) {
      expect(AppEnvironment.releaseProblem(bad, isRelease: true), isNotNull,
          reason: bad);
    }
  });

  testWidgets('a misconfigured store build shows a clear Arabic message',
      (tester) async {
    await tester.pumpWidget(const MisconfiguredBuildApp(message: 'خطأ في الإعداد'));
    expect(find.text('خطأ في الإعداد'), findsOneWidget);
    expect(find.byIcon(Icons.cloud_off_outlined), findsOneWidget);
  });
}
