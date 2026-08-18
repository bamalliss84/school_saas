import 'package:dio/dio.dart';

import '../errors/app_failure.dart';

/// Only transport failures may fall back to cached school data.
/// HTTP authorization/context/server failures must stay visible to the user.
bool isOfflineEligibleError(Object error) {
  if (error is! DioException) return false;
  final failure = error.error;
  if (failure is AppFailure) return failure.kind == FailureKind.network;
  if (error.response != null) return false;
  return switch (error.type) {
    DioExceptionType.connectionTimeout ||
    DioExceptionType.sendTimeout ||
    DioExceptionType.receiveTimeout ||
    DioExceptionType.transformTimeout ||
    DioExceptionType.connectionError ||
    DioExceptionType.unknown => true,
    DioExceptionType.badCertificate ||
    DioExceptionType.badResponse ||
    DioExceptionType.cancel => false,
  };
}

String failureMessage(Object error, String fallback) {
  if (error is DioException && error.error is AppFailure) {
    return (error.error as AppFailure).message;
  }
  return fallback;
}
