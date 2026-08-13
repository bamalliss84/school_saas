enum FailureKind {
  validation,
  unauthorized,
  forbidden,
  notFound,
  contextRequired,
  server,
  network,
  unknown
}

class AppFailure implements Exception {
  const AppFailure(this.kind, this.message,
      {this.statusCode, this.fields = const {}});
  final FailureKind kind;
  final String message;
  final int? statusCode;
  final Map<String, dynamic> fields;

  factory AppFailure.fromResponse(int? status, dynamic data) {
    final map =
        data is Map ? Map<String, dynamic>.from(data) : <String, dynamic>{};
    final message =
        (map['detail'] ?? map['message'] ?? 'حدث خطأ غير متوقع').toString();
    final kind = switch (status) {
      400 || 422 => FailureKind.validation,
      401 => FailureKind.unauthorized,
      403 => FailureKind.forbidden,
      404 => FailureKind.notFound,
      409 => FailureKind.contextRequired,
      int value when value >= 500 => FailureKind.server,
      _ => FailureKind.unknown,
    };
    return AppFailure(kind, message, statusCode: status, fields: map);
  }
}
