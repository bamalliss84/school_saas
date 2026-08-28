import 'package:flutter/material.dart';
import '../../../../core/design_system/components.dart';
import '../../../../core/design_system/tokens.dart';
import '../data/timetable_repository.dart';
import '../domain/timetable_models.dart';

class StudentHomeScreen extends StatelessWidget {
  const StudentHomeScreen(
      {super.key,
      required this.data,
      required this.studentName,
      required this.schoolName,
      required this.academicYear,
      required this.onOpenTimetable,
      required this.onOpenAttendance,
      this.onRefresh});
  final StudentTimetableData data;
  final String studentName;
  final String schoolName;
  final String academicYear;
  final VoidCallback onOpenTimetable;
  final VoidCallback onOpenAttendance;
  final Future<void> Function()? onRefresh;
  @override
  Widget build(BuildContext context) => RefreshIndicator(
        onRefresh: onRefresh ?? () async {},
        child:
            ListView(padding: const EdgeInsets.all(AppSpacing.x4), children: [
          Text('مرحبًا، ${studentName.isEmpty ? 'طالبنا' : studentName}',
              maxLines: 2,
              overflow: TextOverflow.ellipsis,
              style: Theme.of(context).textTheme.headlineMedium),
          const SizedBox(height: AppSpacing.x1),
          Text('$schoolName • $academicYear',
              maxLines: 2,
              overflow: TextOverflow.ellipsis,
              style: Theme.of(context)
                  .textTheme
                  .bodySmall
                  ?.copyWith(color: AppColors.textSecondary)),
          const SizedBox(height: AppSpacing.x3),
          AppCard(
            child: InkWell(
              onTap: onOpenAttendance,
              borderRadius: BorderRadius.circular(AppRadius.card),
              child: Padding(
                padding: const EdgeInsets.all(AppSpacing.x1),
                child: Row(children: [
                  Container(
                    width: 40,
                    height: 40,
                    decoration: BoxDecoration(
                      color: AppColors.primary.withOpacity(0.08),
                      borderRadius: BorderRadius.circular(AppRadius.chip),
                    ),
                    child: const Icon(Icons.fact_check_outlined,
                        color: AppColors.primary),
                  ),
                  const SizedBox(width: AppSpacing.x3),
                  Expanded(
                      child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text('الحضور والغياب',
                          style: Theme.of(context).textTheme.titleSmall),
                      Text('عرض السجل اليومي',
                          maxLines: 1,
                          overflow: TextOverflow.ellipsis,
                          style: Theme.of(context)
                              .textTheme
                              .bodySmall
                              ?.copyWith(color: AppColors.textSecondary)),
                    ],
                  )),
                  const Icon(Icons.chevron_left,
                      size: 20, color: AppColors.textSecondary),
                ]),
              ),
            ),
          ),
          const SizedBox(height: AppSpacing.x4),
          Row(mainAxisAlignment: MainAxisAlignment.spaceBetween, children: [
            Expanded(
              child: Text(
                'حصصي اليوم',
                maxLines: 1,
                overflow: TextOverflow.ellipsis,
                style: Theme.of(context).textTheme.titleLarge,
              ),
            ),
            const SizedBox(width: AppSpacing.x2),
            TextButton(
                onPressed: onOpenTimetable, child: const Text('عرض الجدول')),
          ]),
          const SizedBox(height: AppSpacing.x2),
          AppCard(
            child: Column(children: [
              _HomeLessonRow(
                label: 'الحصة الحالية',
                entry: data.current,
                empty: 'لا توجد حصة حالية',
                accent: AppColors.success,
              ),
              const Divider(height: AppSpacing.x4),
              _HomeLessonRow(
                label: 'الحصة التالية',
                entry: data.next,
                empty: 'لا توجد حصة قادمة',
                accent: AppColors.primary,
              ),
            ]),
          ),
          const SizedBox(height: AppSpacing.x4),
          Text('جدول اليوم', style: Theme.of(context).textTheme.titleMedium),
          const SizedBox(height: AppSpacing.x2),
          if (data.today.entries.isEmpty)
            const _CompactHomeEmpty(message: 'لا توجد حصص اليوم')
          else
            ...data.today.entries.map((entry) => Padding(
                padding: const EdgeInsets.only(bottom: AppSpacing.x2),
                child: LessonCard(entry: entry))),
        ]),
      );
}

class _HomeLessonRow extends StatelessWidget {
  const _HomeLessonRow({
    required this.label,
    required this.entry,
    required this.empty,
    required this.accent,
  });
  final String label;
  final TimetableEntryModel? entry;
  final String empty;
  final Color accent;
  @override
  Widget build(BuildContext context) => Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Container(
            width: 4,
            height: entry == null ? 42 : 64,
            decoration: BoxDecoration(
              color: accent,
              borderRadius: BorderRadius.circular(AppRadius.chip),
            ),
          ),
          const SizedBox(width: AppSpacing.x3),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(label,
                    style: Theme.of(context)
                        .textTheme
                        .labelMedium
                        ?.copyWith(color: AppColors.textSecondary)),
                const SizedBox(height: AppSpacing.x1),
                if (entry == null)
                  Text(empty, maxLines: 1, overflow: TextOverflow.ellipsis)
                else ...[
                  Text(entry!.subject,
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                      style: Theme.of(context).textTheme.titleSmall),
                  Text(
                    '${entry!.classroom} - ${entry!.section} • ${entry!.teacher}',
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                    style: Theme.of(context)
                        .textTheme
                        .bodySmall
                        ?.copyWith(color: AppColors.textSecondary),
                  ),
                  Text(
                    '${_time(entry!.period.startTime)} – ${_time(entry!.period.endTime)}',
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                    style: Theme.of(context)
                        .textTheme
                        .bodySmall
                        ?.copyWith(color: AppColors.textSecondary),
                  ),
                ],
              ],
            ),
          ),
        ],
      );
}

class _CompactHomeEmpty extends StatelessWidget {
  const _CompactHomeEmpty({required this.message});
  final String message;

  @override
  Widget build(BuildContext context) => Container(
        width: double.infinity,
        padding: const EdgeInsets.all(AppSpacing.x3),
        decoration: BoxDecoration(
          color: AppColors.surface,
          border: Border.all(color: AppColors.divider),
          borderRadius: BorderRadius.circular(AppRadius.card),
        ),
        child: Row(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const Icon(Icons.event_available_outlined,
                size: 18, color: AppColors.textSecondary),
            const SizedBox(width: AppSpacing.x2),
            Flexible(
              child: Text(
                message,
                maxLines: 2,
                overflow: TextOverflow.ellipsis,
                textAlign: TextAlign.center,
                style: Theme.of(context)
                    .textTheme
                    .bodySmall
                    ?.copyWith(color: AppColors.textSecondary),
              ),
            ),
          ],
        ),
      );
}

enum LessonEmphasis { current, next, neutral }

class LessonCard extends StatelessWidget {
  const LessonCard(
      {super.key, required this.entry, this.emphasis = LessonEmphasis.neutral});
  final TimetableEntryModel entry;
  final LessonEmphasis emphasis;
  @override
  Widget build(BuildContext context) {
    final accent = switch (emphasis) {
      LessonEmphasis.current => AppColors.success,
      LessonEmphasis.next => AppColors.primary,
      LessonEmphasis.neutral => AppColors.divider,
    };
    final stateLabel = switch (emphasis) {
      LessonEmphasis.current => 'الآن',
      LessonEmphasis.next => 'التالية',
      LessonEmphasis.neutral when entry.status == 'finished' => 'انتهت',
      LessonEmphasis.neutral => null,
    };
    return AppCard(
        child: Row(children: [
      Container(
          width: 4,
          height: 58,
          decoration: BoxDecoration(
              color: accent,
              borderRadius: BorderRadius.circular(AppRadius.chip))),
      const SizedBox(width: AppSpacing.x3),
      Expanded(
          child:
              Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Expanded(
            child: Text(entry.subject,
                style: Theme.of(context).textTheme.titleMedium,
                maxLines: 2,
                overflow: TextOverflow.ellipsis),
          ),
          if (stateLabel != null) ...[
            const SizedBox(width: AppSpacing.x2),
            Container(
              padding: const EdgeInsets.symmetric(
                  horizontal: AppSpacing.x2, vertical: 2),
              decoration: BoxDecoration(
                color: accent.withOpacity(.10),
                borderRadius: BorderRadius.circular(AppRadius.chip),
              ),
              child: Text(stateLabel,
                  style: Theme.of(context)
                      .textTheme
                      .labelSmall
                      ?.copyWith(color: accent)),
            ),
          ],
        ]),
        Text('${entry.classroom} - ${entry.section} • ${entry.teacher}',
            maxLines: 2,
            overflow: TextOverflow.ellipsis,
            style: Theme.of(context).textTheme.bodySmall),
        Text(
            '${_time(entry.period.startTime)} – ${_time(entry.period.endTime)}',
            style: Theme.of(context).textTheme.bodySmall),
      ])),
    ]));
  }
}

class BreakCard extends StatelessWidget {
  const BreakCard({super.key, required this.period});
  final TimetablePeriod period;
  @override
  Widget build(BuildContext context) => Container(
        padding: const EdgeInsets.all(AppSpacing.x3),
        decoration: BoxDecoration(
            color: AppColors.info.withOpacity(.08),
            borderRadius: BorderRadius.circular(AppRadius.card)),
        child: Row(children: [
          const Icon(Icons.local_cafe_outlined),
          const SizedBox(width: AppSpacing.x2),
          Expanded(
            child:
                Text(period.name, maxLines: 2, overflow: TextOverflow.ellipsis),
          ),
          const SizedBox(width: AppSpacing.x2),
          Flexible(
            child: Text('${_time(period.startTime)} – ${_time(period.endTime)}',
                maxLines: 1, overflow: TextOverflow.ellipsis),
          ),
        ]),
      );
}

class StudentTimetableScreen extends StatefulWidget {
  const StudentTimetableScreen(
      {super.key,
      required this.data,
      required this.onRefresh,
      this.onBack,
      this.historical = false});
  final StudentTimetableData data;
  final Future<void> Function() onRefresh;
  final VoidCallback? onBack;
  final bool historical;
  @override
  State<StudentTimetableScreen> createState() => _StudentTimetableScreenState();
}

class _StudentTimetableScreenState extends State<StudentTimetableScreen> {
  int tab = 0;
  int day = 0;
  static const dayNames = [
    'الأحد',
    'الاثنين',
    'الثلاثاء',
    'الأربعاء',
    'الخميس',
    'الجمعة',
    'السبت'
  ];

  @override
  void initState() {
    super.initState();
    day = _todayIndex();
  }

  @override
  void didUpdateWidget(covariant StudentTimetableScreen oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.data.week.weekStart != widget.data.week.weekStart ||
        day >= widget.data.week.days.length) {
      day = _todayIndex();
    }
  }

  int _todayIndex() {
    final index = widget.data.week.days.indexWhere(
      (item) => DateUtils.isSameDay(item.date, widget.data.today.date),
    );
    return index < 0 ? 0 : index;
  }

  bool get _notConfigured =>
      widget.data.today.periods.isEmpty &&
      widget.data.week.days.every((item) => item.entries.isEmpty);

  @override
  Widget build(BuildContext context) => RefreshIndicator(
        onRefresh: widget.onRefresh,
        child:
            ListView(padding: const EdgeInsets.all(AppSpacing.x4), children: [
          Row(children: [
            if (widget.onBack != null)
              IconButton(
                tooltip: 'رجوع',
                onPressed: widget.onBack,
                icon: const Icon(Icons.arrow_forward),
              ),
            Expanded(
              child: Text('جدولي',
                  style: Theme.of(context).textTheme.headlineMedium),
            ),
            if (widget.historical) const Chip(label: Text('عرض فقط')),
          ]),
          if (widget.historical) ...[
            const SizedBox(height: AppSpacing.x1),
            Text('جدول السنة الدراسية السابقة',
                style: Theme.of(context)
                    .textTheme
                    .bodySmall
                    ?.copyWith(color: AppColors.textSecondary)),
          ],
          const SizedBox(height: AppSpacing.x4),
          SegmentedButton<int>(segments: const [
            ButtonSegment(value: 0, label: Text('اليوم')),
            ButtonSegment(value: 1, label: Text('الأسبوع'))
          ], selected: {
            tab
          }, onSelectionChanged: (v) => setState(() => tab = v.first)),
          const SizedBox(height: AppSpacing.x4),
          if (_notConfigured)
            const AppEmptyState(
                message: 'لم يتم إعداد الجدول الدراسي لهذا السياق بعد')
          else if (tab == 0 && widget.data.today.entries.isEmpty)
            const AppEmptyState(message: 'لا توجد حصص اليوم')
          else if (tab == 0)
            ..._timeline(widget.data.today.periods, widget.data.today.entries)
          else ...[
            Wrap(
              spacing: AppSpacing.x2,
              runSpacing: AppSpacing.x2,
              children: [
                for (var i = 0; i < widget.data.week.days.length; i++)
                  Builder(builder: (context) {
                    final item = widget.data.week.days[i];
                    final isToday =
                        DateUtils.isSameDay(item.date, widget.data.today.date);
                    return ChoiceChip(
                      key: ValueKey('week-day-${item.weekday}'),
                      label: Text(
                        '${dayNames[item.weekday]}${isToday ? ' • اليوم' : ''}',
                      ),
                      selected: day == i,
                      onSelected: (_) => setState(() => day = i),
                    );
                  }),
              ],
            ),
            const SizedBox(height: AppSpacing.x4),
            if (widget.data.week.days.isEmpty ||
                widget.data.week.days[day].entries.isEmpty)
              const AppEmptyState(message: 'لا توجد حصص في هذا اليوم')
            else
              ...widget.data.week.days[day].entries.map((entry) => Padding(
                  padding: const EdgeInsets.only(bottom: AppSpacing.x2),
                  child: LessonCard(entry: entry))),
          ],
        ]),
      );

  List<Widget> _timeline(
      List<TimetablePeriod> periods, List<TimetableEntryModel> entries) {
    final byPeriod = {for (final entry in entries) entry.period.id: entry};
    final currentId = widget.data.current?.id;
    final nextId = widget.data.next?.id;
    return periods
        .map((period) => Padding(
            padding: const EdgeInsets.only(bottom: AppSpacing.x2),
            child: period.isBreak
                ? BreakCard(period: period)
                : byPeriod[period.id] == null
                    ? AppCard(child: Text('${period.name} • لا توجد حصة'))
                    : LessonCard(
                        entry: byPeriod[period.id]!,
                        emphasis: byPeriod[period.id]!.id == currentId
                            ? LessonEmphasis.current
                            : byPeriod[period.id]!.id == nextId
                                ? LessonEmphasis.next
                                : LessonEmphasis.neutral,
                      )))
        .toList();
  }
}

String _time(String value) => value.length >= 5 ? value.substring(0, 5) : value;
