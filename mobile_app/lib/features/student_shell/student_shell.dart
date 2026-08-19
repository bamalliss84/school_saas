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
import '../student/homework/data/homework_local_data_source.dart';
import '../student/homework/data/homework_remote_data_source.dart';
import '../student/homework/data/homework_repository.dart';
import '../student/homework/presentation/homework_controller.dart';
import '../student/homework/presentation/homework_screens.dart';
import '../student/results/data/results_repository.dart';
import '../student/results/presentation/results_controller.dart';
import '../student/results/presentation/results_screens.dart';

final studentTimetableProvider = StateNotifierProvider.autoDispose
    .family<TimetableController, TimetableState, CacheScope>((ref, scope) {
  final controller = TimetableController(
      StudentTimetableRepository(
          ref.read(apiProvider).dio, ref.read(databaseProvider)),
      scope);
  Future<void>.microtask(controller.load);
  return controller;
});

final studentHomeworkProvider = StateNotifierProvider.autoDispose
    .family<HomeworkController, HomeworkState, CacheScope>((ref, scope) {
  final controller = HomeworkController(
    StudentHomeworkRepository(
      DioHomeworkRemoteDataSource(ref.read(apiProvider).dio),
      HomeworkLocalDataSource(ref.read(databaseProvider)),
    ),
    scope,
  );
  Future<void>.microtask(controller.load);
  return controller;
});

final studentResultsProvider = StateNotifierProvider.autoDispose
    .family<ResultsController, ResultsState, CacheScope>((ref, scope) {
  final controller = ResultsController(
    StudentResultsRepository(ref.read(apiProvider).dio, ref.read(databaseProvider)),
    scope,
  );
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
    final homework = ref.watch(studentHomeworkProvider(scope));
    final results = ref.watch(studentResultsProvider(scope));
    return Scaffold(
      body: SafeArea(
        child: Column(children: [
          StudentAppHeader(
              schoolName: session.context?.schoolName ?? 'مدرستي',
              studentName: session.user?.fullName,
              academicYear: session.context?.academicYearName),
          if (session.status == SessionStatus.historical)
            HistoricalContextBanner(context: session.context),
          if (session.offline) const OfflineCacheBanner(),
          if (selectedIndex == 0 && timetable is TimetableReady)
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
                      : selectedIndex == 1
                          ? _homeworkFeature(homework, session, scope)
                          : selectedIndex == 2
                              ? _resultsFeature(results, session, scope)
                              : Center(
                                  child: Padding(
                                  padding: const EdgeInsets.all(AppSpacing.x6),
                                  child: Text(
                                      '${labels[selectedIndex]}\nواجهة تمهيدية — ستكتمل في المرحلة المخصصة لها',
                                      textAlign: TextAlign.center),
                                ))),
        ]),
      ),
      bottomNavigationBar: SafeArea(
        top: false,
        child: StudentBottomNavigation(
            selectedIndex: selectedIndex,
            onSelected: (value) {
              if (value == 1) {
                ref.read(studentHomeworkProvider(scope).notifier).closeDetail();
              } else if (value == 2) {
                ref.read(studentResultsProvider(scope).notifier).close();
              }
              setState(() {
                selectedIndex = value;
                showTimetable = false;
              });
              Future<void>.microtask(() {
                if (value == 0) {
                  ref.read(studentTimetableProvider(scope).notifier).refresh();
                } else if (value == 1) {
                  ref.read(studentHomeworkProvider(scope).notifier).refresh();
                } else if (value == 2) {
                  ref.read(studentResultsProvider(scope).notifier).refresh();
                }
              });
            }),
      ),
    );
  }

  Widget _resultsFeature(
      ResultsState state, AppSession session, CacheScope scope) {
    if (state is ResultsLoading) return const AppSkeletonCard();
    if (state is ResultsFailure) return AppErrorState(message: state.message);
    final ready = state as ResultsReady;
    final controller = ref.read(studentResultsProvider(scope).notifier);
    if (ready.selected != null) {
      return ResultDetailScreen(
        result: ready.selected!,
        historical: session.status == SessionStatus.historical,
        onBack: controller.close,
      );
    }
    return StudentResultsScreen(
      state: ready,
      historical: session.status == SessionStatus.historical,
      onTerm: controller.selectTerm,
      onSubject: controller.selectSubject,
      onExamType: controller.selectExamType,
      onOpen: controller.open,
      onRefresh: controller.refresh,
    );
  }

  Widget _homeworkFeature(
      HomeworkState state, AppSession session, CacheScope scope) {
    if (state is HomeworkLoading) return const AppSkeletonCard();
    if (state is HomeworkFailure) {
      return AppErrorState(message: state.message);
    }
    final ready = state as HomeworkReady;
    final controller = ref.read(studentHomeworkProvider(scope).notifier);
    final detail = ready.detail;
    if (detail is HomeworkDetailLoading) return const AppSkeletonCard();
    if (detail is HomeworkDetailFailure) {
      return Column(children: [
        Expanded(child: AppErrorState(message: detail.message)),
        TextButton(
            onPressed: controller.closeDetail,
            child: const Text('العودة إلى الواجبات')),
      ]);
    }
    if (detail is HomeworkDetailReady) {
      return Column(children: [
        Expanded(
          child: StudentHomeworkDetailScreen(
            data: detail.data,
            historical: session.status == SessionStatus.historical,
            submitting: detail.submitting,
            onBack: controller.closeDetail,
            onSave: controller.saveDraft,
            onSubmit: controller.submit,
            onUploadAttachments: controller.uploadAttachments,
            onDeleteAttachment: controller.deleteAttachment,
            onDownload: controller.download,
          ),
        ),
      ]);
    }
    return Column(children: [
      Padding(
        padding: const EdgeInsets.symmetric(horizontal: AppSpacing.x4),
        child: Align(
          alignment: AlignmentDirectional.centerStart,
          child: LastUpdatedLabel(value: ready.list.lastUpdated.toLocal()),
        ),
      ),
      Expanded(
        child: StudentHomeworkListScreen(
          state: ready,
          onFilter: controller.selectFilter,
          onOpen: controller.open,
          onRefresh: controller.refresh,
        ),
      ),
    ]);
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
        const SizedBox(height: AppSpacing.x6),
        TextButton.icon(
          onPressed: () => ref.read(sessionProvider.notifier).logout(),
          icon: const Icon(Icons.logout),
          label: const Text('تسجيل الخروج'),
        ),
      ],
    );
  }
}
