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
import '../student/attendance/data/attendance_repository.dart';
import '../student/attendance/presentation/attendance_controller.dart';
import '../student/attendance/presentation/attendance_screens.dart';
import '../student/homework/data/homework_local_data_source.dart';
import '../student/homework/data/homework_remote_data_source.dart';
import '../student/homework/data/homework_repository.dart';
import '../student/homework/presentation/homework_controller.dart';
import '../student/homework/presentation/homework_screens.dart';
import '../student/results/data/results_repository.dart';
import '../student/results/presentation/results_controller.dart';
import '../student/results/presentation/results_screens.dart';
import '../student/communications/data/communications_repository.dart';
import '../student/communications/domain/communication_models.dart';
import '../student/communications/presentation/communications_controller.dart';
import '../student/communications/presentation/communications_screens.dart';
import '../student/student_profile_controller.dart';
import '../student/student_profile_repository.dart';
import '../student/student_profile_screens.dart';

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
    StudentResultsRepository(
        ref.read(apiProvider).dio, ref.read(databaseProvider)),
    scope,
  );
  Future<void>.microtask(controller.load);
  return controller;
});

final studentAttendanceProvider = StateNotifierProvider.autoDispose
    .family<AttendanceController, AttendanceState, CacheScope>((ref, scope) {
  final controller = AttendanceController(
    StudentAttendanceRepository(
        ref.read(apiProvider).dio, ref.read(databaseProvider)),
    scope,
  );
  Future<void>.microtask(controller.load);
  return controller;
});

final studentCommunicationsProvider = StateNotifierProvider.autoDispose
    .family<CommunicationsController, CommunicationsState, CacheScope>(
        (ref, scope) {
  final controller = CommunicationsController(
    StudentCommunicationsRepository(
        ref.read(apiProvider).dio, ref.read(databaseProvider)),
    scope,
  );
  Future<void>.microtask(controller.load);
  return controller;
});

final studentProfileProvider = StateNotifierProvider.autoDispose
    .family<StudentProfileController, StudentProfileState, CacheScope>(
        (ref, scope) {
  final controller = StudentProfileController(
    StudentProfileRepository(
        ref.read(apiProvider).dio, ref.read(databaseProvider)),
    scope,
  );
  Future<void>.microtask(controller.load);
  return controller;
});

enum _MoreDestination { profile, context, history, appearance, help, about }

class StudentBottomNavigation extends StatelessWidget {
  const StudentBottomNavigation(
      {super.key,
      required this.selectedIndex,
      required this.onSelected,
      this.messageCount = 0});
  final int selectedIndex;
  final ValueChanged<int> onSelected;
  final int messageCount;
  @override
  Widget build(BuildContext context) => NavigationBar(
        selectedIndex: selectedIndex,
        onDestinationSelected: onSelected,
        destinations: [
          const NavigationDestination(
              icon: Icon(Icons.home_outlined), label: 'الرئيسية'),
          const NavigationDestination(
              icon: Icon(Icons.assignment_outlined), label: 'الواجبات'),
          const NavigationDestination(
              icon: Icon(Icons.bar_chart_outlined), label: 'النتائج'),
          NavigationDestination(
              icon: Badge(
                isLabelVisible: messageCount > 0,
                label: Text(messageCount > 99 ? '99+' : '$messageCount'),
                child: const Icon(Icons.chat_bubble_outline),
              ),
              label: 'الرسائل'),
          const NavigationDestination(
              icon: Icon(Icons.more_horiz), label: 'المزيد'),
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
  bool showAttendance = false;
  bool showCommunicationsCenter = false;
  _MoreDestination? moreDestination;

  @override
  void initState() {
    super.initState();
    ref.listenManual<bool>(
      sessionProvider.select((session) => session.offline),
      (previous, offline) {
        if (previous == true && !offline) {
          final session = ref.read(sessionProvider);
          final context = session.context;
          final user = session.user;
          if (context == null || user == null) return;
          final scope = CacheScope(
            localUserKey: 'user:${user.id}',
            membershipId: context.membershipId,
            academicYearKey: context.academicYearId?.toString() ??
                context.academicYearName ??
                '',
          );
          Future<void>.microtask(() => ref
              .read(studentCommunicationsProvider(scope).notifier)
              .refresh());
        }
      },
    );
  }

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
    final communications = ref.watch(studentCommunicationsProvider(scope));
    final profile =
        selectedIndex == 4 ? ref.watch(studentProfileProvider(scope)) : null;
    final attendance =
        showAttendance ? ref.watch(studentAttendanceProvider(scope)) : null;
    return PopScope(
        canPop: !(selectedIndex == 4 && moreDestination != null),
        onPopInvokedWithResult: (didPop, result) {
          if (!didPop && selectedIndex == 4 && moreDestination != null) {
            setState(() => moreDestination = null);
          }
        },
        child: Scaffold(
          body: SafeArea(
            child: Column(children: [
              StudentAppHeader(
                  schoolName: session.context?.schoolName ?? 'مدرستي',
                  studentName: session.user?.fullName,
                  academicYear: session.context?.academicYearName,
                  notificationCount: communications is CommunicationsReady
                      ? communications.data.badges.notifications
                      : 0,
                  onNotifications: () =>
                      setState(() => showCommunicationsCenter = true)),
              if (session.status == SessionStatus.historical)
                HistoricalContextBanner(context: session.context),
              if (session.offline) const OfflineCacheBanner(),
              if (selectedIndex == 0 && timetable is TimetableReady)
                Padding(
                  padding:
                      const EdgeInsets.symmetric(horizontal: AppSpacing.x4),
                  child: Align(
                      alignment: AlignmentDirectional.centerStart,
                      child: LastUpdatedLabel(
                          value: timetable.data.lastUpdated.toLocal())),
                ),
              Expanded(
                  child: showCommunicationsCenter
                      ? _communicationsCenter(communications, session, scope)
                      : selectedIndex == 4
                          ? _moreFeature(profile!, session, scope)
                          : selectedIndex == 0
                              ? _studentFeature(
                                  timetable, attendance, session, scope)
                              : selectedIndex == 1
                                  ? _homeworkFeature(homework, session, scope)
                                  : selectedIndex == 2
                                      ? _resultsFeature(results, session, scope)
                                      : _messagesFeature(
                                          communications, session, scope)),
            ]),
          ),
          bottomNavigationBar: SafeArea(
            top: false,
            child: StudentBottomNavigation(
                selectedIndex: selectedIndex,
                messageCount: communications is CommunicationsReady
                    ? communications.data.badges.conversations
                    : 0,
                onSelected: (value) {
                  if (value == 1) {
                    ref
                        .read(studentHomeworkProvider(scope).notifier)
                        .closeDetail();
                  } else if (value == 2) {
                    ref.read(studentResultsProvider(scope).notifier).close();
                  }
                  setState(() {
                    selectedIndex = value;
                    showTimetable = false;
                    showAttendance = false;
                    showCommunicationsCenter = false;
                    moreDestination = null;
                  });
                  Future<void>.microtask(() {
                    if (value == 0) {
                      ref
                          .read(studentTimetableProvider(scope).notifier)
                          .refresh();
                    } else if (value == 1) {
                      ref
                          .read(studentHomeworkProvider(scope).notifier)
                          .refresh();
                    } else if (value == 2) {
                      ref
                          .read(studentResultsProvider(scope).notifier)
                          .refresh();
                    } else if (value == 3) {
                      ref
                          .read(studentCommunicationsProvider(scope).notifier)
                          .refresh();
                    }
                  });
                }),
          ),
        ));
  }

  Widget _moreFeature(
      StudentProfileState profile, AppSession session, CacheScope scope) {
    void back() => setState(() => moreDestination = null);
    final destination = moreDestination;
    if (destination == _MoreDestination.profile) {
      return StudentProfileScreen(
        state: profile,
        contextInfo: session.context!,
        onBack: back,
        onRetry: ref.read(studentProfileProvider(scope).notifier).refresh,
      );
    }
    if (destination == _MoreDestination.context) {
      return StudentContextScreen(
        current: session.context!,
        contexts: session.contexts,
        offline: session.offline,
        onBack: back,
        onSelect: (item) async {
          await ref.read(sessionProvider.notifier).selectContext(item);
          if (mounted) setState(() => moreDestination = null);
        },
      );
    }
    if (destination == _MoreDestination.history) {
      return StudentAcademicHistoryScreen(
        state: profile,
        onBack: back,
        onRetry: ref.read(studentProfileProvider(scope).notifier).refresh,
      );
    }
    if (destination == _MoreDestination.appearance) {
      return AppearanceSettings(onBack: back);
    }
    if (destination == _MoreDestination.help) {
      return StudentHelpScreen(
        onBack: back,
        onSupport: () => setState(() {
          selectedIndex = 3;
          moreDestination = null;
        }),
      );
    }
    if (destination == _MoreDestination.about) {
      return StudentAboutScreen(onBack: back);
    }
    return StudentMoreScreen(
      studentName: session.user?.fullName ?? '',
      schoolName: session.context?.schoolName ?? '',
      canChangeContext: session.contexts.length > 1,
      onProfile: () =>
          setState(() => moreDestination = _MoreDestination.profile),
      onContext: () =>
          setState(() => moreDestination = _MoreDestination.context),
      onHistory: () =>
          setState(() => moreDestination = _MoreDestination.history),
      onAppearance: () =>
          setState(() => moreDestination = _MoreDestination.appearance),
      onHelp: () => setState(() => moreDestination = _MoreDestination.help),
      onAbout: () => setState(() => moreDestination = _MoreDestination.about),
      onLogout: () => ref.read(sessionProvider.notifier).logout(),
    );
  }

  Future<void> _openNotification(
      CommunicationNotification item, CacheScope scope) async {
    final communications =
        ref.read(studentCommunicationsProvider(scope).notifier);
    final navigator = Navigator.of(context);
    final messenger = ScaffoldMessenger.of(context);
    final historical =
        ref.read(sessionProvider).status == SessionStatus.historical;
    if (!item.isRead && !historical) {
      try {
        await communications.readNotification(item.id);
      } catch (_) {}
    }
    final action = item.action;
    final route = action?['route']?.toString();
    final params = action?['params'] is Map
        ? Map<String, dynamic>.from(action!['params'] as Map)
        : const <String, dynamic>{};
    if (!mounted) return;
    if (route == null || route.isEmpty) {
      messenger.showSnackBar(
          const SnackBar(content: Text('لا توجد تفاصيل إضافية لهذا الإشعار.')));
      return;
    }
    if (route == 'homework_detail') {
      final id = (params['homework_id'] as num?)?.toInt();
      if (id != null) {
        setState(() {
          selectedIndex = 1;
          showCommunicationsCenter = false;
        });
        await ref.read(studentHomeworkProvider(scope).notifier).open(id);
      }
      return;
    }
    if (route == 'homework_submission') {
      setState(() {
        selectedIndex = 1;
        showCommunicationsCenter = false;
      });
      messenger.showSnackBar(
          const SnackBar(content: Text('افتح الواجب لمراجعة حالة التسليم.')));
      return;
    }
    if (route == 'result_detail') {
      final id = (params['result_id'] as num?)?.toInt();
      final state = ref.read(studentResultsProvider(scope));
      if (id != null && state is ResultsReady) {
        final matches = state.data.items.where((e) => e.id == id);
        if (matches.isNotEmpty) {
          setState(() {
            selectedIndex = 2;
            showCommunicationsCenter = false;
          });
          ref.read(studentResultsProvider(scope).notifier).open(matches.first);
        }
      }
      return;
    }
    if (route == 'announcement_detail') {
      final id = (params['announcement_id'] as num?)?.toInt();
      final state = ref.read(studentCommunicationsProvider(scope));
      if (id != null && state is CommunicationsReady) {
        final matches = state.data.announcements.where((e) => e.id == id);
        if (matches.isNotEmpty) {
          final announcement = matches.first;
          if (!announcement.isRead && !historical) {
            try {
              await communications.readAnnouncement(announcement.id);
            } catch (_) {}
          }
          if (!mounted) return;
          await navigator.push(MaterialPageRoute<void>(
            builder: (_) => Scaffold(
              body: SafeArea(
                child: StudentAnnouncementDetailScreen(
                  item: announcement,
                  historical: historical,
                  onBack: () => navigator.pop(),
                  onInquire: announcement.canInquire && !historical
                      ? () async {
                          await communications.inquire(announcement.id);
                          if (navigator.canPop()) navigator.pop();
                        }
                      : null,
                ),
              ),
            ),
          ));
          return;
        }
      }
      messenger.showSnackBar(
          const SnackBar(content: Text('تعذر فتح تفاصيل الإعلان.')));
      return;
    }
    if (route == 'conversation_detail' || route == 'school_support_detail') {
      final id = (params['conversation_id'] as num?)?.toInt();
      final state = ref.read(studentCommunicationsProvider(scope));
      if (id != null && state is CommunicationsReady) {
        final matches = state.data.conversations.where((e) => e.id == id);
        if (matches.isNotEmpty) {
          setState(() {
            selectedIndex = 3;
            showCommunicationsCenter = false;
          });
          await communications.openConversation(matches.first);
        }
      }
      return;
    }
    if (route == 'school_home') {
      setState(() {
        selectedIndex = 0;
        showCommunicationsCenter = false;
      });
      return;
    }
    if (route == 'conversation_start') {
      setState(() {
        selectedIndex = 3;
        showCommunicationsCenter = false;
      });
      messenger.showSnackBar(
          const SnackBar(content: Text('اختر محادثة متاحة لبدء التواصل.')));
      return;
    }
    messenger.showSnackBar(
        const SnackBar(content: Text('هذا الإشعار لا يحتوي على وجهة مدعومة.')));
  }

  Widget _communicationsCenter(
      CommunicationsState state, AppSession session, CacheScope scope) {
    if (state is CommunicationsLoading) return const AppSkeletonCard();
    if (state is CommunicationsFailure) {
      return AppErrorState(message: state.message);
    }
    final ready = state as CommunicationsReady;
    final controller = ref.read(studentCommunicationsProvider(scope).notifier);
    return StudentCommunicationsCenter(
      data: ready.data,
      historical: session.status == SessionStatus.historical,
      onBack: () => setState(() => showCommunicationsCenter = false),
      onOpenNotification: (item) => _openNotification(item, scope),
      onReadAll: controller.readAll,
      onReadAnnouncement: controller.readAnnouncement,
      onInquireAnnouncement: (announcement) async {
        final id = await controller.inquire(announcement.id);
        final current = ref.read(studentCommunicationsProvider(scope));
        if (current is CommunicationsReady) {
          final matches =
              current.data.conversations.where((item) => item.id == id);
          if (matches.isNotEmpty) {
            setState(() {
              selectedIndex = 3;
              showCommunicationsCenter = false;
            });
            await controller.openConversation(matches.first);
          }
        }
      },
    );
  }

  Widget _messagesFeature(
      CommunicationsState state, AppSession session, CacheScope scope) {
    if (state is CommunicationsLoading) return const AppSkeletonCard();
    if (state is CommunicationsFailure) {
      return AppErrorState(message: state.message);
    }
    final ready = state as CommunicationsReady;
    final controller = ref.read(studentCommunicationsProvider(scope).notifier);
    if (ready.selectedConversation != null) {
      return ConversationDetailScreen(
        conversation: ready.selectedConversation!,
        messages: ready.messages,
        historical: session.status == SessionStatus.historical,
        offline: ready.data.offline || session.offline,
        loading: ready.busy,
        error: ready.detailError,
        onBack: controller.closeConversation,
        onSend: controller.send,
      );
    }
    return StudentConversationsScreen(
      items: ready.data.conversations,
      offline: ready.data.offline || session.offline,
      historical: session.status == SessionStatus.historical,
      onOpen: controller.openConversation,
      onCreateSupport: controller.createSupport,
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

  Widget _studentFeature(TimetableState state, AttendanceState? attendance,
      AppSession session, CacheScope scope) {
    if (showAttendance) {
      final controller = ref.read(studentAttendanceProvider(scope).notifier);
      if (attendance == null || attendance is AttendanceLoading) {
        return const StudentAttendanceLoadingView();
      }
      if (attendance is AttendanceOfflineEmpty) {
        return StudentAttendanceOfflineEmptyView(
          onRetry: controller.refresh,
          onBack: () => setState(() => showAttendance = false),
        );
      }
      if (attendance is AttendanceFailure) {
        return StudentAttendanceErrorView(
          message: attendance.message,
          onRetry: controller.refresh,
          onBack: () => setState(() => showAttendance = false),
        );
      }
      final attendanceReady = attendance as AttendanceReady;
      if (attendanceReady.selected != null) {
        return StudentAttendanceDetailScreen(
          record: attendanceReady.selected!,
          historical: session.status == SessionStatus.historical,
          onBack: controller.close,
        );
      }
      return StudentAttendanceScreen(
        state: attendanceReady,
        historical: session.status == SessionStatus.historical,
        onFilter: controller.selectFilter,
        onOpen: controller.open,
        onRefresh: controller.refresh,
        onBack: () => setState(() => showAttendance = false),
      );
    }
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
      onOpenAttendance: () => setState(() => showAttendance = true),
      onRefresh: () =>
          ref.read(studentTimetableProvider(scope).notifier).refresh(),
    );
  }
}

class AppearanceSettings extends ConsumerWidget {
  const AppearanceSettings({super.key, this.onBack});
  final VoidCallback? onBack;
  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final selected = ref.watch(fontProvider);
    return ListView(
      padding: const EdgeInsets.all(AppSpacing.x4),
      children: [
        Row(children: [
          if (onBack != null)
            IconButton(
                onPressed: onBack, icon: const Icon(Icons.arrow_forward)),
          Expanded(
              child: Text('إعدادات المظهر',
                  style: Theme.of(context).textTheme.headlineMedium)),
        ]),
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
