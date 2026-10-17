import 'dart:async';
import 'dart:convert';
import 'dart:typed_data';

import 'package:dio/dio.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:school_saas_mobile/core/api/api_client.dart';
import 'package:school_saas_mobile/core/errors/app_failure.dart';
import 'package:school_saas_mobile/core/storage/session_store.dart';
import 'package:school_saas_mobile/features/authentication/data/auth_repository.dart';

void main() {
  test('successful refresh updates tokens and retries the request once',
      () async {
    final store = _MemorySessionStore();
    var resourceCalls = 0;
    final apiAdapter = _CallbackAdapter((options) {
      resourceCalls++;
      return resourceCalls == 1
          ? _jsonResponse(401, {'detail': 'expired'})
          : _jsonResponse(200, {'ok': true});
    });
    final refreshAdapter = _CallbackAdapter((options) {
      expect(options.path, 'auth/refresh/');
      expect(options.data, {'refresh': 'refresh-old'});
      return _jsonResponse(
          200, {'access': 'access-new', 'refresh': 'refresh-new'});
    });
    final client =
        _client(store, apiAdapter: apiAdapter, refreshAdapter: refreshAdapter);

    final response = await client.dio.get<Map<String, dynamic>>('resource/');

    expect(response.data, {'ok': true});
    expect(resourceCalls, 2);
    expect(refreshAdapter.calls, 1);
    expect(store.access, 'access-new');
    expect(store.refresh, 'refresh-new');
    expect(store.clearCalls, 0);
  });

  for (final status in [401]) {
    test('refresh $status definitively expires the session once', () async {
      final store = _MemorySessionStore();
      var expired = 0;
      final client = _client(
        store,
        apiAdapter: _alwaysUnauthorized(),
        refreshAdapter: _CallbackAdapter(
            (_) => _jsonResponse(status, {'code': 'token_not_valid'})),
        onExpired: () async => expired++,
      );

      await expectLater(
          client.dio.get<void>('resource/'), throwsA(isA<DioException>()));

      expect(store.clearCalls, 1);
      expect(store.access, isNull);
      expect(store.refresh, isNull);
      expect(store.membershipId, isNull);
      expect(expired, 1);
    });
  }

  test('missing local refresh credential definitively expires the session',
      () async {
    final store = _MemorySessionStore(refresh: null);
    var expired = 0;
    final client = _client(
      store,
      apiAdapter: _alwaysUnauthorized(),
      refreshAdapter: _CallbackAdapter((_) => throw StateError('not called')),
      onExpired: () async => expired++,
    );

    await expectLater(
        client.dio.get<void>('resource/'), throwsA(isA<DioException>()));

    expect(store.clearCalls, 1);
    expect(expired, 1);
  });

  for (final status in [429, 500, 503]) {
    test('refresh $status preserves tokens membership and active context',
        () async {
      final store = _MemorySessionStore();
      var expired = 0;
      var activeContext = 'school:5/year:9';
      final client = _client(
        store,
        apiAdapter: _alwaysUnauthorized(),
        refreshAdapter:
            _CallbackAdapter((_) => _jsonResponse(status, {'detail': 'busy'})),
        onExpired: () async {
          expired++;
          activeContext = '';
        },
      );

      await expectLater(
          client.dio.get<void>('resource/'), throwsA(isA<DioException>()));

      expect(store.access, 'access-old');
      expect(store.refresh, 'refresh-old');
      expect(store.membershipId, 5);
      expect(store.clearCalls, 0);
      expect(activeContext, 'school:5/year:9');
      expect(expired, 0);
    });
  }

  for (final type in [
    DioExceptionType.connectionError,
    DioExceptionType.connectionTimeout,
    DioExceptionType.receiveTimeout,
  ]) {
    test('refresh $type preserves the authenticated session', () async {
      final store = _MemorySessionStore();
      var expired = 0;
      final client = _client(
        store,
        apiAdapter: _alwaysUnauthorized(),
        refreshAdapter: _CallbackAdapter((options) => throw DioException(
              requestOptions: options,
              type: type,
            )),
        onExpired: () async => expired++,
      );

      await expectLater(
          client.dio.get<void>('resource/'), throwsA(isA<DioException>()));

      expect(store.access, 'access-old');
      expect(store.refresh, 'refresh-old');
      expect(store.membershipId, 5);
      expect(store.clearCalls, 0);
      expect(expired, 0);
    });
  }

  test('ordinary API 403 never clears or expires the session', () async {
    final store = _MemorySessionStore();
    var expired = 0;
    final client = _client(
      store,
      apiAdapter: _CallbackAdapter((_) => _jsonResponse(403, {})),
      refreshAdapter: _CallbackAdapter((_) => throw StateError('not called')),
      onExpired: () async => expired++,
    );

    await expectLater(
        client.dio.get<void>('forbidden/'),
        throwsA(isA<DioException>().having(
          (error) => (error.error as AppFailure).kind,
          'failure kind',
          FailureKind.forbidden,
        )));

    expect(store.clearCalls, 0);
    expect(store.membershipId, 5);
    expect(expired, 0);
  });

  test('concurrent 401 responses share one refresh operation', () async {
    final store = _MemorySessionStore();
    final gate = Completer<void>();
    var resourceCalls = 0;
    final apiAdapter = _CallbackAdapter((_) {
      resourceCalls++;
      return resourceCalls <= 2
          ? _jsonResponse(401, {})
          : _jsonResponse(200, {'ok': true});
    });
    final refreshAdapter = _CallbackAdapter((_) async {
      await gate.future;
      return _jsonResponse(200, {'access': 'new-access'});
    });
    final client =
        _client(store, apiAdapter: apiAdapter, refreshAdapter: refreshAdapter);

    final first = client.dio.get<void>('one/');
    final second = client.dio.get<void>('two/');
    await Future<void>.delayed(Duration.zero);
    gate.complete();
    await Future.wait([first, second]);

    expect(refreshAdapter.calls, 1);
    expect(store.clearCalls, 0);
  });

  test('concurrent definitive rejection expires the session only once',
      () async {
    final store = _MemorySessionStore();
    final gate = Completer<void>();
    var expired = 0;
    final refreshAdapter = _CallbackAdapter((_) async {
      await gate.future;
      return _jsonResponse(401, {'code': 'token_not_valid'});
    });
    final client = _client(
      store,
      apiAdapter: _alwaysUnauthorized(),
      refreshAdapter: refreshAdapter,
      onExpired: () async => expired++,
    );

    final requests = [
      client.dio.get<void>('one/').catchError(
          (_) => Response<void>(requestOptions: RequestOptions(path: 'one/'))),
      client.dio.get<void>('two/').catchError(
          (_) => Response<void>(requestOptions: RequestOptions(path: 'two/'))),
    ];
    await Future<void>.delayed(Duration.zero);
    gate.complete();
    await Future.wait(requests);

    expect(refreshAdapter.calls, 1);
    expect(store.clearCalls, 1);
    expect(expired, 1);
  });

  test('a retried request cannot enter a refresh loop', () async {
    final store = _MemorySessionStore();
    final apiAdapter = _alwaysUnauthorized();
    final refreshAdapter =
        _CallbackAdapter((_) => _jsonResponse(200, {'access': 'access-new'}));
    final client =
        _client(store, apiAdapter: apiAdapter, refreshAdapter: refreshAdapter);

    await expectLater(
        client.dio.get<void>('resource/'), throwsA(isA<DioException>()));

    expect(apiAdapter.calls, 2);
    expect(refreshAdapter.calls, 1);
    expect(store.clearCalls, 0);
  });

  test('explicit logout still clears local session', () async {
    final store = _MemorySessionStore();
    final dio = Dio(BaseOptions(baseUrl: 'https://example.test/'));
    dio.httpClientAdapter =
        _CallbackAdapter((_) => _jsonResponse(205, const {}));
    final repository = AuthRepository(dio, store);

    await repository.logout();

    expect(store.clearCalls, 1);
    expect(store.access, isNull);
    expect(store.refresh, isNull);
    expect(store.membershipId, isNull);
  });
}

ApiClient _client(
  _MemorySessionStore store, {
  required _CallbackAdapter apiAdapter,
  required _CallbackAdapter refreshAdapter,
  Future<void> Function()? onExpired,
}) {
  final dio = Dio(BaseOptions(baseUrl: 'https://example.test/'))
    ..httpClientAdapter = apiAdapter;
  final refreshDio = Dio(BaseOptions(baseUrl: 'https://example.test/'))
    ..httpClientAdapter = refreshAdapter;
  return ApiClient(
    baseUrl: 'https://example.test/',
    store: store,
    dio: dio,
    refreshDio: refreshDio,
    onSessionExpired: onExpired,
  );
}

_CallbackAdapter _alwaysUnauthorized() =>
    _CallbackAdapter((_) => _jsonResponse(401, {'detail': 'expired'}));

ResponseBody _jsonResponse(int status, Object body) => ResponseBody.fromString(
      jsonEncode(body),
      status,
      headers: {
        Headers.contentTypeHeader: ['application/json'],
      },
    );

class _CallbackAdapter implements HttpClientAdapter {
  _CallbackAdapter(this.callback);
  final FutureOr<ResponseBody> Function(RequestOptions options) callback;
  int calls = 0;

  @override
  Future<ResponseBody> fetch(RequestOptions options,
      Stream<Uint8List>? requestStream, Future<void>? cancelFuture) async {
    calls++;
    return callback(options);
  }

  @override
  void close({bool force = false}) {}
}

class _MemorySessionStore implements SessionStore {
  _MemorySessionStore({
    this.access = 'access-old',
    this.refresh = 'refresh-old',
    this.membershipId = 5,
  });
  String? access;
  String? refresh;
  int? membershipId;
  int clearCalls = 0;

  @override
  Future<void> clear() async {
    clearCalls++;
    access = null;
    refresh = null;
    membershipId = null;
  }

  @override
  Future<String?> readAccessToken() async => access;

  @override
  Future<int?> readMembershipId() async => membershipId;

  @override
  Future<String?> readRefreshToken() async => refresh;

  @override
  Future<void> writeMembershipId(int? membershipId) async {
    this.membershipId = membershipId;
  }

  @override
  Future<void> writeTokens(
      {required String access, required String refresh}) async {
    this.access = access;
    this.refresh = refresh;
  }
}
