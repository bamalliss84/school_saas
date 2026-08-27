import 'package:dio/dio.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:school_saas_mobile/app/session/session_controller.dart';
import 'package:school_saas_mobile/core/models/school_context.dart';
import 'package:school_saas_mobile/core/storage/session_snapshot_store.dart';
import 'package:school_saas_mobile/core/storage/session_store.dart';
import 'package:school_saas_mobile/features/authentication/data/auth_repository.dart';
import 'package:school_saas_mobile/features/school_context/data/context_repository.dart';

class MemorySessionStore implements SessionStore {
  String? access, refresh;
  int? membershipId;
  @override
  Future<void> clear() async {
    access = null;
    refresh = null;
    membershipId = null;
  }

  @override
  Future<String?> readAccessToken() async => access;
  @override
  Future<String?> readRefreshToken() async => refresh;
  @override
  Future<int?> readMembershipId() async => membershipId;
  @override
  Future<void> writeMembershipId(int? value) async => membershipId = value;
  @override
  Future<void> writeTokens(
      {required String access, required String refresh}) async {
    this.access = access;
    this.refresh = refresh;
  }
}

class MemorySnapshotStore implements SessionSnapshotStore {
  LocalSessionSnapshot? value;
  bool failWrites = false;
  @override
  Future<void> clear() async => value = null;
  @override
  Future<LocalSessionSnapshot?> read() async => value;
  @override
  Future<void> write(LocalSessionSnapshot snapshot) async {
    if (failWrites) throw StateError('disk unavailable');
    value = snapshot;
  }
}

void main() {
  test('failed context switch restores stored membership and old session',
      () async {
    const current = SchoolContext(
        membershipId: 10,
        schoolName: 'مدرسة النور',
        role: 'student',
        status: 'active',
        accessMode: 'active',
        canWrite: true,
        academicYearName: '2026/2027');
    const next = SchoolContext(
        membershipId: 20,
        schoolName: 'مدرسة الأمل',
        role: 'student',
        status: 'active',
        accessMode: 'active',
        canWrite: true,
        academicYearName: '2026/2027');
    final store = MemorySessionStore();
    final snapshots = MemorySnapshotStore();
    final dio = Dio();
    dio.interceptors.add(InterceptorsWrapper(onRequest: (options, handler) {
      dynamic data;
      if (options.path == 'auth/login/') {
        data = {
          'access': 'a',
          'refresh': 'r',
          'user': {
            'id': 1,
            'username': 'student',
            'full_name': 'محمد',
            'role': 'student'
          }
        };
      } else if (options.path == 'auth/contexts/') {
        data = {
          'contexts': [
            {
              'membership_id': 10,
              'school': {'name': 'مدرسة النور'},
              'role': 'student',
              'status': 'active',
              'access_mode': 'active',
              'can_write': true,
              'academic_year': {'name': '2026/2027'}
            },
            {
              'membership_id': 20,
              'school': {'name': 'مدرسة الأمل'},
              'role': 'student',
              'status': 'active',
              'access_mode': 'active',
              'can_write': true,
              'academic_year': {'name': '2026/2027'}
            },
          ],
          'current_context': {
            'membership_id': 10,
            'school': {'name': 'مدرسة النور'},
            'role': 'student',
            'status': 'active',
            'access_mode': 'active',
            'can_write': true,
            'academic_year': {'name': '2026/2027'}
          },
        };
      }
      handler.resolve(Response(requestOptions: options, data: data));
    }));
    final controller = SessionController(AuthRepository(dio, store),
        ContextRepository(dio, store), snapshots, (_) async {});
    await controller.login('student', 'secret');
    expect(controller.state.context?.membershipId, current.membershipId);
    expect(store.membershipId, current.membershipId);
    snapshots.failWrites = true;

    await expectLater(controller.selectContext(next), throwsStateError);

    expect(store.membershipId, current.membershipId);
    expect(controller.state.context?.membershipId, current.membershipId);
  });
}
