import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../core/api/api_client.dart';
import '../core/config/app_environment.dart';
import '../core/design_system/app_theme.dart';
import '../core/design_system/components.dart';
import '../core/local_database/app_database.dart';
import '../core/local_database/local_data_purge_service.dart';
import '../core/preferences/font_preferences.dart';
import '../core/storage/session_store.dart';
import '../core/storage/session_snapshot_store.dart';
import '../features/authentication/data/auth_repository.dart';
import '../features/school_context/data/context_repository.dart';
import '../features/student_shell/student_shell.dart';
import '../features/teacher_shell/teacher_shell.dart';
import 'session/app_session.dart';
import 'session/session_controller.dart';

final storeProvider = Provider<SessionStore>((ref) => SecureSessionStore());
final sessionSnapshotStoreProvider = Provider<SessionSnapshotStore>(
    (ref) => SharedPreferencesSessionSnapshotStore());
final databaseProvider = Provider<AppDatabase>((ref) {
  final database = AppDatabase();
  ref.onDispose(database.close);
  return database;
});
final purgeUserDataProvider = Provider<Future<void> Function(String)>((ref) =>
    (localUserKey) => LocalDataPurgeService(ref.read(databaseProvider))
        .purgeCurrentUserData(localUserKey));
final apiProvider = Provider<ApiClient>((ref) => ApiClient(
    baseUrl: AppEnvironment.apiBaseUrl, store: ref.read(storeProvider)));
final sessionProvider =
    StateNotifierProvider<SessionController, AppSession>((ref) {
  final client = ref.read(apiProvider);
  final controller = SessionController(
    AuthRepository(client.dio, ref.read(storeProvider)),
    ContextRepository(client.dio, ref.read(storeProvider)),
    ref.read(sessionSnapshotStoreProvider),
    ref.read(purgeUserDataProvider),
  );
  client.onContextRequired = controller.requireContext;
  client.onSessionExpired = controller.expire;
  client.onForbidden = controller.revalidateCurrentContext;
  client.onNetworkUnavailable = controller.markOffline;
  client.onConnectionRestored = controller.markOnline;
  Future<void>.microtask(controller.bootstrap);
  return controller;
});

String routeFor(SessionStatus status) => switch (status) {
      SessionStatus.unauthenticated || SessionStatus.sessionExpired => '/login',
      SessionStatus.authenticating => '/loading',
      SessionStatus.needsContext => '/contexts',
      SessionStatus.authenticated || SessionStatus.historical => '/home',
      SessionStatus.unavailable => '/unavailable',
    };

class SchoolSaaSApp extends ConsumerWidget {
  const SchoolSaaSApp({super.key});
  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final status = ref.watch(sessionProvider.select((session) => session.status));
    final router = GoRouter(initialLocation: routeFor(status), routes: [
      GoRoute(path: '/login', builder: (_, __) => const LoginScreen()),
      GoRoute(path: '/loading', builder: (_, __) => const LoadingScreen()),
      GoRoute(path: '/contexts', builder: (_, __) => const ContextScreen()),
      GoRoute(path: '/home', builder: (_, __) => const RoleShell()),
      GoRoute(
          path: '/unavailable', builder: (_, __) => const UnavailableScreen()),
    ]);
    return _AppThemeHost(router: router);
  }
}

class _AppThemeHost extends StatelessWidget {
  const _AppThemeHost({required this.router});
  final GoRouter router;
  @override
  Widget build(BuildContext context) => MaterialApp.router(
        title: 'مدرستي',
        debugShowCheckedModeBanner: false,
        locale: const Locale('ar'),
        builder: (context, child) => _DynamicAppTheme(child: child!),
        routerConfig: router,
      );
}

class _DynamicAppTheme extends ConsumerWidget {
  const _DynamicAppTheme({required this.child});
  final Widget child;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final font = ref.watch(fontProvider);
    return Theme(
      data: buildAppTheme(font),
      child: Directionality(textDirection: TextDirection.rtl, child: child),
    );
  }
}

class LoadingScreen extends StatelessWidget {
  const LoadingScreen({super.key});
  @override
  Widget build(BuildContext context) =>
      const Scaffold(body: Center(child: CircularProgressIndicator()));
}

class LoginScreen extends ConsumerStatefulWidget {
  const LoginScreen({super.key});
  @override
  ConsumerState<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends ConsumerState<LoginScreen> {
  final username = TextEditingController();
  final password = TextEditingController();
  @override
  void dispose() {
    username.dispose();
    password.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final state = ref.watch(sessionProvider);
    final expired = state.status == SessionStatus.sessionExpired;
    return Scaffold(
        body: SafeArea(
            child: Center(
                child: SingleChildScrollView(
                    padding: const EdgeInsets.all(24),
                    child: ConstrainedBox(
                        constraints: const BoxConstraints(maxWidth: 420),
                        child:
                            Column(mainAxisSize: MainAxisSize.min, children: [
                          Icon(
                            expired
                                ? Icons.error_outline
                                : Icons.school_rounded,
                            size: 72,
                            color: expired
                                ? Theme.of(context).colorScheme.error
                                : null,
                          ),
                          const SizedBox(height: 16),
                          Text(
                            expired ? 'انتهت جلسة تسجيل الدخول' : 'مدرستي',
                            style: Theme.of(context).textTheme.headlineMedium,
                            textAlign: TextAlign.center,
                          ),
                          if (expired) ...[
                            const SizedBox(height: 8),
                            const Text(
                              'انتهت صلاحية تسجيل الدخول.\nيرجى تسجيل الدخول مرة أخرى للمتابعة.',
                              textAlign: TextAlign.center,
                            ),
                          ],
                          const SizedBox(height: 32),
                          TextField(
                              controller: username,
                              decoration: const InputDecoration(
                                  labelText:
                                      'رقم الجوال أو البريد الإلكتروني')),
                          const SizedBox(height: 12),
                          TextField(
                              controller: password,
                              obscureText: true,
                              decoration: const InputDecoration(
                                  labelText: 'كلمة المرور')),
                          const SizedBox(height: 16),
                          if (state.message != null && !expired)
                            Text(state.message!,
                                style: TextStyle(
                                    color:
                                        Theme.of(context).colorScheme.error)),
                          const SizedBox(height: 8),
                          FilledButton(
                              onPressed: () => ref
                                  .read(sessionProvider.notifier)
                                  .login(username.text, password.text),
                              child: const Text('تسجيل الدخول')),
                        ]))))));
  }
}

class ContextScreen extends ConsumerWidget {
  const ContextScreen({super.key});
  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final contexts = ref.watch(sessionProvider).contexts;
    return Scaffold(
        appBar: AppBar(title: const Text('اختر المدرسة والسياق')),
        body: ListView.separated(
            padding: const EdgeInsets.all(16),
            itemCount: contexts.length,
            separatorBuilder: (_, __) => const SizedBox(height: 8),
            itemBuilder: (_, index) {
              final item = contexts[index];
              return Card(
                  child: ListTile(
                      title: Text(item.schoolName),
                      subtitle: Text(
                          '${item.role} • ${item.academicYearName ?? ''}${item.isHistorical ? ' • تاريخي' : ''}'),
                      trailing: const Icon(Icons.chevron_left),
                      onTap: () => ref
                          .read(sessionProvider.notifier)
                          .selectContext(item)));
            }));
  }
}

class HistoricalBanner extends StatelessWidget {
  const HistoricalBanner({super.key});
  @override
  Widget build(BuildContext context) => const HistoricalContextBanner();
}

class RoleShell extends ConsumerStatefulWidget {
  const RoleShell({super.key});
  @override
  ConsumerState<RoleShell> createState() => _RoleShellState();
}

class _RoleShellState extends ConsumerState<RoleShell> {
  int selected = 0;
  @override
  Widget build(BuildContext context) {
    final session = ref.watch(sessionProvider);
    final school = session.context;
    final role = school?.role ?? '';
    if (role == 'student') {
      return StudentShell(key: ValueKey(school?.membershipId));
    }
    if (role == 'teacher') {
      return TeacherShell(key: ValueKey(school?.membershipId));
    }
    final labels = switch (role) {
      'student' => ['الرئيسية', 'الجدول', 'الواجبات', 'النتائج', 'الإشعارات'],
      'parent' => ['الرئيسية', 'الأبناء', 'الجدول', 'الواجبات', 'الإشعارات'],
      'teacher' => ['اليوم', 'الجدول', 'الحضور', 'الواجبات', 'الإشعارات'],
      _ => ['غير متاح'],
    };
    return Scaffold(
        appBar: AppBar(title: Text(school?.schoolName ?? 'مدرستي'), actions: [
          IconButton(
              onPressed: () => ref.read(sessionProvider.notifier).logout(),
              icon: const Icon(Icons.logout))
        ]),
        body: Column(children: [
          if (session.status == SessionStatus.historical)
            const HistoricalBanner(),
          Expanded(
              child: Center(
                  child: Text('${labels[selected]}\nواجهة تمهيدية',
                      textAlign: TextAlign.center,
                      style: Theme.of(context).textTheme.headlineSmall)))
        ]),
        bottomNavigationBar: NavigationBar(
            selectedIndex: selected.clamp(0, labels.length - 1),
            onDestinationSelected: (value) => setState(() => selected = value),
            destinations: labels
                .map((label) => NavigationDestination(
                    icon: const Icon(Icons.circle_outlined), label: label))
                .toList()));
  }
}

class UnavailableScreen extends ConsumerWidget {
  const UnavailableScreen({super.key});
  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final session = ref.watch(sessionProvider);
    return Scaffold(
      body: Center(
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: Column(mainAxisSize: MainAxisSize.min, children: [
            const Icon(Icons.mobile_off, size: 64),
            const SizedBox(height: 16),
            Text(
              session.message ?? 'هذا الحساب المدرسي غير متاح حالياً',
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: 12),
            TextButton(
              onPressed: () => ref.read(sessionProvider.notifier).bootstrap(),
              child: const Text('إعادة المحاولة'),
            ),
            TextButton(
              onPressed: () => ref.read(sessionProvider.notifier).logout(),
              child: const Text('تسجيل الخروج'),
            ),
          ]),
        ),
      ),
    );
  }
}
