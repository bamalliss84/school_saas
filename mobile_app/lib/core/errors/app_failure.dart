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
    final kind = switch (status) {
      400 || 422 => FailureKind.validation,
      401 => FailureKind.unauthorized,
      403 => FailureKind.forbidden,
      404 => FailureKind.notFound,
      409 => FailureKind.contextRequired,
      int value when value >= 500 => FailureKind.server,
      _ => FailureKind.unknown,
    };
    final serverMessage = (map['detail'] ?? map['message'])?.toString();
    final message = switch (kind) {
      FailureKind.validation =>
        serverMessage?.trim().isNotEmpty == true ? serverMessage! : 'تعذر إكمال العملية. راجع البيانات وحاول مجددًا',
      FailureKind.unauthorized => 'انتهت جلسة تسجيل الدخول. يرجى تسجيل الدخول مجددًا',
      FailureKind.forbidden => 'ليس لديك صلاحية للوصول إلى هذه البيانات',
      FailureKind.notFound => 'تعذر العثور على البيانات المطلوبة',
      FailureKind.contextRequired => 'اختر الحساب المدرسي للمتابعة',
      FailureKind.server => 'تعذر إكمال الطلب حالياً. حاول مجددًا لاحقًا',
      _ => serverMessage?.trim().isNotEmpty == true
          ? serverMessage!
          : 'حدث خطأ غير متوقع',
    };
    return AppFailure(kind, message, statusCode: status, fields: map);
  }
}
