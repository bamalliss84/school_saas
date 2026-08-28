import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../core/errors/app_failure.dart';
import '../../core/models/auth_models.dart';
import '../../core/models/school_context.dart';
import '../../features/authentication/data/auth_repository.dart';
import '../../core/storage/session_snapshot_store.dart';
import '../../features/school_context/data/context_repository.dart';
import 'app_session.dart';

class SessionController extends StateNotifier<AppSession> {
  SessionController(
      this.auth, this.contexts, this.snapshotStore, this.purgeUserData)
      : super(const AppSession(SessionStatus.authenticating));
  final AuthRepository auth;
  final ContextRepository contexts;
  final SessionSnapshotStore snapshotStore;
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
      selected ??= _usableCurrent(result, usable) ??
          (usable.length == 1 ? usable.single : null);
      if (selected == null) {
        state = AppSession(
          usable.isEmpty
              ? SessionStatus.unavailable
              : SessionStatus.needsContext,
          contexts: usable,
        );
        return;
      }
      await selectContext(selected, available: usable);
    } on DioException catch (error) {
      final failure = error.error;
      if (failure is AppFailure && failure.kind == FailureKind.network) {
        final snapshot = await snapshotStore.read();
        if (snapshot != null) {
          state = AppSession(
            statusForContext(snapshot.context),
            user: snapshot.user,
            context: snapshot.context,
            contexts: [snapshot.context],
            offline: true,
          );
          return;
        }
        state = const AppSession(SessionStatus.unauthenticated,
            message: 'تعذر استعادة الجلسة. تحقق من الاتصال ثم حاول مجددًا');
        return;
      }
      await auth.clearLocalSession();
      await snapshotStore.clear();
      state = const AppSession(SessionStatus.unauthenticated);
    } catch (_) {
      await auth.clearLocalSession();
      await snapshotStore.clear();
      state = const AppSession(SessionStatus.unauthenticated);
    }
  }

  Future<void> login(String username, String password) async {
    await snapshotStore.clear();
    state = const AppSession(SessionStatus.authenticating);
    try {
      final login = await auth.login(username, password);
      final result = await contexts.list();
      final usable = result.contexts
          .where((c) => c.status == 'active' || c.isHistorical)
          .toList();
      final serverCurrent = _usableCurrent(result, usable);
      final selected = serverCurrent ??
          (usable.length == 1 ? usable.single : null);
      if (selected == null) {
        state = AppSession(
            usable.isEmpty
                ? SessionStatus.unavailable
                : SessionStatus.needsContext,
            user: login.user,
            contexts: usable);
      } else {
        if (serverCurrent?.membershipId == selected.membershipId) {
          await _activateKnownContext(
              selected, login.user, usable);
        } else {
          await selectContext(selected, user: login.user, available: usable);
        }
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
    final previousMembershipId = await contexts.storedMembershipId();
    try {
      await contexts.select(context);
      final resolvedUser = user ?? state.user ?? await auth.me();
      await snapshotStore
          .write(LocalSessionSnapshot(user: resolvedUser, context: context));
      state = AppSession(statusForContext(context),
          user: resolvedUser,
          context: context,
          contexts: available ?? state.contexts);
    } catch (_) {
      await contexts.restoreStoredMembership(previousMembershipId);
      rethrow;
    }
  }

  Future<void> _activateKnownContext(SchoolContext context,
      AuthenticatedUser user, List<SchoolContext> available) async {
    await Future.wait([
      contexts.restoreStoredMembership(context.membershipId),
      snapshotStore.write(LocalSessionSnapshot(user: user, context: context)),
    ]);
    state = AppSession(statusForContext(context),
        user: user, context: context, contexts: available);
  }

  /// Revalidates the current membership after an authenticated 403.
  /// Returns true only when the current school context became unavailable
  /// or was replaced, so callers can distinguish stale membership from an
  /// ordinary feature-level permission denial.
  Future<bool> revalidateCurrentContext() async {
    final currentMembershipId = state.context?.membershipId;
    if (currentMembershipId == null) return false;
    try {
      final result = await contexts.list();
      final usable = result.contexts
          .where((c) => c.status == 'active' || c.isHistorical)
          .toList();
      SchoolContext? current;
      for (final item in usable) {
        if (item.membershipId == currentMembershipId) {
          current = item;
          break;
        }
      }
      if (current != null) {
        if (state.user != null) {
          await snapshotStore
              .write(LocalSessionSnapshot(user: state.user!, context: current));
        }
        return false;
      }

      await contexts.clearStoredMembership();
      await snapshotStore.clear();
      final next = _usableCurrent(result, usable) ??
          (usable.length == 1 ? usable.single : null);
      if (next != null) {
        await selectContext(next, available: usable);
      } else {
        state = AppSession(
          usable.isEmpty
              ? SessionStatus.unavailable
              : SessionStatus.needsContext,
          user: state.user,
          contexts: usable,
          message: usable.isEmpty
              ? 'لا يوجد لديك حالياً حساب مدرسي نشط يمكنك الدخول إليه.'
              : 'اختر حساباً مدرسياً متاحاً للمتابعة',
        );
      }
      return true;
    } on DioException catch (error) {
      final failure = error.error;
      if (failure is AppFailure && failure.kind == FailureKind.network) {
        markOffline();
      }
      // If revalidation itself cannot reach the server, keep the last locally
      // validated context. Offline mode cannot discover a server-side status
      // change until connectivity returns.
      return false;
    }
  }

  SchoolContext? _usableCurrent(
      ContextListResult result, List<SchoolContext> usable) {
    final current = result.current;
    if (current == null) return null;
    for (final item in usable) {
      if (item.membershipId == current.membershipId) return item;
    }
    return null;
  }

  void markOffline() {
    if (state.status == SessionStatus.authenticated ||
        state.status == SessionStatus.historical) {
      state = AppSession(state.status,
          user: state.user,
          context: state.context,
          contexts: state.contexts,
          message: state.message,
          offline: true);
    }
  }

  void markOnline() {
    if (state.offline) {
      state = AppSession(state.status,
          user: state.user,
          context: state.context,
          contexts: state.contexts,
          message: state.message,
          offline: false);
    }
  }

  void requireContext() => state = AppSession(SessionStatus.needsContext,
      user: state.user, contexts: state.contexts);
  Future<void> expire() async {
    final localUserKey = state.user == null ? null : 'user:${state.user!.id}';
    if (localUserKey != null) await purgeUserData(localUserKey);
    await snapshotStore.clear();
    state = const AppSession(SessionStatus.sessionExpired,
        message: 'انتهت صلاحية تسجيل الدخول. يرجى تسجيل الدخول مرة أخرى للمتابعة.');
  }

  Future<void> logout() async {
    final localUserKey = state.user == null ? null : 'user:${state.user!.id}';
    try {
      await auth.logout();
    } finally {
      if (localUserKey != null) await purgeUserData(localUserKey);
      await snapshotStore.clear();
      state = AppSession.unauthenticated;
    }
  }
}
