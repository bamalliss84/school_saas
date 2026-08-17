import 'package:dio/dio.dart';

import '../errors/app_failure.dart';
import '../storage/session_store.dart';
import 'refresh_coordinator.dart';

class ApiClient {
  ApiClient({
    required String baseUrl,
    required SessionStore store,
    Dio? dio,
    Dio? refreshDio,
    RefreshCoordinator? coordinator,
    this.onSessionExpired,
    this.onContextRequired,
  })  : _store = store,
        _dio = dio ?? Dio(BaseOptions(baseUrl: baseUrl)),
        _refreshDio = refreshDio ?? Dio(BaseOptions(baseUrl: baseUrl)),
        _coordinator = coordinator ?? RefreshCoordinator() {
    _dio.interceptors.add(
      InterceptorsWrapper(onRequest: _onRequest, onError: _onError),
    );
  }
  final Dio _dio;
  final Dio _refreshDio;
  final SessionStore _store;
  final RefreshCoordinator _coordinator;
  Future<void> Function()? onSessionExpired;
  void Function()? onContextRequired;
  Dio get dio => _dio;

  Future<void> _onRequest(
    RequestOptions options,
    RequestInterceptorHandler handler,
  ) async {
    final access = await _store.readAccessToken();
    final membership = await _store.readMembershipId();
    if (access != null) {
      options.headers['Authorization'] = 'Bearer $access';
    }
    if (membership != null && !_isContextIndependentAuthPath(options.path)) {
      options.headers['X-School-Membership-ID'] = membership;
    }
    handler.next(options);
  }

  Future<void> _onError(
    DioException error,
    ErrorInterceptorHandler handler,
  ) async {
    if (error.response?.statusCode == 409) onContextRequired?.call();
    if (error.response?.statusCode == 401 &&
        error.requestOptions.extra['retried'] != true &&
        !error.requestOptions.path.contains('auth/login')) {
      try {
        final token = await _coordinator.run(_refresh);
        final request = error.requestOptions;
        request.extra['retried'] = true;
        request.headers['Authorization'] = 'Bearer $token';
        return handler.resolve(await _dio.fetch(request));
      } catch (_) {
        await _store.clear();
        await onSessionExpired?.call();
      }
    }
    final failure = error.response == null && _isNetworkFailure(error.type)
        ? const AppFailure(FailureKind.network, 'تعذر الاتصال بالخادم')
        : AppFailure.fromResponse(
            error.response?.statusCode,
            error.response?.data,
          );
    handler.reject(
      DioException(
        requestOptions: error.requestOptions,
        response: error.response,
        type: error.type,
        error: failure,
      ),
    );
  }

  Future<String> _refresh() async {
    final refresh = await _store.readRefreshToken();
    if (refresh == null) {
      throw const AppFailure(FailureKind.unauthorized, 'انتهت الجلسة');
    }
    final response = await _refreshDio.post<Map<String, dynamic>>(
      'auth/refresh/',
      data: {'refresh': refresh},
    );
    final access = response.data!['access'].toString();
    await _store.writeTokens(
      access: access,
      refresh: response.data?['refresh']?.toString() ?? refresh,
    );
    return access;
  }
}


bool _isContextIndependentAuthPath(String path) =>
    path.contains('auth/login') ||
    path.contains('auth/refresh') ||
    path.contains('auth/logout') ||
    path.contains('auth/contexts') ||
    path.contains('auth/context/default');

bool _isNetworkFailure(DioExceptionType type) => switch (type) {
      DioExceptionType.connectionTimeout ||
      DioExceptionType.sendTimeout ||
      DioExceptionType.receiveTimeout ||
      DioExceptionType.connectionError ||
      DioExceptionType.unknown => true,
      _ => false,
    };
