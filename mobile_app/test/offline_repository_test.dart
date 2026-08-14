import 'package:flutter_test/flutter_test.dart';
import 'package:school_saas_mobile/core/offline/offline_read_repository.dart';

class FakeRemote implements RemoteReadDataSource<String> {
  FakeRemote({this.value, this.error});
  String? value;
  Object? error;
  @override
  Future<String> fetch() async {
    if (error != null) throw error!;
    return value!;
  }
}

class FakeLocal implements LocalReadDataSource<String> {
  FakeLocal({this.value, this.rejectWrite = false});
  String? value;
  bool rejectWrite;
  @override
  Future<String?> read() async => value;
  @override
  Future<void> replace(String next) async {
    if (rejectWrite) throw const FormatException('invalid remote response');
    value = next;
  }
}

void main() {
  test('remote success updates cache and returns fresh data', () async {
    final local = FakeLocal(value: 'old');
    final result =
        await OfflineReadRepository(FakeRemote(value: 'fresh'), local)
            .refreshWithFallback();
    expect(result, 'fresh');
    expect(local.value, 'fresh');
  });

  test('remote failure returns cache', () async {
    final result = await OfflineReadRepository(
            FakeRemote(error: Exception('offline')), FakeLocal(value: 'cached'))
        .refreshWithFallback();
    expect(result, 'cached');
  });

  test('remote failure without cache is controlled offline failure', () async {
    expect(
      () => OfflineReadRepository(
              FakeRemote(error: Exception('offline')), FakeLocal())
          .refreshWithFallback(),
      throwsA(isA<OfflineUnavailable>()),
    );
  });

  test('invalid remote replacement preserves old cache', () async {
    final local = FakeLocal(value: 'old', rejectWrite: true);
    final result =
        await OfflineReadRepository(FakeRemote(value: 'invalid'), local)
            .refreshWithFallback();
    expect(result, 'old');
    expect(local.value, 'old');
  });
}
