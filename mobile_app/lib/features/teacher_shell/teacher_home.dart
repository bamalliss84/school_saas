import 'package:flutter/material.dart';

import '../../app/session/app_session.dart';
import '../../core/design_system/components.dart';
import '../../core/design_system/role_visual_tokens.dart';
import '../../core/design_system/tokens.dart';
import '../../core/models/school_context.dart';
import '../teacher/profile/teacher_profile.dart';
import '../teacher/timetable/domain/teacher_timetable_models.dart';
import '../teacher/timetable/presentation/teacher_timetable_controller.dart';
import 'teacher_shared.dart';

class TeacherHomeFoundation extends StatelessWidget {
  const TeacherHomeFoundation({
    super.key,
    required this.session,
    required this.onContext,
    required this.onProfile,
    required this.timetable,
    this.profile,
  });

  final AppSession session;
  final TeacherProfile? profile;
  final TeacherTimetableState timetable;
  final VoidCallback onContext;
  final VoidCallback onProfile;

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
          onProfile: onProfile,
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
          _LessonOverview(
            timetable: timetable,
            historical: historical,
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
    required this.onProfile,
  });

  final String name;
  final SchoolContext contextInfo;
  final VoidCallback onContext;
  final VoidCallback onProfile;

  @override
  Widget build(BuildContext context) => Container(
        decoration: const BoxDecoration(
          gradient: LinearGradient(
            colors: [RoleVisualTokens.teacher, Color(0xff103f9f)],
            begin: Alignment.topRight,
            end: Alignment.bottomLeft,
          ),
        ),
        padding: const EdgeInsets.fromLTRB(
          AppSpacing.x4,
          AppSpacing.x4,
          AppSpacing.x4,
          AppSpacing.x6,
        ),
        child: Row(children: [
          IconButton(
            tooltip: 'الملف الشخصي',
            onPressed: onProfile,
            style: IconButton.styleFrom(backgroundColor: Colors.white24),
            icon: const Icon(Icons.person_outline, color: Colors.white),
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
                  contextInfo.schoolName,
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
              color: RoleVisualTokens.softSurface(AppVisualRole.teacher),
              borderRadius: BorderRadius.circular(AppRadius.chip),
            ),
            child: const Icon(Icons.school_outlined,
                color: RoleVisualTokens.teacher),
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

class _LessonOverview extends StatelessWidget {
  const _LessonOverview({
    required this.timetable,
    required this.historical,
  });

  final TeacherTimetableState timetable;
  final bool historical;

  @override
  Widget build(BuildContext context) {
    final ready = timetable is TeacherTimetableReady
        ? timetable as TeacherTimetableReady
        : null;
    final current = !historical && ready != null
        ? _actualCurrent(ready.data.current)
        : null;
    final next = !historical && ready != null
        ? _actualNext(ready.data.next)
        : null;
    return Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
      Text('الحصة الحالية', style: Theme.of(context).textTheme.titleLarge),
      const SizedBox(height: AppSpacing.x2),
      if (historical)
        const _FoundationCard(
          icon: Icons.history_edu_outlined,
          title: 'السجل السابق للعرض فقط',
          subtitle: 'لا تُعرض حالة مباشرة أو إجراءات حصة في هذا السياق.',
        )
      else if (timetable is TeacherTimetableLoading)
        const AppSkeletonCard()
      else if (timetable is TeacherTimetableFailure)
        const _FoundationCard(
          icon: Icons.cloud_off_outlined,
          title: 'تعذر تحميل ملخص الحصص',
          subtitle: 'يمكنك إعادة المحاولة من شاشة جدولي.',
        )
      else if (current != null)
        _HomeLessonCard(
          item: current,
          label: 'جارية الآن',
          color: AppColors.success,
        )
      else
        const _FoundationCard(
          icon: Icons.schedule_outlined,
          title: 'لا توجد حصة جارية الآن',
          subtitle: 'ستظهر هنا تفاصيل الحصة عندما يحين موعدها.',
        ),
      if (!historical && timetable is! TeacherTimetableFailure) ...[
        const SizedBox(height: AppSpacing.x4),
        Text('الحصة التالية', style: Theme.of(context).textTheme.titleLarge),
        const SizedBox(height: AppSpacing.x2),
        if (timetable is TeacherTimetableLoading)
          const AppSkeletonCard()
        else if (next != null)
          _HomeLessonCard(
            item: next,
            label: _nextLabel(next),
            color: RoleVisualTokens.teacher,
          )
        else
          const _FoundationCard(
            icon: Icons.event_available_outlined,
            title: 'لا توجد حصة قادمة',
            subtitle: 'لا توجد حصة لاحقة متاحة في بيانات الجدول الحالية.',
          ),
      ],
    ]);
  }
}

class _HomeLessonCard extends StatelessWidget {
  const _HomeLessonCard({
    required this.item,
    required this.label,
    required this.color,
  });

  final DatedTeacherLesson item;
  final String label;
  final Color color;

  @override
  Widget build(BuildContext context) {
    final lesson = item.lesson;
    final classLabel = [lesson.classroom, lesson.section]
        .where((value) => value.isNotEmpty)
        .join(' — ');
    return AppCard(
      child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Container(
            padding: const EdgeInsets.all(AppSpacing.x2),
            decoration: BoxDecoration(
              color: color.withOpacity(.1),
              borderRadius: BorderRadius.circular(AppRadius.chip),
            ),
            child: Icon(Icons.menu_book_outlined, color: color),
          ),
          const SizedBox(width: AppSpacing.x3),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(lesson.subject,
                    maxLines: 2,
                    overflow: TextOverflow.ellipsis,
                    style: Theme.of(context).textTheme.titleMedium),
                if (classLabel.isNotEmpty) Text(classLabel),
                Text(
                  '${_shortLessonTime(lesson.period.startTime)} - ${_shortLessonTime(lesson.period.endTime)}',
                  style: Theme.of(context).textTheme.bodySmall,
                ),
                if (lesson.roomOrLocation.isNotEmpty)
                  Text(lesson.roomOrLocation,
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                      style: Theme.of(context).textTheme.bodySmall),
              ],
            ),
          ),
          const SizedBox(width: AppSpacing.x2),
          TeacherSmallLabel(label: label, color: color),
        ]),
      ]),
    );
  }
}

DatedTeacherLesson? _actualCurrent(DatedTeacherLesson? item) {
  if (item == null) return null;
  final start = _lessonDateTime(item.date, item.lesson.period.startTime);
  final end = _lessonDateTime(item.date, item.lesson.period.endTime);
  if (start == null || end == null) {
    return item.lesson.status == 'current' ? item : null;
  }
  final now = DateTime.now();
  return !now.isBefore(start) && now.isBefore(end) ? item : null;
}

DatedTeacherLesson? _actualNext(DatedTeacherLesson? item) {
  if (item == null) return null;
  final start = _lessonDateTime(item.date, item.lesson.period.startTime);
  if (start == null) return item;
  return start.isAfter(DateTime.now()) ? item : null;
}

String _nextLabel(DatedTeacherLesson item) {
  final start = _lessonDateTime(item.date, item.lesson.period.startTime);
  if (start == null) return 'قادمة';
  final minutes = start.difference(DateTime.now()).inMinutes;
  if (minutes < 0) return 'قادمة';
  if (minutes < 60) return 'بعد $minutes دقيقة';
  final hours = minutes ~/ 60;
  final remainder = minutes % 60;
  return remainder == 0 ? 'بعد $hours ساعة' : 'بعد $hours س و$remainder د';
}

DateTime? _lessonDateTime(DateTime date, String value) {
  final parts = value.split(':');
  if (parts.length < 2) return null;
  final hour = int.tryParse(parts[0]);
  final minute = int.tryParse(parts[1]);
  if (hour == null || minute == null) return null;
  return DateTime(date.year, date.month, date.day, hour, minute);
}

String _shortLessonTime(String value) =>
    value.length >= 5 ? value.substring(0, 5) : value;

class _FoundationCard extends StatelessWidget {
  const _FoundationCard({
    required this.icon,
    required this.title,
    required this.subtitle,
  });

  final IconData icon;
  final String title;
  final String subtitle;

  @override
  Widget build(BuildContext context) => AppCard(
        child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Row(children: [
            Container(
              padding: const EdgeInsets.all(AppSpacing.x2),
              decoration: BoxDecoration(
                color: RoleVisualTokens.softSurface(AppVisualRole.teacher),
                borderRadius: BorderRadius.circular(AppRadius.chip),
              ),
              child: Icon(icon, color: RoleVisualTokens.teacher),
            ),
            const SizedBox(width: AppSpacing.x2),
            Expanded(
                child: Text(title,
                    style: Theme.of(context).textTheme.titleMedium)),
          ]),
          const SizedBox(height: AppSpacing.x2),
          Text(subtitle, style: Theme.of(context).textTheme.bodySmall),
        ]),
      );
}
