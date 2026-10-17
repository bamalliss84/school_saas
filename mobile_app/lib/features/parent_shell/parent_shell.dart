import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../app/app.dart';
import '../../app/session/app_session.dart';
import '../../core/design_system/role_visual_tokens.dart';
import '../../core/local_database/app_database.dart';
import '../../core/models/school_context.dart';
import '../parent/domain/parent_models.dart';
import '../parent/presentation/parent_controller.dart';
import '../parent/presentation/parent_communications_screens.dart';
import '../parent/presentation/parent_home.dart';
import '../parent/presentation/parent_homework_controller.dart';
import '../parent/presentation/parent_homework_screens.dart';
import '../parent/presentation/parent_m2_controller.dart';
import '../parent/presentation/parent_m2_screens.dart';
import '../parent/presentation/parent_results_controller.dart';
import '../parent/presentation/parent_results_screens.dart';

class ParentShell extends ConsumerStatefulWidget {
  const ParentShell({super.key});

  @override
  ConsumerState<ParentShell> createState() => _ParentShellState();
}

class _ParentShellState extends ConsumerState<ParentShell> {
  int selectedIndex = 0;

  @override
  void initState() {
    super.initState();
    ref.listenManual<bool>(
      sessionProvider.select((session) => session.offline),
      (previous, offline) {
        if (previous == true && !offline) {
          final session = ref.read(sessionProvider);
          final scope = _scope(session);
          if (scope != null) {
            Future<void>.microtask(
              ref.read(parentFoundationProvider(scope).notifier).refresh,
            );
          }
        }
      },
    );
  }

  @override
  Widget build(BuildContext context) {
    final session = ref.watch(sessionProvider);
    final contextInfo = session.context;
    final scope = _scope(session);
    if (contextInfo == null || contextInfo.role != 'parent' || scope == null) {
      return const SizedBox.shrink();
    }
    final state = ref.watch(parentFoundationProvider(scope));
    final selectedChild =
        state is ParentReady ? state.data.selectedChild : null;
    final query = selectedChild == null
        ? null
        : (scope: scope, childId: selectedChild.id);
    final selectedEnrollment = state is ParentReady
        ? _enrollmentForScope(state.data.selectedHistory, scope)
        : null;
    final resultsQuery = selectedChild == null || selectedEnrollment == null
        ? null
        : (
            scope: scope,
            childId: selectedChild.id,
            enrollmentId: selectedEnrollment.id,
          );
    return Scaffold(
      key: const Key('parent-shell'),
      body: SafeArea(
        child: switch (selectedIndex) {
          0 => ParentHome(
              state: state,
              contextInfo: contextInfo,
              onSelectChild: (id) => ref
                  .read(parentFoundationProvider(scope).notifier)
                  .selectChild(id),
              onRefresh:
                  ref.read(parentFoundationProvider(scope).notifier).refresh,
            ),
          1 => query == null
              ? const _ParentFeatureUnavailable()
              : ParentTimetableScreen(
                  state: ref.watch(parentTimetableProvider(query)),
                  childName: selectedChild!.fullName,
                  historical: contextInfo.isHistorical,
                  onRefresh:
                      ref.read(parentTimetableProvider(query).notifier).refresh,
                ),
          2 => query == null
              ? const _ParentFeatureUnavailable()
              : ParentAttendanceScreen(
                  state: ref.watch(parentAttendanceProvider(query)),
                  childName: selectedChild!.fullName,
                  historical: contextInfo.isHistorical,
                  onRefresh: ref
                      .read(parentAttendanceProvider(query).notifier)
                      .refresh,
                ),
          3 => query == null
              ? const _ParentFeatureUnavailable()
              : ParentHomeworkListScreen(
                  state: ref.watch(parentHomeworkProvider(query)),
                  childName: selectedChild!.fullName,
                  historical: contextInfo.isHistorical,
                  onRefresh:
                      ref.read(parentHomeworkProvider(query).notifier).refresh,
                  onOpen: (homework) => Navigator.of(context).push(
                    MaterialPageRoute<void>(
                      builder: (_) => ParentHomeworkDetailPage(
                        scope: scope,
                        childId: selectedChild.id,
                        childName: selectedChild.fullName,
                        homework: homework,
                        historical: contextInfo.isHistorical,
                      ),
                    ),
                  ),
                ),
          4 => resultsQuery == null
              ? const _ParentFeatureUnavailable()
              : ParentResultsScreen(
                  state: ref.watch(parentResultsProvider(resultsQuery)),
                  childName: selectedChild!.fullName,
                  historical: contextInfo.isHistorical,
                  onRefresh: ref
                      .read(parentResultsProvider(resultsQuery).notifier)
                      .refresh,
                  onOpen: (result) => Navigator.of(context).push(
                    MaterialPageRoute<void>(
                      builder: (_) => ParentResultDetailScreen(
                        result: result,
                        historical: contextInfo.isHistorical,
                      ),
                    ),
                  ),
                ),
          _ => ParentMore(
              session: session,
              onSelectContext: ref.read(sessionProvider.notifier).selectContext,
              onLogout: ref.read(sessionProvider.notifier).logout,
              onNotifications: () => Navigator.of(context).push(
                MaterialPageRoute<void>(
                  builder: (_) => ParentNotificationsPage(
                    scope: scope,
                    historical: contextInfo.isHistorical,
                  ),
                ),
              ),
              onAnnouncements: () => Navigator.of(context).push(
                MaterialPageRoute<void>(
                  builder: (_) => ParentAnnouncementsPage(
                    scope: scope,
                    historical: contextInfo.isHistorical,
                    childId: selectedChild?.id,
                  ),
                ),
              ),
              onMessages: () => Navigator.of(context).push(
                MaterialPageRoute<void>(
                  builder: (_) => ParentConversationsPage(
                    scope: scope,
                    historical: contextInfo.isHistorical,
                  ),
                ),
              ),
            ),
        },
      ),
      bottomNavigationBar: ParentBottomNavigation(
        selectedIndex: selectedIndex,
        onSelected: (value) => setState(() => selectedIndex = value),
      ),
    );
  }
}

class ParentBottomNavigation extends StatelessWidget {
  const ParentBottomNavigation({
    super.key,
    required this.selectedIndex,
    required this.onSelected,
  });
  final int selectedIndex;
  final ValueChanged<int> onSelected;

  @override
  Widget build(BuildContext context) => NavigationBar(
        selectedIndex: selectedIndex,
        onDestinationSelected: onSelected,
        destinations: const [
          NavigationDestination(
            icon: Icon(Icons.home_outlined),
            selectedIcon: Icon(Icons.home),
            label: 'الرئيسية',
          ),
          NavigationDestination(
            icon: Icon(Icons.calendar_month_outlined),
            selectedIcon: Icon(Icons.calendar_month),
            label: 'الجدول',
          ),
          NavigationDestination(
            icon: Icon(Icons.fact_check_outlined),
            selectedIcon: Icon(Icons.fact_check),
            label: 'الحضور',
          ),
          NavigationDestination(
            icon: Icon(Icons.assignment_outlined),
            selectedIcon: Icon(Icons.assignment),
            label: 'الواجبات',
          ),
          NavigationDestination(
            icon: Icon(Icons.assessment_outlined),
            selectedIcon: Icon(Icons.assessment),
            label: 'النتائج',
          ),
          NavigationDestination(
            icon: Icon(Icons.more_horiz),
            label: 'المزيد',
          ),
        ],
      );
}

class _ParentFeatureUnavailable extends StatelessWidget {
  const _ParentFeatureUnavailable();

  @override
  Widget build(BuildContext context) => const Center(
        child: Text('اختر ابنًا من الصفحة الرئيسية لعرض البيانات.'),
      );
}

CacheScope? _scope(AppSession session) {
  final user = session.user;
  final context = session.context;
  if (user == null || context == null) return null;
  return CacheScope(
    localUserKey: 'user:${user.id}',
    membershipId: context.membershipId,
    academicYearKey:
        context.academicYearId?.toString() ?? context.academicYearName ?? '',
  );
}

ParentEnrollment? _enrollmentForScope(
  List<ParentEnrollment> history,
  CacheScope scope,
) {
  final academicYearId = int.tryParse(scope.academicYearKey);
  for (final enrollment in history) {
    if (academicYearId != null &&
        enrollment.academicYear.id == academicYearId) {
      return enrollment;
    }
  }
  return history.length == 1 ? history.single : null;
}

class ParentMore extends StatefulWidget {
  const ParentMore({
    super.key,
    required this.session,
    required this.onSelectContext,
    required this.onLogout,
    this.onNotifications,
    this.onAnnouncements,
    this.onMessages,
  });

  final AppSession session;
  final Future<void> Function(SchoolContext context) onSelectContext;
  final Future<void> Function() onLogout;
  final VoidCallback? onNotifications;
  final VoidCallback? onAnnouncements;
  final VoidCallback? onMessages;

  @override
  State<ParentMore> createState() => _ParentMoreState();
}

class _ParentMoreState extends State<ParentMore> {
  int? switchingMembershipId;
  String? error;

  @override
  Widget build(BuildContext context) {
    final current = widget.session.context!;
    final parentContexts = widget.session.contexts
        .where((item) => item.role == 'parent')
        .toList(growable: false);
    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        Text('المزيد', style: Theme.of(context).textTheme.headlineSmall),
        const SizedBox(height: 16),
        Card(
          child: ListTile(
            leading: const CircleAvatar(
              backgroundColor: Color(0x147447c8),
              child:
                  Icon(Icons.family_restroom, color: RoleVisualTokens.parent),
            ),
            title: Text(current.schoolName),
            subtitle: Text([
              current.academicYearName ?? '—',
              current.isHistorical ? 'للقراءة فقط' : 'ولي أمر',
            ].join(' • ')),
          ),
        ),
        if (error != null) ...[
          const SizedBox(height: 8),
          Text(error!,
              style: TextStyle(color: Theme.of(context).colorScheme.error)),
        ],
        if (parentContexts.length > 1) ...[
          const SizedBox(height: 16),
          Text('المدرسة والسياق',
              style: Theme.of(context).textTheme.titleMedium),
          const SizedBox(height: 8),
          for (final item in parentContexts)
            Card(
              child: ListTile(
                leading: item.membershipId == current.membershipId
                    ? const Icon(Icons.check_circle, color: Colors.green)
                    : const Icon(Icons.school_outlined),
                title: Text(item.schoolName),
                subtitle: Text(item.isHistorical
                    ? 'سياق تاريخي — للقراءة فقط'
                    : item.academicYearName ?? 'سياق نشط'),
                trailing: switchingMembershipId == item.membershipId
                    ? const SizedBox.square(
                        dimension: 20,
                        child: CircularProgressIndicator(strokeWidth: 2),
                      )
                    : null,
                enabled:
                    !widget.session.offline && switchingMembershipId == null,
                onTap: item.membershipId == current.membershipId
                    ? null
                    : () => _select(item),
              ),
            ),
        ],
        if (widget.session.offline) ...[
          const SizedBox(height: 12),
          const Text(
            'لا يمكن تغيير المدرسة دون اتصال بالإنترنت.',
            textAlign: TextAlign.center,
          ),
        ],
        if (widget.onNotifications != null &&
            widget.onAnnouncements != null &&
            widget.onMessages != null) ...[
          const SizedBox(height: 16),
          ParentCommunicationLinks(
            onNotifications: widget.onNotifications!,
            onAnnouncements: widget.onAnnouncements!,
            onMessages: widget.onMessages!,
          ),
        ],
        const SizedBox(height: 24),
        OutlinedButton.icon(
          onPressed: widget.onLogout,
          icon: const Icon(Icons.logout),
          label: const Text('تسجيل الخروج'),
        ),
      ],
    );
  }

  Future<void> _select(SchoolContext contextInfo) async {
    setState(() {
      switchingMembershipId = contextInfo.membershipId;
      error = null;
    });
    try {
      await widget.onSelectContext(contextInfo);
    } catch (_) {
      if (mounted) {
        setState(() => error = 'تعذر تغيير السياق. ما زلت في السياق السابق.');
      }
    } finally {
      if (mounted) setState(() => switchingMembershipId = null);
    }
  }
}
