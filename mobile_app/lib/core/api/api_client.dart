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
    this.onForbidden,
    this.onNetworkUnavailable,
    this.onConnectionRestored,
  })  : _store = store,
        _dio = dio ?? Dio(BaseOptions(baseUrl: baseUrl)),
        _refreshDio = refreshDio ?? Dio(BaseOptions(baseUrl: baseUrl)),
        _coordinator = coordinator ?? RefreshCoordinator() {
    _dio.interceptors.add(
      InterceptorsWrapper(
        onRequest: _onRequest,
        onResponse: (response, handler) {
          if (response.requestOptions.path.contains('auth/login')) {
            _sessionExpirationNotified = false;
          }
          onConnectionRestored?.call();
          handler.next(response);
        },
        onError: _onError,
      ),
    );
  }
  final Dio _dio;
  final Dio _refreshDio;
  final SessionStore _store;
  final RefreshCoordinator _coordinator;
  bool _sessionExpirationNotified = false;
  Future<void> Function()? onSessionExpired;
  void Function()? onContextRequired;
  Future<bool> Function()? onForbidden;
  void Function()? onNetworkUnavailable;
  void Function()? onConnectionRestored;
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
    var invalidSchoolContext = false;
    if (error.response?.statusCode == 403 && onForbidden != null) {
      invalidSchoolContext = await onForbidden!();
    }
    if (error.response?.statusCode == 401 &&
        error.requestOptions.extra['retried'] != true &&
        !error.requestOptions.path.contains('auth/login')) {
      late final String token;
      try {
        token = await _coordinator.run(_refresh);
      } catch (refreshError) {
        if (_isDefinitiveRefreshRejection(refreshError)) {
          await _expireSessionOnce();
        }
        return handler.reject(_refreshFailure(error, refreshError));
      }
      final request = error.requestOptions;
      request.extra['retried'] = true;
      request.headers['Authorization'] = 'Bearer $token';
      return handler.resolve(await _dio.fetch(request));
    }
    final isNetwork = error.response == null && _isNetworkFailure(error.type);
    if (isNetwork) onNetworkUnavailable?.call();
    final failure = isNetwork
        ? const AppFailure(FailureKind.network, 'تعذر الاتصال بالخادم')
        : invalidSchoolContext
            ? const AppFailure(
                FailureKind.forbidden,
                'هذا الحساب المدرسي غير متاح حالياً',
                statusCode: 403,
              )
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
    _sessionExpirationNotified = false;
    await _store.writeTokens(
      access: access,
      refresh: response.data?['refresh']?.toString() ?? refresh,
    );
    return access;
  }

  Future<void> _expireSessionOnce() async {
    if (_sessionExpirationNotified) return;
    _sessionExpirationNotified = true;
    await _store.clear();
    await onSessionExpired?.call();
  }

  DioException _refreshFailure(DioException original, Object refreshError) {
    if (refreshError is DioException) {
      final isNetwork =
          refreshError.response == null && _isNetworkFailure(refreshError.type);
      if (isNetwork) onNetworkUnavailable?.call();
      return DioException(
        requestOptions: original.requestOptions,
        response: refreshError.response,
        type: refreshError.type,
        error: isNetwork
            ? const AppFailure(FailureKind.network, 'تعذر الاتصال بالخادم')
            : AppFailure.fromResponse(
                refreshError.response?.statusCode,
                refreshError.response?.data,
              ),
      );
    }
    final failure = refreshError is AppFailure
        ? refreshError
        : const AppFailure(FailureKind.unknown, 'حدث خطأ غير متوقع');
    return DioException(
      requestOptions: original.requestOptions,
      error: failure,
    );
  }
}

bool _isDefinitiveRefreshRejection(Object error) {
  if (error is AppFailure) return error.kind == FailureKind.unauthorized;
  if (error is DioException) {
    if (error.error case AppFailure(:final kind)) {
      return kind == FailureKind.unauthorized;
    }
    return error.response?.statusCode == 401;
  }
  return false;
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
      DioExceptionType.unknown =>
        true,
      _ => false,
    };
