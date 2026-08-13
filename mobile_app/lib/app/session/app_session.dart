import '../../core/models/auth_models.dart';
import '../../core/models/school_context.dart';

enum SessionStatus {
  unauthenticated,
  authenticating,
  needsContext,
  authenticated,
  historical,
  unavailable,
  sessionExpired
}

class AppSession {
  const AppSession(this.status,
      {this.user, this.context, this.contexts = const [], this.message});
  final SessionStatus status;
  final AuthenticatedUser? user;
  final SchoolContext? context;
  final List<SchoolContext> contexts;
  final String? message;
  static const unauthenticated = AppSession(SessionStatus.unauthenticated);
  bool get canWrite =>
      status == SessionStatus.authenticated && (context?.canWrite ?? false);
}

SessionStatus statusForContext(SchoolContext context) {
  if (!{'student', 'parent', 'teacher'}.contains(context.role)) {
    return SessionStatus.unavailable;
  }
  return context.isHistorical
      ? SessionStatus.historical
      : SessionStatus.authenticated;
}
