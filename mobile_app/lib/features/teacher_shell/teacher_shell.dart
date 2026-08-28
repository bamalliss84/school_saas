import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../app/app.dart';
import '../../app/session/app_session.dart';
import '../../core/design_system/components.dart';
import '../../core/models/school_context.dart';
import '../teacher/profile/teacher_profile.dart';
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

  void _selectTab(int index) => setState(() {
        selectedIndex = index;
        destination = null;
      });

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
    final profile =
        ref.watch(teacherProfileProvider(contextInfo.membershipId));
    return Scaffold(
      body: SafeArea(
        child: Column(children: [
          if (session.offline) ...[
            const SizedBox(height: 8),
            const OfflineCacheBanner(),
          ],
          if (session.status == SessionStatus.historical)
            TeacherHistoricalBanner(contextInfo: contextInfo),
          Expanded(child: _page(session, contextInfo, profile)),
        ]),
      ),
      bottomNavigationBar: NavigationBar(
        selectedIndex: selectedIndex,
        onDestinationSelected: _selectTab,
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

  Widget _page(AppSession session, SchoolContext contextInfo,
      AsyncValue<TeacherProfile> profile) {
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
            onRetry: () => ref.invalidate(
                teacherProfileProvider(contextInfo.membershipId)),
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
          onContext: () => _open(_TeacherDestination.context),
          onSchedule: () => _selectTab(1),
          onAttendance: session.canWrite ? () => _selectTab(2) : null,
          onTasks: session.canWrite ? () => _selectTab(3) : null,
        ),
      1 => const TeacherFutureFeature(
          title: 'جدولي',
          message: 'سيظهر جدولك الدراسي هنا',
          detail: 'سترتب حصص اليوم والأسبوع في هذه الصفحة.',
          icon: Icons.calendar_month_outlined),
      2 => const TeacherFutureFeature(
          title: 'الطلاب والحضور',
          message: 'طلاب حصصك وحضورهم سيظهرون هنا',
          detail: 'ستتمكن من عرض الطلاب وتسجيل الحضور في مرحلة لاحقة.',
          icon: Icons.groups_outlined),
      3 => const TeacherFutureFeature(
          title: 'المهام والتقييم',
          message: 'ستظهر المهام والتقييمات هنا',
          detail: 'الواجبات والتسليمات والنتائج ستتوفر في المراحل القادمة.',
          icon: Icons.assignment_outlined),
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
