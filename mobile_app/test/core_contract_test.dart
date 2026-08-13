import 'dart:async';

import 'package:flutter_test/flutter_test.dart';
import 'package:school_saas_mobile/app/app.dart';
import 'package:school_saas_mobile/app/session/app_session.dart';
import 'package:school_saas_mobile/core/api/refresh_coordinator.dart';
import 'package:school_saas_mobile/core/errors/app_failure.dart';
import 'package:school_saas_mobile/core/models/school_context.dart';

void main() {
  test('maps documented HTTP errors', () {
    expect(AppFailure.fromResponse(400, {}).kind, FailureKind.validation);
    expect(AppFailure.fromResponse(401, {}).kind, FailureKind.unauthorized);
    expect(AppFailure.fromResponse(403, {}).kind, FailureKind.forbidden);
    expect(AppFailure.fromResponse(404, {}).kind, FailureKind.notFound);
    expect(AppFailure.fromResponse(409, {}).kind, FailureKind.contextRequired);
    expect(AppFailure.fromResponse(503, {}).kind, FailureKind.server);
  });

  test('historical context is read-only', () {
    const context = SchoolContext(
      membershipId: 7,
      schoolName: 'مدرسة',
      role: 'student',
      status: 'historical',
      accessMode: 'historical',
      canWrite: false,
    );
    expect(context.isHistorical, isTrue);
    expect(statusForContext(context), SessionStatus.historical);
    expect(
      const AppSession(SessionStatus.historical, context: context).canWrite,
      isFalse,
    );
  });

  test('unsupported admin role becomes unavailable', () {
    const context = SchoolContext(
      membershipId: 1,
      schoolName: 'مدرسة',
      role: 'school_admin',
      status: 'active',
      accessMode: 'active',
      canWrite: true,
    );
    expect(statusForContext(context), SessionStatus.unavailable);
  });

  test('session status selects the expected route', () {
    expect(routeFor(SessionStatus.unauthenticated), '/login');
    expect(routeFor(SessionStatus.needsContext), '/contexts');
    expect(routeFor(SessionStatus.authenticated), '/home');
    expect(routeFor(SessionStatus.historical), '/home');
  });

  test('refresh coordinator shares one in-flight refresh', () async {
    final coordinator = RefreshCoordinator();
    final completer = Completer<String>();
    var calls = 0;
    Future<String> refresh() {
      calls++;
      return completer.future;
    }

    final first = coordinator.run(refresh);
    final second = coordinator.run(refresh);
    expect(calls, 1);
    completer.complete('token');
    expect(await Future.wait([first, second]), ['token', 'token']);
  });
}
