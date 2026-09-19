import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../app/session/app_session.dart';
import '../../core/design_system/components.dart';
import '../../core/design_system/tokens.dart';
import '../../core/models/school_context.dart';
import '../../core/preferences/font_preferences.dart';
import '../teacher/profile/teacher_profile.dart';
import 'teacher_shared.dart';

class TeacherMoreScreen extends StatelessWidget {
  const TeacherMoreScreen({
    super.key,
    required this.session,
    required this.profile,
    required this.onContext,
    required this.onProfile,
    required this.onNotifications,
    required this.onAnnouncements,
    required this.onMessages,
    required this.onHistory,
    required this.onSettings,
    required this.onHelp,
    required this.onAbout,
    required this.onLogout,
  });

  final AppSession session;
  final AsyncValue<TeacherProfile> profile;
  final VoidCallback onContext;
  final VoidCallback onProfile;
  final VoidCallback onNotifications;
  final VoidCallback onAnnouncements;
  final VoidCallback onMessages;
  final VoidCallback onHistory;
  final VoidCallback onSettings;
  final VoidCallback onHelp;
  final VoidCallback onAbout;
  final VoidCallback onLogout;

  @override
  Widget build(BuildContext context) {
    final contextInfo = session.context!;
    final profileName = profile.asData?.value.fullName ?? '';
    return ListView(
      padding: const EdgeInsets.all(AppSpacing.x4),
      children: [
        Text('المزيد', style: Theme.of(context).textTheme.headlineMedium),
        const SizedBox(height: AppSpacing.x4),
        AppCard(
          child: ListTile(
            contentPadding: EdgeInsets.zero,
            leading: const CircleAvatar(child: Icon(Icons.person_outline)),
            title: Text(profileName.isNotEmpty
                ? profileName
                : session.user?.fullName ?? 'المعلم'),
            subtitle: Text(
              '${contextInfo.schoolName}\n${contextInfo.academicYearName ?? '—'} • معلم${contextInfo.isHistorical ? ' • للعرض فقط' : ''}',
            ),
            isThreeLine: true,
            trailing: profile.isLoading
                ? const SizedBox.square(
                    dimension: 20,
                    child: CircularProgressIndicator(strokeWidth: 2),
                  )
                : const Icon(Icons.chevron_left),
            onTap: onProfile,
          ),
        ),
        const SizedBox(height: AppSpacing.x3),
        _MoreGroup(children: [
          _MoreTile(
              icon: Icons.swap_horiz,
              label: 'تغيير المدرسة أو الدور',
              onTap: onContext),
          _MoreTile(
              icon: Icons.person_outline,
              label: 'الملف الشخصي',
              onTap: onProfile),
          _MoreTile(
              icon: Icons.notifications_none,
              label: 'الإشعارات',
              onTap: onNotifications),
          _MoreTile(
              icon: Icons.campaign_outlined,
              label: 'الإعلانات',
              onTap: onAnnouncements),
          _MoreTile(
              icon: Icons.chat_bubble_outline,
              label: 'الرسائل',
              onTap: onMessages),
          _MoreTile(
              icon: Icons.history_edu_outlined,
              label: 'السجل الدراسي السابق',
              onTap: onHistory),
        ]),
        const SizedBox(height: AppSpacing.x3),
        _MoreGroup(children: [
          _MoreTile(
              icon: Icons.settings_outlined,
              label: 'الإعدادات',
              onTap: onSettings),
          _MoreTile(
              icon: Icons.help_outline,
              label: 'المساعدة',
              onTap: onHelp),
          _MoreTile(
              icon: Icons.info_outline,
              label: 'حول التطبيق',
              onTap: onAbout),
        ]),
        const SizedBox(height: AppSpacing.x4),
        OutlinedButton.icon(
          onPressed: onLogout,
          icon: const Icon(Icons.logout),
          label: const Text('تسجيل الخروج'),
        ),
      ],
    );
  }
}

class TeacherProfileScreen extends StatelessWidget {
  const TeacherProfileScreen({
    super.key,
    required this.state,
    required this.contextInfo,
    required this.onBack,
    required this.onRetry,
  });

  final AsyncValue<TeacherProfile> state;
  final SchoolContext contextInfo;
  final VoidCallback onBack;
  final VoidCallback onRetry;

  @override
  Widget build(BuildContext context) => TeacherNestedPage(
        title: 'الملف الشخصي',
        onBack: onBack,
        child: state.when(
          loading: () => const AppSkeletonCard(),
          error: (_, __) => AppCard(
            child: Column(mainAxisSize: MainAxisSize.min, children: [
              const Icon(Icons.cloud_off_outlined,
                  color: AppColors.disabled, size: 40),
              const SizedBox(height: AppSpacing.x3),
              const Text('تعذر تحميل تفاصيل الملف الشخصي'),
              const SizedBox(height: AppSpacing.x2),
              Text(
                'يمكنك متابعة استخدام التطبيق بالسياق الحالي.',
                style: Theme.of(context).textTheme.bodySmall,
              ),
              TextButton(
                onPressed: onRetry,
                child: const Text('إعادة المحاولة'),
              ),
            ]),
          ),
          data: (profile) => ListView(children: [
            AppCard(
              child: Column(children: [
                const CircleAvatar(
                  radius: 32,
                  child: Icon(Icons.person_outline, size: 34),
                ),
                const SizedBox(height: AppSpacing.x2),
                Text(
                  profile.fullName,
                  textAlign: TextAlign.center,
                  style: Theme.of(context).textTheme.titleLarge,
                ),
                const TeacherSmallLabel(label: 'معلم'),
              ]),
            ),
            const SizedBox(height: AppSpacing.x3),
            AppCard(
              child: Column(children: [
                TeacherInfoRow('المدرسة', contextInfo.schoolName),
                TeacherInfoRow(
                    'العام الدراسي', contextInfo.academicYearName),
                TeacherInfoRow('رقم الموظف', profile.employeeCode),
                TeacherInfoRow('التخصص', profile.specialization),
                TeacherInfoRow('المؤهل', profile.qualification),
                TeacherInfoRow('البريد الإلكتروني', profile.email),
                TeacherInfoRow('رقم الهاتف', profile.phone),
                TeacherInfoRow(
                  'الحالة',
                  contextInfo.isHistorical
                      ? 'للعرض فقط'
                      : profile.isActive
                          ? 'نشط'
                          : 'غير نشط',
                ),
              ]),
            ),
          ]),
        ),
      );
}

class TeacherSettingsScreen extends ConsumerWidget {
  const TeacherSettingsScreen({super.key, required this.onBack});

  final VoidCallback onBack;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final selected = ref.watch(fontProvider);
    return TeacherNestedPage(
      title: 'الإعدادات',
      onBack: onBack,
      child: ListView(children: [
        AppCard(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text('خط التطبيق',
                  style: Theme.of(context).textTheme.titleMedium),
              ...AppFont.values.map((font) => RadioListTile<AppFont>(
                    value: font,
                    groupValue: selected,
                    title: Text(font.label),
                    onChanged: (value) {
                      if (value != null) {
                        ref.read(fontProvider.notifier).select(value);
                      }
                    },
                  )),
            ],
          ),
        ),
      ]),
    );
  }
}

class TeacherInformationScreen extends StatelessWidget {
  const TeacherInformationScreen({
    super.key,
    required this.title,
    required this.message,
    required this.icon,
    required this.onBack,
  });

  final String title;
  final String message;
  final IconData icon;
  final VoidCallback onBack;

  @override
  Widget build(BuildContext context) => TeacherNestedPage(
        title: title,
        onBack: onBack,
        child: Center(
          child: AppCard(
            child: Column(mainAxisSize: MainAxisSize.min, children: [
              Icon(icon, size: 48, color: AppColors.primary),
              const SizedBox(height: AppSpacing.x3),
              Text(message, textAlign: TextAlign.center),
            ]),
          ),
        ),
      );
}

class _MoreGroup extends StatelessWidget {
  const _MoreGroup({required this.children});

  final List<Widget> children;

  @override
  Widget build(BuildContext context) =>
      AppCard(child: Column(children: children));
}

class _MoreTile extends StatelessWidget {
  const _MoreTile({
    required this.icon,
    required this.label,
    required this.onTap,
  });

  final IconData icon;
  final String label;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) => ListTile(
        contentPadding: EdgeInsets.zero,
        leading: Icon(icon, color: AppColors.primary),
        title: Text(label),
        trailing: const Icon(Icons.chevron_left),
        onTap: onTap,
      );
}
