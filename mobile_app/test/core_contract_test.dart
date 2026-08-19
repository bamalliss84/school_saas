import 'dart:async';

import 'package:dio/dio.dart';

import 'package:flutter_test/flutter_test.dart';
import 'package:school_saas_mobile/app/app.dart';
import 'package:school_saas_mobile/app/session/app_session.dart';
import 'package:school_saas_mobile/core/api/refresh_coordinator.dart';
import 'package:school_saas_mobile/core/errors/app_failure.dart';
import 'package:school_saas_mobile/core/models/school_context.dart';
import 'package:school_saas_mobile/core/models/auth_models.dart';
import 'package:school_saas_mobile/core/storage/session_snapshot_store.dart';
import 'package:school_saas_mobile/core/offline/offline_error_policy.dart';

void main() {
  test('maps documented HTTP errors', () {
    expect(AppFailure.fromResponse(400, {}).kind, FailureKind.validation);
    expect(AppFailure.fromResponse(401, {}).kind, FailureKind.unauthorized);
    expect(AppFailure.fromResponse(403, {}).kind, FailureKind.forbidden);
    expect(AppFailure.fromResponse(404, {}).kind, FailureKind.notFound);
    expect(AppFailure.fromResponse(409, {}).kind, FailureKind.contextRequired);
    expect(AppFailure.fromResponse(503, {}).kind, FailureKind.server);
  });

  test('offline fallback accepts transport errors but rejects HTTP errors', () {
    final request = RequestOptions(path: '/student/data');
    expect(
      isOfflineEligibleError(DioException(
        requestOptions: request,
        type: DioExceptionType.connectionError,
      )),
      isTrue,
    );
    expect(
      isOfflineEligibleError(DioException(
        requestOptions: request,
        response: Response(requestOptions: request, statusCode: 403),
        type: DioExceptionType.badResponse,
        error: const AppFailure(FailureKind.forbidden, 'ممنوع', statusCode: 403),
      )),
      isFalse,
    );
  });


  test('HTTP access errors use safe Arabic messages', () {
    expect(AppFailure.fromResponse(403, {'detail': 'You do not have permission'}).message,
        'ليس لديك صلاحية للوصول إلى هذه البيانات');
    expect(AppFailure.fromResponse(404, {'detail': 'Not found'}).message,
        'تعذر العثور على البيانات المطلوبة');
  });

  test('local session snapshot round-trips user and context safely', () {
    const snapshot = LocalSessionSnapshot(
      user: AuthenticatedUser(
          id: 9, username: 'student', fullName: 'طالب', role: 'student'),
      context: SchoolContext(
        membershipId: 42,
        schoolName: 'مدرسة',
        role: 'student',
        status: 'active',
        accessMode: 'active',
        canWrite: true,
        academicYearName: '2026',
        academicYearId: 3,
      ),
    );
    final restored = LocalSessionSnapshot.fromJson(
        Map<String, dynamic>.from(snapshot.toJson()));
    expect(restored.user.id, 9);
    expect(restored.context.membershipId, 42);
    expect(restored.context.academicYearId, 3);
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

  test('suspended membership is unavailable, not historical', () {
    const context = SchoolContext(
      membershipId: 8,
      schoolName: 'مدرسة',
      role: 'student',
      status: 'suspended',
      accessMode: 'unavailable',
      canWrite: false,
    );
    expect(context.isHistorical, isFalse);
    expect(context.isUnavailable, isTrue);
    expect(statusForContext(context), SessionStatus.unavailable);
  });

  test('ended membership is unavailable, not historical', () {
    const context = SchoolContext(
      membershipId: 9,
      schoolName: 'مدرسة',
      role: 'student',
      status: 'ended',
      accessMode: 'unavailable',
      canWrite: false,
    );
    expect(context.isHistorical, isFalse);
    expect(context.isUnavailable, isTrue);
    expect(statusForContext(context), SessionStatus.unavailable);
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
