import 'package:flutter/material.dart';

import '../../../../core/design_system/components.dart';
import '../../student/timetable/domain/timetable_models.dart';
import '../domain/parent_attendance_models.dart';
import 'parent_m2_controller.dart';

class ParentTimetableScreen extends StatefulWidget {
  const ParentTimetableScreen({
    super.key,
    required this.state,
    required this.childName,
    required this.historical,
    required this.onRefresh,
  });
  final ParentTimetableState state;
  final String childName;
  final bool historical;
  final Future<void> Function() onRefresh;

  @override
  State<ParentTimetableScreen> createState() => _ParentTimetableScreenState();
}

class _ParentTimetableScreenState extends State<ParentTimetableScreen> {
  DateTime? selectedDate;

  @override
  Widget build(BuildContext context) {
    final state = widget.state;
    if (state is ParentTimetableLoading) return const _Loading();
    if (state is ParentTimetableFailure) {
      return _Failure(message: state.message, onRetry: widget.onRefresh);
    }
    final ready = state as ParentTimetableReady;
    final days = ready.data.week.days;
    final selected = days.where((day) => day.date == selectedDate).firstOrNull ??
        (days.isEmpty ? null : days.first);
    return RefreshIndicator(
      onRefresh: widget.onRefresh,
      child: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          _Header(title: 'جدول ${widget.childName}', historical: widget.historical),
          if (ready.data.offline) const OfflineCacheBanner(),
          if (ready.refreshing) const LinearProgressIndicator(),
          if (days.isEmpty)
            const _Empty(icon: Icons.calendar_month, text: 'لا توجد حصص في هذا الأسبوع')
          else ...[
            SingleChildScrollView(
              scrollDirection: Axis.horizontal,
              child: Row(
                children: [
                  for (final day in days)
                    Padding(
                      padding: const EdgeInsetsDirectional.only(end: 8),
                      child: ChoiceChip(
                        label: Text('${_weekday(day.weekday)} ${day.date.day}'),
                        selected: selected?.date == day.date,
                        onSelected: (_) => setState(() => selectedDate = day.date),
                      ),
                    ),
                ],
              ),
            ),
            const SizedBox(height: 12),
            if (selected!.entries.isEmpty)
              const _Empty(icon: Icons.event_available, text: 'لا توجد حصص في هذا اليوم')
            else
              for (final entry in selected.entries) _TimetableCard(entry: entry),
          ],
        ],
      ),
    );
  }
}

class ParentAttendanceScreen extends StatelessWidget {
  const ParentAttendanceScreen({
    super.key,
    required this.state,
    required this.childName,
    required this.historical,
    required this.onRefresh,
  });
  final ParentAttendanceState state;
  final String childName;
  final bool historical;
  final Future<void> Function() onRefresh;

  @override
  Widget build(BuildContext context) {
    if (state is ParentAttendanceLoading) return const _Loading();
    if (state case ParentAttendanceFailure(:final message)) {
      return _Failure(message: message, onRetry: onRefresh);
    }
    final ready = state as ParentAttendanceReady;
    final data = ready.data;
    final percentage = data.attendancePercentage.toStringAsFixed(
        data.attendancePercentage % 1 == 0 ? 0 : 1);
    return RefreshIndicator(
      onRefresh: onRefresh,
      child: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          _Header(title: 'حضور $childName', historical: historical),
          if (data.offline) const OfflineCacheBanner(),
          if (ready.refreshing) const LinearProgressIndicator(),
          Card(
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                children: [
                  Text('$percentage%', style: Theme.of(context).textTheme.headlineMedium),
                  const Text('نسبة الحضور'),
                  const SizedBox(height: 12),
                  Wrap(spacing: 16, runSpacing: 8, children: [
                    Text('حاضر ${data.presentCount}'),
                    Text('غائب ${data.absentCount}'),
                    Text('متأخر ${data.lateCount}'),
                    Text('بعذر ${data.excusedCount}'),
                  ]),
                ],
              ),
            ),
          ),
          if (data.records.isEmpty)
            const _Empty(icon: Icons.fact_check_outlined, text: 'لا توجد سجلات حضور')
          else
            for (final record in data.records)
              Card(
                child: ListTile(
                  leading: _StatusIcon(status: record.status),
                  title: Text(record.status.arabicLabel),
                  subtitle: Text([
                    '${record.date.year}/${record.date.month.toString().padLeft(2, '0')}/${record.date.day.toString().padLeft(2, '0')}',
                    if (record.termName.isNotEmpty) record.termName,
                    if (record.note.isNotEmpty) record.note,
                  ].join(' • ')),
                ),
              ),
        ],
      ),
    );
  }
}

class _Header extends StatelessWidget {
  const _Header({required this.title, required this.historical});
  final String title;
  final bool historical;
  @override
  Widget build(BuildContext context) => Padding(
        padding: const EdgeInsets.only(bottom: 12),
        child: Row(children: [
          Expanded(child: Text(title, style: Theme.of(context).textTheme.headlineSmall)),
          if (historical) const Chip(label: Text('سياق تاريخي — للقراءة فقط')),
        ]),
      );
}

class _TimetableCard extends StatelessWidget {
  const _TimetableCard({required this.entry});
  final TimetableEntryModel entry;
  @override
  Widget build(BuildContext context) => Card(
        child: ListTile(
          leading: const Icon(Icons.menu_book_outlined),
          title: Text(entry.subject),
          subtitle: Text([
            entry.period.name,
            '${_shortTime(entry.period.startTime)} - ${_shortTime(entry.period.endTime)}',
            if (entry.teacher.isNotEmpty) entry.teacher,
            if (entry.classroom.isNotEmpty) '${entry.classroom} / ${entry.section}',
          ].join(' • ')),
        ),
      );
}

class _StatusIcon extends StatelessWidget {
  const _StatusIcon({required this.status});
  final ParentAttendanceStatus status;
  @override
  Widget build(BuildContext context) {
    final color = switch (status) {
      ParentAttendanceStatus.present => Colors.green,
      ParentAttendanceStatus.absent => Colors.red,
      ParentAttendanceStatus.late => Colors.orange,
      ParentAttendanceStatus.excused => Colors.blue,
    };
    return CircleAvatar(
      backgroundColor: color.withOpacity(.12),
      child: Icon(Icons.circle, size: 12, color: color),
    );
  }
}

class _Loading extends StatelessWidget {
  const _Loading();
  @override
  Widget build(BuildContext context) => const Center(child: CircularProgressIndicator());
}

class _Failure extends StatelessWidget {
  const _Failure({required this.message, required this.onRetry});
  final String message;
  final Future<void> Function() onRetry;
  @override
  Widget build(BuildContext context) => Center(
        child: Column(mainAxisSize: MainAxisSize.min, children: [
          Text(message, textAlign: TextAlign.center),
          const SizedBox(height: 12),
          FilledButton(onPressed: onRetry, child: const Text('إعادة المحاولة')),
        ]),
      );
}

class _Empty extends StatelessWidget {
  const _Empty({required this.icon, required this.text});
  final IconData icon;
  final String text;
  @override
  Widget build(BuildContext context) => Padding(
        padding: const EdgeInsets.symmetric(vertical: 40),
        child: Column(children: [Icon(icon, size: 48), const SizedBox(height: 12), Text(text)]),
      );
}

String _weekday(int value) => const {
      0: 'الأحد', 1: 'الاثنين', 2: 'الثلاثاء', 3: 'الأربعاء',
      4: 'الخميس', 5: 'الجمعة', 6: 'السبت',
    }[value] ?? '';

String _shortTime(String value) => value.length >= 5 ? value.substring(0, 5) : value;
