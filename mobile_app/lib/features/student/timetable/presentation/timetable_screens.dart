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
      this.onRefresh});
  final StudentTimetableData data;
  final String studentName;
  final String schoolName;
  final String academicYear;
  final VoidCallback onOpenTimetable;
  final Future<void> Function()? onRefresh;
  @override
  Widget build(BuildContext context) => RefreshIndicator(
        onRefresh: onRefresh ?? () async {},
        child:
            ListView(padding: const EdgeInsets.all(AppSpacing.x4), children: [
          Text('مرحبًا، ${studentName.isEmpty ? 'طالبنا' : studentName}',
              style: Theme.of(context).textTheme.headlineMedium),
          const SizedBox(height: AppSpacing.x1),
          Text('$schoolName • $academicYear',
              style: Theme.of(context).textTheme.bodySmall),
          const SizedBox(height: AppSpacing.x6),
          _LessonSection(
              title: 'الحصة الحالية',
              entry: data.current,
              empty: 'لا توجد حصة حالية'),
          const SizedBox(height: AppSpacing.x4),
          _LessonSection(
              title: 'الحصة التالية',
              entry: data.next,
              empty: 'لا توجد حصة قادمة'),
          const SizedBox(height: AppSpacing.x6),
          Row(mainAxisAlignment: MainAxisAlignment.spaceBetween, children: [
            Text('حصصي اليوم', style: Theme.of(context).textTheme.titleLarge),
            TextButton(
                onPressed: onOpenTimetable, child: const Text('عرض الجدول')),
          ]),
          const SizedBox(height: AppSpacing.x2),
          if (data.today.entries.isEmpty)
            const AppEmptyState(message: 'لا توجد حصص اليوم')
          else
            ...data.today.entries.map((entry) => Padding(
                padding: const EdgeInsets.only(bottom: AppSpacing.x2),
                child: LessonCard(entry: entry))),
        ]),
      );
}

class _LessonSection extends StatelessWidget {
  const _LessonSection(
      {required this.title, required this.entry, required this.empty});
  final String title;
  final TimetableEntryModel? entry;
  final String empty;
  @override
  Widget build(BuildContext context) =>
      Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        Text(title, style: Theme.of(context).textTheme.titleLarge),
        const SizedBox(height: AppSpacing.x2),
        if (entry == null)
          AppCard(child: Text(empty))
        else
          LessonCard(
            entry: entry!,
            emphasis: title == 'الحصة الحالية'
                ? LessonEmphasis.current
                : LessonEmphasis.next,
          ),
      ]);
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
        Text(entry.subject,
            style: Theme.of(context).textTheme.titleMedium,
            maxLines: 2,
            overflow: TextOverflow.ellipsis),
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
          Expanded(child: Text(period.name)),
          Text('${_time(period.startTime)} – ${_time(period.endTime)}')
        ]),
      );
}

class StudentTimetableScreen extends StatefulWidget {
  const StudentTimetableScreen(
      {super.key, required this.data, required this.onRefresh});
  final StudentTimetableData data;
  final Future<void> Function() onRefresh;
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
  Widget build(BuildContext context) => RefreshIndicator(
        onRefresh: widget.onRefresh,
        child:
            ListView(padding: const EdgeInsets.all(AppSpacing.x4), children: [
          Text('جدولي', style: Theme.of(context).textTheme.headlineMedium),
          const SizedBox(height: AppSpacing.x4),
          SegmentedButton<int>(segments: const [
            ButtonSegment(value: 0, label: Text('اليوم')),
            ButtonSegment(value: 1, label: Text('الأسبوع'))
          ], selected: {
            tab
          }, onSelectionChanged: (v) => setState(() => tab = v.first)),
          const SizedBox(height: AppSpacing.x4),
          if (tab == 0)
            ..._timeline(widget.data.today.periods, widget.data.today.entries)
          else ...[
            SizedBox(
                height: 48,
                child: ListView.separated(
                    scrollDirection: Axis.horizontal,
                    itemCount: widget.data.week.days.length,
                    separatorBuilder: (_, __) =>
                        const SizedBox(width: AppSpacing.x2),
                    itemBuilder: (_, i) => ChoiceChip(
                        label: Text(dayNames[widget.data.week.days[i].weekday]),
                        selected: day == i,
                        onSelected: (_) => setState(() => day = i)))),
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
    return periods
        .map((period) => Padding(
            padding: const EdgeInsets.only(bottom: AppSpacing.x2),
            child: period.isBreak
                ? BreakCard(period: period)
                : byPeriod[period.id] == null
                    ? AppCard(child: Text('${period.name} • لا توجد حصة'))
                    : LessonCard(entry: byPeriod[period.id]!)))
        .toList();
  }
}

String _time(String value) => value.length >= 5 ? value.substring(0, 5) : value;
