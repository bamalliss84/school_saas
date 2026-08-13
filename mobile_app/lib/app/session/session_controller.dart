import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../core/errors/app_failure.dart';
import '../../core/models/auth_models.dart';
import '../../core/models/school_context.dart';
import '../../features/authentication/data/auth_repository.dart';
import '../../features/school_context/data/context_repository.dart';
import 'app_session.dart';

class SessionController extends StateNotifier<AppSession> {
  SessionController(this.auth, this.contexts)
      : super(AppSession.unauthenticated);
  final AuthRepository auth;
  final ContextRepository contexts;
  Future<void> login(String username, String password) async {
    state = const AppSession(SessionStatus.authenticating);
    try {
      final login = await auth.login(username, password);
      final result = await contexts.list();
      final usable = result.contexts
          .where((c) => c.status == 'active' || c.isHistorical)
          .toList();
      final selected =
          result.current ?? (usable.length == 1 ? usable.single : null);
      if (selected == null) {
        state = AppSession(
            usable.isEmpty
                ? SessionStatus.unavailable
                : SessionStatus.needsContext,
            user: login.user,
            contexts: usable);
      } else {
        await selectContext(selected, user: login.user, available: usable);
      }
    } on DioException catch (error) {
      final failure = error.error;
      state = AppSession(SessionStatus.unauthenticated,
          message:
              failure is AppFailure ? failure.message : 'تعذر الاتصال بالخادم');
    } catch (_) {
      state = const AppSession(SessionStatus.unauthenticated,
          message: 'تعذر الاتصال بالخادم');
    }
  }

  Future<void> selectContext(SchoolContext context,
      {AuthenticatedUser? user, List<SchoolContext>? available}) async {
    await contexts.select(context);
    state = AppSession(statusForContext(context),
        user: user ?? state.user,
        context: context,
        contexts: available ?? state.contexts);
  }

  void requireContext() => state = AppSession(SessionStatus.needsContext,
      user: state.user, contexts: state.contexts);
  void expire() => state = const AppSession(SessionStatus.sessionExpired,
      message: 'انتهت الجلسة، سجّل الدخول مجددًا');
  Future<void> logout() async {
    await auth.logout();
    state = AppSession.unauthenticated;
  }
}
