import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../app/app.dart';
import '../../app/session/app_session.dart';
import '../../core/design_system/components.dart';
import '../../core/local_database/app_database.dart';
import '../../core/models/school_context.dart';
import '../teacher/profile/teacher_profile.dart';
import '../teacher/students/presentation/teacher_students_screen.dart';
import '../teacher/exams/presentation/teacher_exam_screen.dart';
import '../teacher/timetable/presentation/teacher_timetable_controller.dart';
import '../teacher/timetable/presentation/teacher_timetable_screen.dart';
import 'teacher_context.dart';
import 'teacher_home.dart';
import 'teacher_more.dart';

final teacherProfileProvider = FutureProvider.autoDispose
    .family<TeacherProfile, int>((ref, membershipId) =>
        TeacherProfileRepository(ref.read(apiProvider).dio).getProfile());

enum _TeacherDestination { context, profile, history, settings, help, about }

class TeacherShell extends ConsumerStatefulWidget {
  const TeacherShell({super.key});

  @override
  ConsumerState<TeacherShell> createState() => _TeacherShellState();
}

class _TeacherShellState extends ConsumerState<TeacherShell> {
  int selectedIndex = 0;
  _TeacherDestination? destination;
  bool attendanceDirty = false;

  Future<void> _selectTab(int index) async {
    if (index == selectedIndex) return;
    if (selectedIndex == 2 && attendanceDirty) {
      final discard = await showDialog<bool>(
        context: context,
        builder: (context) => AlertDialog(
          title: const Text('لديك تغييرات غير محفوظة'),
          content: const Text('هل تريد تجاهل مسودة الحضور؟'),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(context, false),
              child: const Text('متابعة التعديل'),
            ),
            FilledButton(
              onPressed: () => Navigator.pop(context, true),
              child: const Text('تجاهل التغييرات'),
            ),
          ],
        ),
      );
      if (discard != true || !mounted) return;
    }
    setState(() {
      selectedIndex = index;
      destination = null;
      attendanceDirty = false;
    });
  }

  void _open(_TeacherDestination value) => setState(() => destination = value);

  void _later(String label) => ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('$label ستتوفر في مرحلة لاحقة.')),
      );

  @override
  Widget build(BuildContext context) {
    final session = ref.watch(sessionProvider);
    final contextInfo = session.context;
    if (contextInfo == null || contextInfo.role != 'teacher') {
      return const SizedBox.shrink();
    }
    final profile = ref.watch(teacherProfileProvider(contextInfo.membershipId));
    final user = session.user;
    if (user == null) return const SizedBox.shrink();
    final timetableScope = CacheScope(
      localUserKey: 'user:${user.id}',
      membershipId: contextInfo.membershipId,
      academicYearKey: contextInfo.academicYearId?.toString() ??
          contextInfo.academicYearName ??
          '',
    );
    final timetable = ref.watch(teacherTimetableProvider(timetableScope));
    return Scaffold(
      body: SafeArea(
        child: Column(children: [
          if (session.offline) ...[
            const SizedBox(height: 8),
            const OfflineCacheBanner(),
          ],
          if (session.status == SessionStatus.historical)
            TeacherHistoricalBanner(contextInfo: contextInfo),
          Expanded(
            child: _page(
              session,
              contextInfo,
              profile,
              timetableScope,
              timetable,
            ),
          ),
        ]),
      ),
      bottomNavigationBar: NavigationBar(
        selectedIndex: selectedIndex,
        onDestinationSelected: (index) => _selectTab(index),
        destinations: const [
          NavigationDestination(
              icon: Icon(Icons.home_outlined),
              selectedIcon: Icon(Icons.home),
              label: 'الرئيسية'),
          NavigationDestination(
              icon: Icon(Icons.calendar_month_outlined),
              selectedIcon: Icon(Icons.calendar_month),
              label: 'جدولي'),
          NavigationDestination(
              icon: Icon(Icons.groups_outlined),
              selectedIcon: Icon(Icons.groups),
              label: 'الطلاب والحضور'),
          NavigationDestination(
              icon: Icon(Icons.assignment_outlined),
              selectedIcon: Icon(Icons.assignment),
              label: 'المهام والتقييم'),
          NavigationDestination(icon: Icon(Icons.more_horiz), label: 'المزيد'),
        ],
      ),
    );
  }

  Widget _page(
    AppSession session,
    SchoolContext contextInfo,
    AsyncValue<TeacherProfile> profile,
    CacheScope timetableScope,
    TeacherTimetableState timetable,
  ) {
    if (destination != null) {
      return switch (destination!) {
        _TeacherDestination.context => TeacherContextScreen(
            current: contextInfo,
            contexts: session.contexts,
            offline: session.offline,
            historicalOnly: false,
            onBack: () => setState(() => destination = null),
            onSelect: ref.read(sessionProvider.notifier).selectContext,
          ),
        _TeacherDestination.history => TeacherContextScreen(
            current: contextInfo,
            contexts: session.contexts,
            offline: session.offline,
            historicalOnly: true,
            onBack: () => setState(() => destination = null),
            onSelect: ref.read(sessionProvider.notifier).selectContext,
          ),
        _TeacherDestination.profile => TeacherProfileScreen(
            state: profile,
            contextInfo: contextInfo,
            onBack: () => setState(() => destination = null),
            onRetry: () => ref
                .invalidate(teacherProfileProvider(contextInfo.membershipId)),
          ),
        _TeacherDestination.settings => TeacherSettingsScreen(
            onBack: () => setState(() => destination = null)),
        _TeacherDestination.help => TeacherInformationScreen(
            title: 'المساعدة',
            message: 'للمساعدة، تواصل مع إدارة مدرستك.',
            icon: Icons.help_outline,
            onBack: () => setState(() => destination = null),
          ),
        _TeacherDestination.about => TeacherInformationScreen(
            title: 'حول التطبيق',
            message: 'مدرستي — تطبيق المعلم',
            icon: Icons.info_outline,
            onBack: () => setState(() => destination = null),
          ),
      };
    }
    return switch (selectedIndex) {
      0 => TeacherHomeFoundation(
          session: session,
          profile: profile.asData?.value,
          timetable: timetable,
          onContext: () => _open(_TeacherDestination.context),
          onProfile: () => _open(_TeacherDestination.profile),
        ),
      1 => TeacherTimetableScreen(
          state: timetable,
          historical: session.status == SessionStatus.historical,
          onRefresh: ref
              .read(teacherTimetableProvider(timetableScope).notifier)
              .refresh,
        ),
      2 => TeacherStudentsScreen(
          scope: timetableScope,
          historical: !session.canWrite,
          onDirtyChanged: (value) {
            if (attendanceDirty != value) {
              setState(() => attendanceDirty = value);
            }
          },
        ),
      3 => TeacherWorkCenterScreen(
          scope: timetableScope,
          historical: !session.canWrite,
        ),
      _ => TeacherMoreScreen(
          session: session,
          profile: profile,
          onContext: () => _open(_TeacherDestination.context),
          onProfile: () => _open(_TeacherDestination.profile),
          onHistory: () => _open(_TeacherDestination.history),
          onSettings: () => _open(_TeacherDestination.settings),
          onHelp: () => _open(_TeacherDestination.help),
          onAbout: () => _open(_TeacherDestination.about),
          onNotifications: () => _later('الإشعارات'),
          onAnnouncements: () => _later('الإعلانات'),
          onLogout: ref.read(sessionProvider.notifier).logout,
        ),
    };
  }
}
