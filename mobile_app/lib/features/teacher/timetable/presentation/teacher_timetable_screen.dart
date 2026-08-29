import 'package:flutter/material.dart';

import '../../../../core/design_system/components.dart';
import '../../../../core/design_system/role_visual_tokens.dart';
import '../../../../core/design_system/tokens.dart';
import '../domain/teacher_timetable_models.dart';
import 'teacher_timetable_controller.dart';

class TeacherTimetableScreen extends StatefulWidget {
  const TeacherTimetableScreen({
    super.key,
    required this.state,
    required this.historical,
    required this.onRefresh,
  });

  final TeacherTimetableState state;
  final bool historical;
  final Future<void> Function() onRefresh;

  @override
  State<TeacherTimetableScreen> createState() => _TeacherTimetableScreenState();
}

class _TeacherTimetableScreenState extends State<TeacherTimetableScreen> {
  bool weekMode = false;
  DateTime? selectedDate;

  @override
  Widget build(BuildContext context) {
    final state = widget.state;
    if (state is TeacherTimetableLoading) {
      return const _TimetableLoadingView();
    }
    if (state is TeacherTimetableFailure) {
      return _TimetableErrorView(onRetry: widget.onRefresh);
    }
    final ready = state as TeacherTimetableReady;
    final data = ready.data;
    return Column(children: [
      _TimetableHeader(
        weekMode: weekMode,
        onChanged: (value) => setState(() => weekMode = value),
      ),
      if (ready.refreshing)
        const LinearProgressIndicator(minHeight: 2),
      Expanded(
        child: weekMode
            ? _weekView(data)
            : _todayView(data),
      ),
    ]);
  }

  Widget _todayView(TeacherTimetableData data) {
    final today = data.today;
    return RefreshIndicator(
      onRefresh: widget.onRefresh,
      child: ListView(
        physics: const AlwaysScrollableScrollPhysics(),
        padding: const EdgeInsets.fromLTRB(
          AppSpacing.x4,
          AppSpacing.x2,
          AppSpacing.x4,
          AppSpacing.x6,
        ),
        children: [
          if (!widget.historical) ..._operationalSummary(data),
          if (widget.historical)
            const _ArchiveNotice(),
          const SizedBox(height: AppSpacing.x4),
          Text('حصص اليوم', style: Theme.of(context).textTheme.titleLarge),
          const SizedBox(height: AppSpacing.x2),
          if (today.entries.isEmpty)
            _EmptyDay(onWeek: () => setState(() => weekMode = true))
          else
            ..._todayTimeline(today),
          const SizedBox(height: AppSpacing.x3),
          LastUpdatedLabel(value: data.lastUpdated.toLocal()),
        ],
      ),
    );
  }

  List<Widget> _operationalSummary(TeacherTimetableData data) {
    final current = data.current != null &&
            _statusFor(data.current!.lesson, data.current!.date, false) ==
                _LessonVisualStatus.current
        ? data.current
        : null;
    final next = data.next != null && _minutesUntil(data.next!) != null
        ? data.next
        : null;
    if (current != null) {
      return [
        Text('الحصة الحالية', style: Theme.of(context).textTheme.titleLarge),
        const SizedBox(height: AppSpacing.x2),
        _LessonCard(
          lesson: current.lesson,
          status: _LessonVisualStatus.current,
          prominent: true,
          onOpen: () => ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(
              content: Text('أدوات الحصة ستتوفر في مرحلة الحضور القادمة.'),
            ),
          ),
        ),
      ];
    }
    return [
      const _NoCurrentLesson(),
      if (next != null) ...[
        const SizedBox(height: AppSpacing.x4),
        Text('الحصة القادمة', style: Theme.of(context).textTheme.titleLarge),
        const SizedBox(height: AppSpacing.x2),
        _LessonCard(
          lesson: next.lesson,
          status: _LessonVisualStatus.upcoming,
          countdownMinutes: _minutesUntil(next),
          prominent: true,
        ),
      ],
    ];
  }

  List<Widget> _todayTimeline(TeacherTodayTimetable today) {
    if (today.periods.isEmpty) {
      return today.entries
          .map((entry) => Padding(
                padding: const EdgeInsets.only(bottom: AppSpacing.x2),
                child: _LessonCard(
                  lesson: entry,
                  status: _statusFor(entry, today.date, widget.historical),
                ),
              ))
          .toList();
    }
    final entriesByPeriod = {
      for (final entry in today.entries) entry.period.id: entry,
    };
    return today.periods.map((period) {
      final entry = entriesByPeriod[period.id];
      return Padding(
        padding: const EdgeInsets.only(bottom: AppSpacing.x2),
        child: period.isBreak
            ? _PeriodOnlyCard(period: period, breakPeriod: true)
            : entry == null
                ? _PeriodOnlyCard(period: period)
                : _LessonCard(
                    lesson: entry,
                    status: _statusFor(entry, today.date, widget.historical),
                  ),
      );
    }).toList();
  }

  Widget _weekView(TeacherTimetableData data) {
    final days = data.week.days;
    final selected = _selectedDay(days, data.today.date);
    return RefreshIndicator(
      onRefresh: widget.onRefresh,
      child: ListView(
        physics: const AlwaysScrollableScrollPhysics(),
        padding: const EdgeInsets.fromLTRB(
          AppSpacing.x4,
          AppSpacing.x2,
          AppSpacing.x4,
          AppSpacing.x6,
        ),
        children: [
          if (widget.historical) const _ArchiveNotice(),
          if (widget.historical) const SizedBox(height: AppSpacing.x3),
          SizedBox(
            height: 68,
            child: ListView.separated(
              scrollDirection: Axis.horizontal,
              itemCount: days.length,
              separatorBuilder: (_, __) =>
                  const SizedBox(width: AppSpacing.x2),
              itemBuilder: (context, index) {
                final day = days[index];
                final active = _sameDate(day.date, selected.date);
                return ChoiceChip(
                  selected: active,
                  onSelected: (_) => setState(() => selectedDate = day.date),
                  selectedColor:
                      RoleVisualTokens.softSurface(AppVisualRole.teacher),
                  side: BorderSide(
                    color: active
                        ? RoleVisualTokens.teacher
                        : AppColors.divider,
                  ),
                  labelStyle: TextStyle(
                    color: active
                        ? RoleVisualTokens.teacher
                        : AppColors.textSecondary,
                    fontWeight: active ? FontWeight.w700 : FontWeight.w500,
                  ),
                  label: SizedBox(
                    width: 48,
                    child: Column(mainAxisSize: MainAxisSize.min, children: [
                      Text(_weekdayLabel(day.weekday)),
                      Text('${day.date.day}'),
                    ]),
                  ),
                );
              },
            ),
          ),
          const SizedBox(height: AppSpacing.x3),
          Text(
            '${_weekdayLabel(selected.weekday)} ${selected.date.day}/${selected.date.month}',
            style: Theme.of(context).textTheme.titleLarge,
          ),
          const SizedBox(height: AppSpacing.x2),
          if (selected.entries.isEmpty)
            const AppCard(child: AppEmptyState(message: 'لا توجد حصص في هذا اليوم'))
          else
            ...selected.entries.map((entry) => Padding(
                  padding: const EdgeInsets.only(bottom: AppSpacing.x2),
                  child: _LessonCard(
                    lesson: entry,
                    status: _statusFor(entry, selected.date, widget.historical),
                  ),
                )),
          const SizedBox(height: AppSpacing.x3),
          LastUpdatedLabel(value: data.lastUpdated.toLocal()),
        ],
      ),
    );
  }

  TeacherTimetableDay _selectedDay(
      List<TeacherTimetableDay> days, DateTime today) {
    if (days.isEmpty) {
      return TeacherTimetableDay(date: today, weekday: 0, entries: const []);
    }
    final wanted = selectedDate ?? today;
    return days.firstWhere(
      (day) => _sameDate(day.date, wanted),
      orElse: () => days.first,
    );
  }
}

class _TimetableHeader extends StatelessWidget {
  const _TimetableHeader({required this.weekMode, required this.onChanged});
  final bool weekMode;
  final ValueChanged<bool> onChanged;

  @override
  Widget build(BuildContext context) => Container(
        color: RoleVisualTokens.softSurface(AppVisualRole.teacher),
        padding: const EdgeInsets.fromLTRB(
          AppSpacing.x4, AppSpacing.x4, AppSpacing.x4, AppSpacing.x3),
        child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Row(children: [
            Container(
              padding: const EdgeInsets.all(AppSpacing.x2),
              decoration: BoxDecoration(
                color: Colors.white,
                borderRadius: BorderRadius.circular(AppRadius.chip),
              ),
              child: const Icon(Icons.calendar_month_outlined,
                  color: RoleVisualTokens.teacher),
            ),
            const SizedBox(width: AppSpacing.x3),
            Text('جدولي', style: Theme.of(context).textTheme.headlineMedium),
          ]),
          const SizedBox(height: AppSpacing.x3),
          SizedBox(
            width: double.infinity,
            child: SegmentedButton<bool>(
              segments: const [
                ButtonSegment(value: false, label: Text('اليوم')),
                ButtonSegment(value: true, label: Text('الأسبوع')),
              ],
              selected: {weekMode},
              onSelectionChanged: (selection) => onChanged(selection.first),
              showSelectedIcon: false,
              style: ButtonStyle(
                visualDensity: VisualDensity.compact,
                backgroundColor: MaterialStateProperty.resolveWith(
                  (states) => states.contains(MaterialState.selected)
                      ? RoleVisualTokens.teacher
                      : Colors.white,
                ),
                foregroundColor: MaterialStateProperty.resolveWith(
                  (states) => states.contains(MaterialState.selected)
                      ? Colors.white
                      : AppColors.textPrimary,
                ),
              ),
            ),
          ),
        ]),
      );
}

enum _LessonVisualStatus { completed, current, upcoming, archival }

class _LessonCard extends StatelessWidget {
  const _LessonCard({
    required this.lesson,
    required this.status,
    this.countdownMinutes,
    this.prominent = false,
    this.onOpen,
  });

  final TeacherLesson lesson;
  final _LessonVisualStatus status;
  final int? countdownMinutes;
  final bool prominent;
  final VoidCallback? onOpen;

  @override
  Widget build(BuildContext context) => _TeacherCardSurface(
        prominent: prominent,
        child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
              Container(
                padding: const EdgeInsets.all(AppSpacing.x2),
                decoration: BoxDecoration(
                  color: RoleVisualTokens.softSurface(AppVisualRole.teacher),
                  borderRadius: BorderRadius.circular(AppRadius.chip),
                ),
                child: const Icon(Icons.menu_book_outlined,
                    color: RoleVisualTokens.teacher),
              ),
              const SizedBox(width: AppSpacing.x3),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(lesson.period.name,
                        style: Theme.of(context).textTheme.bodySmall),
                    Text(lesson.subject,
                        style: Theme.of(context).textTheme.titleMedium),
                    Text(_classLabel(lesson)),
                    Text(_timeRange(lesson.period)),
                    if (lesson.roomOrLocation.isNotEmpty)
                      Text(lesson.roomOrLocation,
                          style: Theme.of(context).textTheme.bodySmall),
                  ],
                ),
              ),
              _StatusLabel(status: status, countdownMinutes: countdownMinutes),
            ]),
            if (onOpen != null) ...[
              const SizedBox(height: AppSpacing.x3),
              AppPrimaryButton(label: 'فتح الحصة', onPressed: onOpen),
            ],
          ]),
      );
}

class _StatusLabel extends StatelessWidget {
  const _StatusLabel({required this.status, this.countdownMinutes});
  final _LessonVisualStatus status;
  final int? countdownMinutes;

  @override
  Widget build(BuildContext context) {
    final (label, color) = switch (status) {
      _LessonVisualStatus.completed => ('انتهت', AppColors.disabled),
      _LessonVisualStatus.current => ('جارية الآن', AppColors.success),
      _LessonVisualStatus.archival => ('للعرض فقط', AppColors.warning),
      _LessonVisualStatus.upcoming => (
          countdownMinutes != null && countdownMinutes! >= 0
              ? 'تبدأ بعد $countdownMinutes دقيقة'
              : 'قادمة',
          AppColors.success,
        ),
    };
    return Container(
      padding: const EdgeInsets.symmetric(
        horizontal: AppSpacing.x2,
        vertical: AppSpacing.x1,
      ),
      decoration: BoxDecoration(
        color: color.withOpacity(.12),
        borderRadius: BorderRadius.circular(AppRadius.chip),
      ),
      child: Text(label, style: TextStyle(color: color, fontSize: 12)),
    );
  }
}

class _PeriodOnlyCard extends StatelessWidget {
  const _PeriodOnlyCard({required this.period, this.breakPeriod = false});
  final TeacherTimetablePeriod period;
  final bool breakPeriod;

  @override
  Widget build(BuildContext context) => _TeacherCardSurface(
        child: Row(children: [
          Icon(
            breakPeriod ? Icons.free_breakfast_outlined : Icons.event_busy,
            color: AppColors.disabled,
          ),
          const SizedBox(width: AppSpacing.x3),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(period.name,
                    style: Theme.of(context).textTheme.titleMedium),
                Text(_timeRange(period)),
              ],
            ),
          ),
          Text(breakPeriod ? 'استراحة' : 'لا توجد حصة',
              style: Theme.of(context).textTheme.bodySmall),
        ]),
      );
}

class _NoCurrentLesson extends StatelessWidget {
  const _NoCurrentLesson();
  @override
  Widget build(BuildContext context) => const _TeacherCardSurface(
        child: Row(children: [
          Icon(Icons.schedule_outlined, color: AppColors.disabled),
          SizedBox(width: AppSpacing.x3),
          Expanded(child: Text('لا توجد حصة جارية الآن')),
        ]),
      );
}

class _ArchiveNotice extends StatelessWidget {
  const _ArchiveNotice();
  @override
  Widget build(BuildContext context) => const _TeacherCardSurface(
        child: Row(children: [
          Icon(Icons.history_edu_outlined, color: AppColors.warning),
          SizedBox(width: AppSpacing.x3),
          Expanded(child: Text('جدول سنة دراسية سابقة — للعرض فقط')),
        ]),
      );
}

class _EmptyDay extends StatelessWidget {
  const _EmptyDay({required this.onWeek});
  final VoidCallback onWeek;
  @override
  Widget build(BuildContext context) => AppCard(
        child: Column(children: [
          const Icon(Icons.event_available_outlined,
              size: 48, color: AppColors.disabled),
          const SizedBox(height: AppSpacing.x3),
          Text('لا توجد حصص اليوم',
              style: Theme.of(context).textTheme.titleLarge),
          const SizedBox(height: AppSpacing.x1),
          const Text('يمكنك مراجعة جدول بقية الأسبوع.'),
          const SizedBox(height: AppSpacing.x3),
          AppPrimaryButton(label: 'عرض جدول الأسبوع', onPressed: onWeek),
        ]),
      );
}

class _TeacherCardSurface extends StatelessWidget {
  const _TeacherCardSurface({required this.child, this.prominent = false});

  final Widget child;
  final bool prominent;

  @override
  Widget build(BuildContext context) => Container(
        padding: const EdgeInsets.all(AppSpacing.x4),
        decoration: BoxDecoration(
          color: prominent
              ? RoleVisualTokens.softSurface(AppVisualRole.teacher)
              : AppColors.surface,
          borderRadius: BorderRadius.circular(AppRadius.card),
          border: Border.all(
            color: prominent
                ? RoleVisualTokens.teacher.withOpacity(.28)
                : AppColors.divider.withOpacity(.75),
          ),
          boxShadow: const [
            BoxShadow(
              color: Color(0x0a101828),
              blurRadius: 12,
              offset: Offset(0, 4),
            ),
          ],
        ),
        child: child,
      );
}

class _TimetableLoadingView extends StatelessWidget {
  const _TimetableLoadingView();
  @override
  Widget build(BuildContext context) => ListView(
        padding: const EdgeInsets.all(AppSpacing.x4),
        children: const [
          SizedBox(height: AppSpacing.x4),
          AppSkeletonCard(),
          SizedBox(height: AppSpacing.x3),
          AppSkeletonCard(),
          SizedBox(height: AppSpacing.x3),
          AppSkeletonCard(),
        ],
      );
}

class _TimetableErrorView extends StatelessWidget {
  const _TimetableErrorView({required this.onRetry});
  final Future<void> Function() onRetry;
  @override
  Widget build(BuildContext context) => Center(
        child: Padding(
          padding: const EdgeInsets.all(AppSpacing.x6),
          child: AppCard(
            child: Column(mainAxisSize: MainAxisSize.min, children: [
              const Icon(Icons.cloud_off_outlined,
                  size: 48, color: AppColors.error),
              const SizedBox(height: AppSpacing.x3),
              Text('تعذر تحميل الجدول',
                  style: Theme.of(context).textTheme.titleLarge),
              const SizedBox(height: AppSpacing.x2),
              const Text('تحقق من الاتصال وحاول مرة أخرى.'),
              const SizedBox(height: AppSpacing.x3),
              AppPrimaryButton(
                label: 'إعادة المحاولة',
                onPressed: () => onRetry(),
              ),
            ]),
          ),
        ),
      );
}

_LessonVisualStatus _statusFor(
    TeacherLesson lesson, DateTime date, bool historical) {
  if (historical) return _LessonVisualStatus.archival;
  final start = _dateTimeFor(date, lesson.period.startTime);
  final end = _dateTimeFor(date, lesson.period.endTime);
  if (start != null && end != null) {
    final now = DateTime.now();
    if (!now.isBefore(end)) return _LessonVisualStatus.completed;
    if (!now.isBefore(start)) return _LessonVisualStatus.current;
    return _LessonVisualStatus.upcoming;
  }
  return switch (lesson.status) {
    'finished' => _LessonVisualStatus.completed,
    'current' => _LessonVisualStatus.current,
    _ => _LessonVisualStatus.upcoming,
  };
}

int? _minutesUntil(DatedTeacherLesson item) {
  final start = _dateTimeFor(item.date, item.lesson.period.startTime);
  if (start == null) return null;
  final minutes = start.difference(DateTime.now()).inMinutes;
  return minutes >= 0 ? minutes : null;
}

DateTime? _dateTimeFor(DateTime date, String time) {
  final parts = time.split(':');
  if (parts.length < 2) return null;
  final hour = int.tryParse(parts[0]);
  final minute = int.tryParse(parts[1]);
  if (hour == null || minute == null) return null;
  return DateTime(date.year, date.month, date.day, hour, minute);
}

String _timeRange(TeacherTimetablePeriod period) =>
    '${_shortTime(period.startTime)} - ${_shortTime(period.endTime)}';

String _shortTime(String value) => value.length >= 5 ? value.substring(0, 5) : value;

String _classLabel(TeacherLesson lesson) =>
    [lesson.classroom, lesson.section]
        .where((value) => value.isNotEmpty)
        .join(' — ');

String _weekdayLabel(int weekday) => switch (weekday) {
      0 => 'الأحد',
      1 => 'الاثنين',
      2 => 'الثلاثاء',
      3 => 'الأربعاء',
      4 => 'الخميس',
      5 => 'الجمعة',
      6 => 'السبت',
      _ => 'اليوم',
    };

bool _sameDate(DateTime first, DateTime second) =>
    first.year == second.year &&
    first.month == second.month &&
    first.day == second.day;
