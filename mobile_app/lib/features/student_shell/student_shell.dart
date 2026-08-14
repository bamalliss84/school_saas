import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../app/app.dart';
import '../../app/session/app_session.dart';
import '../../core/design_system/components.dart';
import '../../core/design_system/tokens.dart';
import '../../core/local_database/app_database.dart';
import '../../core/preferences/font_preferences.dart';
import '../student/timetable/data/timetable_repository.dart';
import '../student/timetable/presentation/timetable_controller.dart';
import '../student/timetable/presentation/timetable_screens.dart';

final studentTimetableProvider = StateNotifierProvider.autoDispose
    .family<TimetableController, TimetableState, CacheScope>((ref, scope) {
  final controller = TimetableController(
      StudentTimetableRepository(
          ref.read(apiProvider).dio, ref.read(databaseProvider)),
      scope);
  Future<void>.microtask(controller.load);
  return controller;
});

class StudentBottomNavigation extends StatelessWidget {
  const StudentBottomNavigation(
      {super.key, required this.selectedIndex, required this.onSelected});
  final int selectedIndex;
  final ValueChanged<int> onSelected;
  @override
  Widget build(BuildContext context) => NavigationBar(
        selectedIndex: selectedIndex,
        onDestinationSelected: onSelected,
        destinations: const [
          NavigationDestination(
              icon: Icon(Icons.home_outlined), label: 'الرئيسية'),
          NavigationDestination(
              icon: Icon(Icons.assignment_outlined), label: 'الواجبات'),
          NavigationDestination(
              icon: Icon(Icons.bar_chart_outlined), label: 'النتائج'),
          NavigationDestination(
              icon: Icon(Icons.chat_bubble_outline), label: 'الرسائل'),
          NavigationDestination(icon: Icon(Icons.more_horiz), label: 'المزيد'),
        ],
      );
}

class StudentShell extends ConsumerStatefulWidget {
  const StudentShell({super.key});
  @override
  ConsumerState<StudentShell> createState() => _StudentShellState();
}

class _StudentShellState extends ConsumerState<StudentShell> {
  int selectedIndex = 0;
  bool showTimetable = false;
  static const labels = ['الرئيسية', 'الواجبات', 'النتائج', 'الرسائل'];

  @override
  Widget build(BuildContext context) {
    final session = ref.watch(sessionProvider);
    final scope = CacheScope(
      localUserKey: 'user:${session.user!.id}',
      membershipId: session.context!.membershipId,
      academicYearKey: session.context!.academicYearId?.toString() ??
          session.context!.academicYearName ??
          '',
    );
    final timetable = ref.watch(studentTimetableProvider(scope));
    return Scaffold(
      body: SafeArea(
        child: Column(children: [
          StudentAppHeader(
              schoolName: session.context?.schoolName ?? 'مدرستي',
              studentName: session.user?.fullName,
              academicYear: session.context?.academicYearName),
          if (session.status == SessionStatus.historical)
            HistoricalContextBanner(context: session.context),
          if (timetable is TimetableReady && timetable.offline)
            const OfflineCacheBanner(),
          if (timetable is TimetableReady)
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: AppSpacing.x4),
              child: Align(
                  alignment: AlignmentDirectional.centerStart,
                  child: LastUpdatedLabel(
                      value: timetable.data.lastUpdated.toLocal())),
            ),
          Expanded(
              child: selectedIndex == 4
                  ? const AppearanceSettings()
                  : selectedIndex == 0
                      ? _studentFeature(timetable, session, scope)
                      : Center(
                          child: Padding(
                          padding: const EdgeInsets.all(AppSpacing.x6),
                          child: Text(
                              '${labels[selectedIndex]}\nواجهة تمهيدية — لا توجد ميزة بيانات في Sprint 5B.0',
                              textAlign: TextAlign.center),
                        ))),
        ]),
      ),
      bottomNavigationBar: SafeArea(
        top: false,
        child: StudentBottomNavigation(
            selectedIndex: selectedIndex,
            onSelected: (value) => setState(() => selectedIndex = value)),
      ),
    );
  }

  Widget _studentFeature(
      TimetableState state, AppSession session, CacheScope scope) {
    if (state is TimetableLoading) return const AppSkeletonCard();
    if (state is TimetableFailure) return AppErrorState(message: state.message);
    final ready = state as TimetableReady;
    if (showTimetable) {
      return StudentTimetableScreen(
          data: ready.data,
          onRefresh: () =>
              ref.read(studentTimetableProvider(scope).notifier).refresh());
    }
    return StudentHomeScreen(
      data: ready.data,
      studentName: session.user?.fullName ?? '',
      schoolName: session.context?.schoolName ?? '',
      academicYear: session.context?.academicYearName ?? '',
      onOpenTimetable: () => setState(() => showTimetable = true),
      onRefresh: () =>
          ref.read(studentTimetableProvider(scope).notifier).refresh(),
    );
  }
}

class AppearanceSettings extends ConsumerWidget {
  const AppearanceSettings({super.key});
  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final selected = ref.watch(fontProvider);
    return ListView(
      padding: const EdgeInsets.all(AppSpacing.x4),
      children: [
        Text('إعدادات المظهر',
            style: Theme.of(context).textTheme.headlineMedium),
        const SizedBox(height: AppSpacing.x6),
        const Text('خط التطبيق'),
        const SizedBox(height: AppSpacing.x2),
        AppCard(
            child: Column(
                children: AppFont.values
                    .map((font) => RadioListTile<AppFont>(
                          value: font,
                          groupValue: selected,
                          title: Text(font.label),
                          onChanged: (value) {
                            if (value != null) {
                              ref.read(fontProvider.notifier).select(value);
                            }
                          },
                        ))
                    .toList())),
      ],
    );
  }
}
