import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../core/errors/app_failure.dart';
import '../../core/models/auth_models.dart';
import '../../core/models/school_context.dart';
import '../../features/authentication/data/auth_repository.dart';
import '../../features/school_context/data/context_repository.dart';
import 'app_session.dart';

class SessionController extends StateNotifier<AppSession> {
  SessionController(this.auth, this.contexts, this.purgeUserData)
      : super(const AppSession(SessionStatus.authenticating));
  final AuthRepository auth;
  final ContextRepository contexts;
  final Future<void> Function(String localUserKey) purgeUserData;

  Future<void> bootstrap() async {
    try {
      final refresh = await auth.storedRefreshToken();
      final access = await auth.storedAccessToken();
      if (refresh == null && access == null) {
        state = AppSession.unauthenticated;
        return;
      }

      // Context discovery is intentionally first: this endpoint is independent
      // from a possibly stale membership header and lets us recover safely.
      final result = await contexts.list();
      final usable = result.contexts
          .where((c) => c.status == 'active' || c.isHistorical)
          .toList();
      final storedMembershipId = await contexts.storedMembershipId();
      SchoolContext? selected;
      if (storedMembershipId != null) {
        for (final item in usable) {
          if (item.membershipId == storedMembershipId) {
            selected = item;
            break;
          }
        }
        if (selected == null) await contexts.clearStoredMembership();
      }
      selected ??= result.current ?? (usable.length == 1 ? usable.single : null);
      if (selected == null) {
        state = AppSession(
          usable.isEmpty ? SessionStatus.unavailable : SessionStatus.needsContext,
          contexts: usable,
        );
        return;
      }
      await selectContext(selected, available: usable);
    } on DioException catch (error) {
      final failure = error.error;
      if (failure is AppFailure && failure.kind == FailureKind.network) {
        state = const AppSession(SessionStatus.unauthenticated,
            message: 'تعذر استعادة الجلسة. تحقق من الاتصال ثم حاول مجددًا');
        return;
      }
      await auth.clearLocalSession();
      state = const AppSession(SessionStatus.unauthenticated);
    } catch (_) {
      await auth.clearLocalSession();
      state = const AppSession(SessionStatus.unauthenticated);
    }
  }

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
    final resolvedUser = user ?? state.user ?? await auth.me();
    state = AppSession(statusForContext(context),
        user: resolvedUser,
        context: context,
        contexts: available ?? state.contexts);
  }

  void requireContext() => state = AppSession(SessionStatus.needsContext,
      user: state.user, contexts: state.contexts);
  Future<void> expire() async {
    final localUserKey = state.user == null ? null : 'user:${state.user!.id}';
    if (localUserKey != null) await purgeUserData(localUserKey);
    state = const AppSession(SessionStatus.sessionExpired,
        message: 'انتهت الجلسة، سجّل الدخول مجددًا');
  }

  Future<void> logout() async {
    final localUserKey = state.user == null ? null : 'user:${state.user!.id}';
    try {
      await auth.logout();
    } finally {
      if (localUserKey != null) await purgeUserData(localUserKey);
      state = AppSession.unauthenticated;
    }
  }
}
