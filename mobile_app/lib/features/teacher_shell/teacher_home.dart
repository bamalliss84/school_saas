import 'package:flutter/material.dart';

import '../../app/session/app_session.dart';
import '../../core/design_system/components.dart';
import '../../core/design_system/tokens.dart';
import '../../core/models/school_context.dart';
import '../teacher/profile/teacher_profile.dart';
import 'teacher_shared.dart';

class TeacherHomeFoundation extends StatelessWidget {
  const TeacherHomeFoundation({
    super.key,
    required this.session,
    required this.onContext,
    required this.onSchedule,
    this.profile,
    this.onAttendance,
    this.onTasks,
  });

  final AppSession session;
  final TeacherProfile? profile;
  final VoidCallback onContext;
  final VoidCallback onSchedule;
  final VoidCallback? onAttendance;
  final VoidCallback? onTasks;

  @override
  Widget build(BuildContext context) {
    final contextInfo = session.context!;
    final historical = session.status == SessionStatus.historical;
    final profileName = profile?.fullName ?? '';
    final name = profileName.isNotEmpty
        ? profileName
        : session.user?.fullName ?? '';
    return CustomScrollView(slivers: [
      SliverToBoxAdapter(
        child: TeacherHeader(
          name: name,
          contextInfo: contextInfo,
          onContext: onContext,
        ),
      ),
      SliverPadding(
        padding: const EdgeInsets.fromLTRB(
          AppSpacing.x4,
          AppSpacing.x2,
          AppSpacing.x4,
          AppSpacing.x6,
        ),
        sliver: SliverList.list(children: [
          TeacherContextCard(contextInfo: contextInfo, onTap: onContext),
          const SizedBox(height: AppSpacing.x4),
          Text('الحصة الحالية', style: Theme.of(context).textTheme.titleLarge),
          const SizedBox(height: AppSpacing.x2),
          _FoundationCard(
            icon: Icons.play_lesson_outlined,
            title: historical
                ? 'لا توجد حالة حصة جارية في السجل السابق'
                : 'لا توجد حصة جارية الآن',
            subtitle: historical
                ? 'يمكنك استعراض الجدول المحفوظ لهذا السياق.'
                : 'ستظهر تفاصيل الحصة هنا عند ربط الجدول.',
            actionLabel: 'عرض جدولي',
            onAction: onSchedule,
          ),
          const SizedBox(height: AppSpacing.x4),
          Text('الحصة التالية', style: Theme.of(context).textTheme.titleLarge),
          const SizedBox(height: AppSpacing.x2),
          const _FoundationCard(
            icon: Icons.update_outlined,
            title: 'لم تُحمّل بيانات الحصة التالية بعد',
            subtitle: 'سيعرض هذا القسم الموعد والمادة والفصل لاحقًا.',
          ),
          if (!historical) ...[
            const SizedBox(height: AppSpacing.x4),
            Text('يحتاج انتباهك',
                style: Theme.of(context).textTheme.titleLarge),
            const SizedBox(height: AppSpacing.x2),
            const _FoundationCard(
              icon: Icons.check_circle_outline,
              title: 'لا توجد تنبيهات عاجلة',
              subtitle: 'ستظهر هنا الأعمال التي تحتاج إلى إجراء.',
            ),
          ],
          const SizedBox(height: AppSpacing.x4),
          Text(historical ? 'الوصول السريع' : 'إجراءات سريعة',
              style: Theme.of(context).textTheme.titleLarge),
          const SizedBox(height: AppSpacing.x2),
          Row(children: [
            Expanded(
              child: _QuickAction(
                icon: Icons.calendar_month_outlined,
                label: 'جدولي',
                onTap: onSchedule,
              ),
            ),
            if (!historical) ...[
              const SizedBox(width: AppSpacing.x2),
              Expanded(
                child: _QuickAction(
                  icon: Icons.how_to_reg_outlined,
                  label: 'الحضور',
                  onTap: onAttendance,
                ),
              ),
              const SizedBox(width: AppSpacing.x2),
              Expanded(
                child: _QuickAction(
                  icon: Icons.assignment_outlined,
                  label: 'المهام',
                  onTap: onTasks,
                ),
              ),
            ],
          ]),
        ]),
      ),
    ]);
  }
}

class TeacherHeader extends StatelessWidget {
  const TeacherHeader({
    super.key,
    required this.name,
    required this.contextInfo,
    required this.onContext,
  });

  final String name;
  final SchoolContext contextInfo;
  final VoidCallback onContext;

  @override
  Widget build(BuildContext context) => Container(
        color: AppColors.primary,
        padding: const EdgeInsets.all(AppSpacing.x4),
        child: Row(children: [
          const CircleAvatar(
            backgroundColor: Colors.white24,
            child: Icon(Icons.person_outline, color: Colors.white),
          ),
          const SizedBox(width: AppSpacing.x3),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  name.isEmpty ? 'مرحبًا بك' : 'مرحبًا، $name',
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                  style: Theme.of(context)
                      .textTheme
                      .titleLarge
                      ?.copyWith(color: Colors.white),
                ),
                Text(
                  '${contextInfo.schoolName} • ${contextInfo.academicYearName ?? '—'}',
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                  style: const TextStyle(color: Colors.white70),
                ),
              ],
            ),
          ),
          IconButton(
            tooltip: 'تغيير المدرسة أو الدور',
            onPressed: onContext,
            icon: const Icon(Icons.swap_horiz, color: Colors.white),
          ),
        ]),
      );
}

class TeacherContextCard extends StatelessWidget {
  const TeacherContextCard({
    super.key,
    required this.contextInfo,
    required this.onTap,
  });

  final SchoolContext contextInfo;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) => AppCard(
        child: ListTile(
          contentPadding: EdgeInsets.zero,
          leading: Container(
            padding: const EdgeInsets.all(AppSpacing.x2),
            decoration: BoxDecoration(
              color: AppColors.primary.withOpacity(.08),
              borderRadius: BorderRadius.circular(AppRadius.chip),
            ),
            child: const Icon(Icons.school_outlined, color: AppColors.primary),
          ),
          title: Text(contextInfo.schoolName),
          subtitle: Text(
            '${contextInfo.academicYearName ?? '—'} • ${contextInfo.isHistorical ? 'للعرض فقط' : 'معلم • نشط'}',
          ),
          trailing: const Icon(Icons.chevron_left),
          onTap: onTap,
        ),
      );
}

class TeacherHistoricalBanner extends StatelessWidget {
  const TeacherHistoricalBanner({super.key, required this.contextInfo});

  final SchoolContext contextInfo;

  @override
  Widget build(BuildContext context) => Container(
        width: double.infinity,
        color: const Color(0xfffff4e5),
        padding: const EdgeInsets.all(AppSpacing.x3),
        child: Row(children: [
          const Icon(Icons.history_edu_outlined, color: AppColors.warning),
          const SizedBox(width: AppSpacing.x2),
          Expanded(
            child: Text(
              'أنت تستعرض سنة دراسية سابقة — ${contextInfo.academicYearName ?? ''}\nلا يمكن إجراء تعديلات في هذا السياق',
              style: const TextStyle(color: AppColors.warning),
            ),
          ),
        ]),
      );
}

class TeacherFutureFeature extends StatelessWidget {
  const TeacherFutureFeature({
    super.key,
    required this.title,
    required this.message,
    required this.detail,
    required this.icon,
  });

  final String title;
  final String message;
  final String detail;
  final IconData icon;

  @override
  Widget build(BuildContext context) => Column(children: [
        TeacherPageTitle(title: title),
        Expanded(
          child: Center(
            child: Padding(
              padding: const EdgeInsets.all(AppSpacing.x6),
              child: AppCard(
                child: Column(mainAxisSize: MainAxisSize.min, children: [
                  Icon(icon, size: 54, color: AppColors.disabled),
                  const SizedBox(height: AppSpacing.x4),
                  Text(message,
                      textAlign: TextAlign.center,
                      style: Theme.of(context).textTheme.titleLarge),
                  const SizedBox(height: AppSpacing.x2),
                  Text(detail,
                      textAlign: TextAlign.center,
                      style: Theme.of(context).textTheme.bodySmall),
                ]),
              ),
            ),
          ),
        ),
      ]);
}

class _FoundationCard extends StatelessWidget {
  const _FoundationCard({
    required this.icon,
    required this.title,
    required this.subtitle,
    this.actionLabel,
    this.onAction,
  });

  final IconData icon;
  final String title;
  final String subtitle;
  final String? actionLabel;
  final VoidCallback? onAction;

  @override
  Widget build(BuildContext context) => AppCard(
        child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Row(children: [
            Icon(icon, color: AppColors.primary),
            const SizedBox(width: AppSpacing.x2),
            Expanded(
                child: Text(title,
                    style: Theme.of(context).textTheme.titleMedium)),
          ]),
          const SizedBox(height: AppSpacing.x2),
          Text(subtitle, style: Theme.of(context).textTheme.bodySmall),
          if (actionLabel != null && onAction != null) ...[
            const SizedBox(height: AppSpacing.x3),
            SizedBox(
              width: double.infinity,
              child: OutlinedButton(
                onPressed: onAction,
                child: Text(actionLabel!),
              ),
            ),
          ],
        ]),
      );
}

class _QuickAction extends StatelessWidget {
  const _QuickAction({required this.icon, required this.label, this.onTap});

  final IconData icon;
  final String label;
  final VoidCallback? onTap;

  @override
  Widget build(BuildContext context) => Material(
        color: AppColors.surface,
        borderRadius: BorderRadius.circular(AppRadius.card),
        child: InkWell(
          onTap: onTap,
          borderRadius: BorderRadius.circular(AppRadius.card),
          child: Padding(
            padding: const EdgeInsets.symmetric(
              horizontal: AppSpacing.x2,
              vertical: AppSpacing.x4,
            ),
            child: Column(children: [
              Icon(icon,
                  color: onTap == null
                      ? AppColors.disabled
                      : AppColors.primary),
              const SizedBox(height: AppSpacing.x2),
              Text(label, textAlign: TextAlign.center),
            ]),
          ),
        ),
      );
}
