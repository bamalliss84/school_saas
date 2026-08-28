import 'package:flutter/material.dart';

import '../../../../core/design_system/tokens.dart';
import '../../attendance/presentation/attendance_controller.dart';
import '../../communications/presentation/communications_controller.dart';
import '../../homework/domain/homework_models.dart';
import '../../homework/presentation/homework_controller.dart';
import '../../results/presentation/results_controller.dart';
import '../../timetable/domain/timetable_models.dart';
import '../../timetable/presentation/timetable_controller.dart';

class SmartStudentHome extends StatelessWidget {
  const SmartStudentHome({
    super.key,
    required this.timetable,
    required this.homework,
    required this.results,
    required this.attendance,
    required this.communications,
    required this.historical,
    required this.onRefresh,
    required this.onTimetable,
    required this.onHomework,
    required this.onResults,
    required this.onAttendance,
    required this.onCommunications,
    required this.onUpdates,
  });

  final TimetableState timetable;
  final HomeworkState homework;
  final ResultsState results;
  final AttendanceState? attendance;
  final CommunicationsState communications;
  final bool historical;
  final Future<void> Function() onRefresh;
  final VoidCallback onTimetable,
      onHomework,
      onResults,
      onAttendance,
      onCommunications,
      onUpdates;

  @override
  Widget build(BuildContext context) {
    final model = _Model.fromStates(
      timetable,
      homework,
      results,
      attendance,
      communications,
      historical,
      _Destinations(onTimetable, onHomework, onResults, onAttendance,
          onCommunications, onUpdates),
    );
    final waiting = homework is HomeworkLoading ||
        timetable is TimetableLoading ||
        results is ResultsLoading ||
        communications is CommunicationsLoading ||
        attendance is AttendanceLoading;
    final incomplete = homework is HomeworkFailure ||
        timetable is TimetableFailure ||
        results is ResultsFailure ||
        communications is CommunicationsFailure ||
        attendance is AttendanceFailure ||
        attendance is AttendanceOfflineEmpty;
    return RefreshIndicator(
      onRefresh: onRefresh,
      child: ListView(
        physics: const AlwaysScrollableScrollPhysics(),
        padding: const EdgeInsets.fromLTRB(16, 12, 16, 32),
        children: [
          if (!historical) ...[
            const _Hero(historical: false),
            const SizedBox(height: 24),
            const _Title('يحتاج انتباهك'),
            const SizedBox(height: 8),
            if (model.attention.isEmpty)
              _ClearState(
                  historical: false,
                  waiting: waiting,
                  incomplete: incomplete)
            else
              ...model.attention.map((item) => _ActionTile(item)),
          ],
          if (model.metrics.isNotEmpty) ...[
            if (!historical) const SizedBox(height: 20),
            _Title(historical ? 'ملخص السجل الدراسي' : 'ملخصك الدراسي'),
            const SizedBox(height: 8),
            Wrap(
              spacing: 8,
              runSpacing: 8,
              children: model.metrics.map((item) => _MetricTile(item)).toList(),
            ),
          ] else if (homework is HomeworkLoading ||
              attendance is AttendanceLoading ||
              communications is CommunicationsLoading) ...[
            if (!historical) const SizedBox(height: 20),
            _Title(historical ? 'ملخص السجل الدراسي' : 'ملخصك الدراسي'),
            const SizedBox(height: 8),
            const _SectionLoading(label: 'جارٍ تحميل الملخص'),
          ],
          const SizedBox(height: 24),
          _Title('يومي الدراسي', action: onTimetable),
          const SizedBox(height: 8),
          _SchoolDay(timetable, historical, onTimetable),
          if (model.upcoming.isNotEmpty) ...[
            const SizedBox(height: 24),
            const _Title('القادم'),
            const SizedBox(height: 8),
            _TimelineGroup(model.upcoming),
          ] else if (!historical && homework is HomeworkLoading) ...[
            const SizedBox(height: 24),
            const _Title('القادم'),
            const SizedBox(height: 8),
            const _SectionLoading(label: 'جارٍ تحميل المواعيد القادمة'),
          ],
          if (model.updates.isNotEmpty) ...[
            const SizedBox(height: 24),
            _Title('آخر التحديثات', action: onUpdates),
            const SizedBox(height: 8),
            _UpdatesGroup(model.updates),
          ] else if (communications is CommunicationsLoading ||
              results is ResultsLoading) ...[
            const SizedBox(height: 24),
            const _Title('آخر التحديثات'),
            const SizedBox(height: 8),
            const _SectionLoading(label: 'جارٍ تحميل التحديثات'),
          ],
        ],
      ),
    );
  }
}

class _Model {
  const _Model(this.attention, this.metrics, this.upcoming, this.updates);
  final List<_Item> attention, upcoming, updates;
  final List<_Metric> metrics;

  factory _Model.fromStates(
      TimetableState timetable,
      HomeworkState homework,
      ResultsState results,
      AttendanceState? attendance,
      CommunicationsState communications,
      bool historical,
      _Destinations go) {
    final now = DateTime.now();
    final timetableData =
        timetable is TimetableReady ? timetable.data : null;
    final ranked = <({int priority, _Item item})>[];
    final upcoming = <_Item>[];
    final updates = <_Item>[];
    final metrics = <_Metric>[];
    if (homework is HomeworkReady) {
      final pending = homework.list.items.where(_pending).toList()
        ..sort((a, b) => a.dueDate.compareTo(b.dueDate));
      if (!historical) {
        for (final item in pending) {
          final overdue = item.completionStatus == 'overdue' ||
              item.dueDate.isBefore(_dateOnly(now));
          final today = _sameDay(item.dueDate, now);
          if (overdue || today) {
            ranked.add((
              priority: overdue ? 0 : 1,
              item: _Item(
                overdue ? Icons.assignment_late_outlined : Icons.today_outlined,
                overdue ? AppColors.error : AppColors.warning,
                overdue ? 'واجب متأخر: ${item.title}' : 'واجب مستحق اليوم',
                '${item.subject} • ${_date(item.dueDate)}',
                go.homework,
              ),
            ));
          }
        }
        upcoming.addAll(pending
            .where((item) => !item.dueDate.isBefore(_dateOnly(now)))
            .take(3)
            .map((item) => _Item(Icons.assignment_outlined, AppColors.primary,
                item.title, '${item.subject} • ${_date(item.dueDate)}', go.homework)));
      }
      if (!historical) {
        metrics.add(_Metric(Icons.assignment_outlined, AppColors.info,
            'الواجبات', '${pending.length} مستحقة', go.homework));
      }
    }
    if (!historical && timetableData?.current != null) {
      ranked.add((
        priority: 2,
        item: _Item(Icons.play_circle_outline, AppColors.success,
            'حصتك الآن: ${timetableData!.current!.subject}', _period(timetableData.current!), go.timetable),
      ));
    }
    if (communications is CommunicationsReady) {
      final data = communications.data;
      if (!historical && data.badges.total > 0) {
        ranked.add((
          priority: 3,
          item: _Item(Icons.notifications_none, AppColors.info,
              'لديك ${data.badges.total} تحديثات غير مقروءة', 'إشعارات ورسائل مدرسية', go.communications),
        ));
      }
      if (data.badges.total > 0) {
        metrics.add(_Metric(Icons.mark_chat_unread_outlined, const Color(0xff7047d7),
            'التحديثات', '${data.badges.total} جديدة', go.communications));
      }
      updates.addAll(data.notifications
          .where((item) => !item.isRead)
          .take(2)
          .map((item) => _Item(Icons.notifications_outlined, AppColors.info,
              item.title, item.body, go.updates)));
      final announcements = data.announcements.toList()
        ..sort((a, b) => (b.publishedAt ?? DateTime(0))
            .compareTo(a.publishedAt ?? DateTime(0)));
      updates.addAll(announcements.take(2).map((item) => _Item(
          Icons.campaign_outlined,
          AppColors.primary,
          item.title,
          item.publishedAt == null ? 'إعلان مدرسي' : _date(item.publishedAt!),
          go.updates)));
    }
    if (results is ResultsReady) {
      final published = results.data.items.where((item) => item.isPublished).toList()
        ..sort((a, b) => (b.publishedAt ?? b.examDate)
            .compareTo(a.publishedAt ?? a.examDate));
      updates.addAll(published.take(2).map((item) => _Item(
          Icons.workspace_premium_outlined,
          AppColors.success,
          'نتيجة ${item.subject}',
          '${item.examTitle} • ${item.scoreLabel}',
          go.results)));
    }
    if (attendance is AttendanceReady && attendance.summary.total > 0) {
      metrics.add(_Metric(Icons.how_to_reg_outlined, AppColors.success,
          'الحضور', '${attendance.summary.percentage.toStringAsFixed(0)}%', go.attendance));
    }
    ranked.sort((a, b) => a.priority.compareTo(b.priority));
    return _Model(
      historical ? const [] : ranked.take(3).map((value) => value.item).toList(),
      metrics.take(3).toList(),
      historical ? const [] : upcoming,
      updates.take(3).toList(),
    );
  }
}

class _Destinations {
  const _Destinations(this.timetable, this.homework, this.results,
      this.attendance, this.communications, this.updates);
  final VoidCallback timetable,
      homework,
      results,
      attendance,
      communications,
      updates;
}

class _Item {
  const _Item(this.icon, this.color, this.title, this.subtitle, this.onTap);
  final IconData icon;
  final Color color;
  final String title, subtitle;
  final VoidCallback onTap;
}

class _Metric {
  const _Metric(this.icon, this.color, this.label, this.value, this.onTap);
  final IconData icon;
  final Color color;
  final String label, value;
  final VoidCallback onTap;
}

class _Hero extends StatelessWidget {
  const _Hero({required this.historical});
  final bool historical;
  @override
  Widget build(BuildContext context) => Container(
        width: double.infinity,
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
        decoration: BoxDecoration(
          gradient: LinearGradient(
            colors: historical
                ? const [Color(0xfff4efff), Color(0xffeee7ff)]
                : const [Color(0xfff8f7ff), Color(0xffeef2ff)],
          ),
          borderRadius: BorderRadius.circular(20),
          border: Border.all(
              color: historical
                  ? const Color(0xffd9cbff)
                  : const Color(0xffdfe3ff)),
          boxShadow: const [
            BoxShadow(
                color: Color(0x0c3157d5), blurRadius: 16, offset: Offset(0, 6)),
          ],
        ),
        child: historical
            ? Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
                Container(
                    width: 44,
                    height: 44,
                    decoration: const BoxDecoration(
                        color: Color(0x157047d7), shape: BoxShape.circle),
                    child: const Icon(Icons.hourglass_bottom_rounded,
                        color: Color(0xff7047d7))),
                const SizedBox(width: 12),
                Expanded(
                    child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                      Text('وضع تاريخي • للعرض فقط',
                          style: Theme.of(context)
                              .textTheme
                              .labelLarge
                              ?.copyWith(color: const Color(0xff7047d7))),
                      const SizedBox(height: 4),
                      Text('سجل أكاديمي سابق',
                          maxLines: 2,
                          overflow: TextOverflow.ellipsis,
                          style: Theme.of(context)
                              .textTheme
                              .titleLarge
                              ?.copyWith(fontWeight: FontWeight.w700)),
                    ])),
              ])
            : Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                Text(
                    '${_greeting(DateTime.now())} 👋',
                    maxLines: 2,
                    overflow: TextOverflow.ellipsis,
                    style: Theme.of(context)
                        .textTheme
                        .headlineSmall
                        ?.copyWith(fontWeight: FontWeight.w700)),
                const SizedBox(height: 3),
                Text('ملخص يومك الدراسي',
                    style: Theme.of(context)
                        .textTheme
                        .bodyMedium
                        ?.copyWith(color: AppColors.textSecondary)),
              ]),
      );
}

class _Title extends StatelessWidget {
  const _Title(this.text, {this.action});
  final String text;
  final VoidCallback? action;
  @override
  Widget build(BuildContext context) => Row(children: [
        Expanded(child: Text(text, style: Theme.of(context).textTheme.titleLarge)),
        if (action != null) TextButton(onPressed: action, child: Text(text == 'يومي الدراسي' ? 'عرض الجدول' : 'عرض الكل')),
      ]);
}

class _ClearState extends StatelessWidget {
  const _ClearState(
      {required this.historical,
      required this.waiting,
      required this.incomplete});
  final bool historical, waiting, incomplete;
  @override
  Widget build(BuildContext context) {
    final title = historical
        ? 'سياق تاريخي للعرض فقط'
        : waiting
            ? 'جارٍ تجميع ملخصك'
            : incomplete
                ? 'بعض الملخصات غير متاحة حاليًا'
                : 'أمورك تمام اليوم ✓';
    final subtitle = historical
        ? 'لن تظهر مهام آنية أو إجراءات كتابة'
        : waiting
            ? 'ستظهر الأولويات فور جاهزيتها'
            : incomplete
                ? 'اسحب للتحديث عند عودة الاتصال'
                : 'لا توجد مهام عاجلة';
    final icon = waiting
        ? Icons.sync
        : incomplete
            ? Icons.info_outline
            : historical
                ? Icons.history
                : Icons.check_circle_outline;
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 18, vertical: 20),
      decoration: BoxDecoration(
          gradient: const LinearGradient(
              colors: [Color(0xfff7fcf8), Color(0xffedf9f1)]),
          border: Border.all(color: const Color(0xffccebd7)),
          borderRadius: BorderRadius.circular(20),
          boxShadow: const [
            BoxShadow(color: Color(0x0c197a55), blurRadius: 14, offset: Offset(0, 5))
          ]),
      child: Row(children: [
        Container(
            width: 50,
            height: 50,
            decoration: const BoxDecoration(
                color: Color(0xffdff5e7), shape: BoxShape.circle),
            child: Icon(icon, size: 28, color: AppColors.success)),
        const SizedBox(width: 14),
        Expanded(
            child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
              Text(title,
                  style: Theme.of(context)
                      .textTheme
                      .titleMedium
                      ?.copyWith(
                          color: AppColors.success,
                          fontWeight: FontWeight.w700)),
              const SizedBox(height: 3),
              Text(subtitle,
                  style: const TextStyle(color: AppColors.textSecondary)),
            ])),
      ]),
    );
  }
}

class _ActionTile extends StatelessWidget {
  const _ActionTile(this.item); final _Item item;
  @override Widget build(BuildContext context) => Padding(padding: const EdgeInsets.only(bottom: 9), child: DecoratedBox(decoration: BoxDecoration(color: item.color.withOpacity(.065), borderRadius: BorderRadius.circular(18), border: Border.all(color: item.color.withOpacity(.2)), boxShadow: [BoxShadow(color: item.color.withOpacity(.06), blurRadius: 12, offset: const Offset(0, 4))]), child: Material(color: Colors.transparent, child: InkWell(onTap: item.onTap, borderRadius: BorderRadius.circular(18), child: Padding(padding: const EdgeInsets.all(13), child: Row(crossAxisAlignment: CrossAxisAlignment.center, children: [Container(width: 42, height: 42, decoration: BoxDecoration(color: item.color.withOpacity(.12), shape: BoxShape.circle), child: Icon(item.icon, size: 22, color: item.color)), const SizedBox(width: 12), Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [Text(item.title, maxLines: 2, overflow: TextOverflow.ellipsis, style: Theme.of(context).textTheme.titleSmall?.copyWith(fontWeight: FontWeight.w700)), const SizedBox(height: 3), Text(item.subtitle, maxLines: 2, overflow: TextOverflow.ellipsis, style: Theme.of(context).textTheme.bodySmall?.copyWith(color: AppColors.textSecondary))])), _Chevron(color: item.color)]))))));
}

class _MetricTile extends StatelessWidget {
  const _MetricTile(this.item);

  final _Metric item;

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      width: 104,
      child: DecoratedBox(
        decoration: BoxDecoration(
          gradient: LinearGradient(
            begin: Alignment.topCenter,
            end: Alignment.bottomCenter,
            colors: [
              AppColors.surface,
              item.color.withOpacity(.055),
            ],
          ),
          border: Border.all(color: item.color.withOpacity(.18)),
          borderRadius: BorderRadius.circular(18),
          boxShadow: const [
            BoxShadow(
              color: Color(0x0a182230),
              blurRadius: 10,
              offset: Offset(0, 4),
            ),
          ],
        ),
        child: Material(
          color: Colors.transparent,
          child: InkWell(
            onTap: item.onTap,
            borderRadius: BorderRadius.circular(18),
            child: Padding(
              padding: const EdgeInsets.all(12),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Container(
                    width: 34,
                    height: 34,
                    decoration: BoxDecoration(
                      color: item.color.withOpacity(.11),
                      shape: BoxShape.circle,
                    ),
                    child: Icon(item.icon, size: 19, color: item.color),
                  ),
                  const SizedBox(height: 8),
                  Text(
                    item.label,
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                    style: Theme.of(context)
                        .textTheme
                        .bodySmall
                        ?.copyWith(color: AppColors.textSecondary),
                  ),
                  const SizedBox(height: 2),
                  Text(
                    item.value,
                    maxLines: 2,
                    overflow: TextOverflow.ellipsis,
                    style: Theme.of(context).textTheme.titleSmall?.copyWith(
                          color: item.color,
                          fontWeight: FontWeight.w700,
                        ),
                  ),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }
}

class _SchoolDay extends StatelessWidget {
  const _SchoolDay(this.data, this.historical, this.onTap);
  final TimetableState data;
  final bool historical;
  final VoidCallback onTap;
  @override Widget build(BuildContext context) {
    if (data is TimetableLoading) {
      return const _SectionLoading(label: 'جارٍ تحميل يومك الدراسي');
    }
    if (data is TimetableFailure) {
      return _SimpleState(Icons.info_outline,
          'تعذر تحميل الجدول حاليًا', onTap);
    }
    final timetable = (data as TimetableReady).data;
    if (historical) return _SimpleState(Icons.history, timetable.today.entries.isEmpty ? 'لا يوجد جدول محفوظ لهذا السياق' : 'الجدول المحفوظ متاح للعرض فقط', onTap);
    if (timetable.current == null && timetable.next == null) return _SimpleState(timetable.today.entries.isEmpty ? Icons.event_busy_outlined : Icons.task_alt, timetable.today.entries.isEmpty ? 'لا توجد حصص مجدولة اليوم' : 'انتهى يومك الدراسي', onTap);
    return DecoratedBox(
        decoration: BoxDecoration(
            color: AppColors.surface,
            border: Border.all(color: AppColors.divider),
            borderRadius: BorderRadius.circular(18),
            boxShadow: const [
              BoxShadow(
                  color: Color(0x0a182230),
                  blurRadius: 12,
                  offset: Offset(0, 4))
            ]),
        child: Padding(
            padding: const EdgeInsets.all(14),
            child: Column(children: [
              if (timetable.current != null)
                _Lesson('الآن', timetable.current!, AppColors.success,
                    Icons.menu_book_rounded),
              if (timetable.current != null && timetable.next != null)
                const Divider(height: 24),
              if (timetable.next != null)
                _Lesson('التالي', timetable.next!, AppColors.primary,
                    Icons.auto_stories_rounded),
            ])));
  }
}

class _SectionLoading extends StatelessWidget {
  const _SectionLoading({required this.label});
  final String label;
  @override
  Widget build(BuildContext context) => Container(
      width: double.infinity,
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
          color: AppColors.surface,
          borderRadius: BorderRadius.circular(18),
          border: Border.all(color: AppColors.divider)),
      child: Row(children: [
        const SizedBox(
            width: 18,
            height: 18,
            child: CircularProgressIndicator(strokeWidth: 2)),
        const SizedBox(width: 12),
        Expanded(
            child: Text(label,
                style: Theme.of(context)
                    .textTheme
                    .bodyMedium
                    ?.copyWith(color: AppColors.textSecondary))),
      ]));
}

class _Lesson extends StatelessWidget {
  const _Lesson(this.label, this.entry, this.color, this.icon);
  final String label;
  final TimetableEntryModel entry;
  final Color color;
  final IconData icon;
  @override
  Widget build(BuildContext context) => Row(
          crossAxisAlignment: CrossAxisAlignment.center,
          children: [
            Container(
                width: 40,
                height: 40,
                decoration: BoxDecoration(
                    color: color.withOpacity(.1), shape: BoxShape.circle),
                child: Icon(icon, size: 21, color: color)),
            const SizedBox(width: 11),
            Container(
                width: 4,
                height: 54,
                decoration: BoxDecoration(
                    color: color, borderRadius: BorderRadius.circular(4))),
            const SizedBox(width: 11),
            Expanded(
                child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                  Text(label,
                      style: Theme.of(context)
                          .textTheme
                          .labelMedium
                          ?.copyWith(color: color, fontWeight: FontWeight.w700)),
                  Text(entry.subject,
                      maxLines: 2,
                      overflow: TextOverflow.ellipsis,
                      style: Theme.of(context)
                          .textTheme
                          .titleMedium
                          ?.copyWith(fontWeight: FontWeight.w700)),
                  Text(_period(entry),
                      style: Theme.of(context)
                          .textTheme
                          .bodySmall
                          ?.copyWith(color: AppColors.textSecondary)),
                ])),
          ]);
}
class _SimpleState extends StatelessWidget { const _SimpleState(this.icon, this.text, this.onTap); final IconData icon; final String text; final VoidCallback onTap; @override Widget build(BuildContext context) => Material(color: AppColors.surface, borderRadius: BorderRadius.circular(16), child: InkWell(onTap: onTap, child: Padding(padding: const EdgeInsets.all(16), child: Row(children: [Icon(icon, color: AppColors.textSecondary), const SizedBox(width: 12), Expanded(child: Text(text, maxLines: 3, overflow: TextOverflow.ellipsis))])))); }
class _TimelineGroup extends StatelessWidget {
  const _TimelineGroup(this.items);
  final List<_Item> items;
  @override
  Widget build(BuildContext context) => DecoratedBox(
      decoration: BoxDecoration(
          color: AppColors.surface,
          borderRadius: BorderRadius.circular(18),
          border: Border.all(color: AppColors.divider)),
      child: Column(
          children: List.generate(items.length, (index) => Column(children: [
                _TimelineTile(items[index]),
                if (index != items.length - 1)
                  const Divider(height: 1, indent: 58),
              ]))));
}

class _TimelineTile extends StatelessWidget {
  const _TimelineTile(this.item);
  final _Item item;
  @override
  Widget build(BuildContext context) => InkWell(
      onTap: item.onTap,
      child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 11),
          child: Row(crossAxisAlignment: CrossAxisAlignment.center, children: [
            Container(
                width: 36,
                height: 36,
                decoration: BoxDecoration(
                    color: item.color.withOpacity(.09), shape: BoxShape.circle),
                child: Icon(item.icon, size: 19, color: item.color)),
            const SizedBox(width: 11),
            Expanded(
                child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                  Text(item.title,
                      maxLines: 2,
                      overflow: TextOverflow.ellipsis,
                      style: Theme.of(context)
                          .textTheme
                          .titleSmall
                          ?.copyWith(fontWeight: FontWeight.w600)),
                  Text(item.subtitle,
                      maxLines: 2,
                      overflow: TextOverflow.ellipsis,
                      style: Theme.of(context)
                          .textTheme
                          .bodySmall
                          ?.copyWith(color: AppColors.textSecondary)),
                ])),
            _Chevron(color: item.color, size: 20),
          ])));
}

class _UpdatesGroup extends StatelessWidget {
  const _UpdatesGroup(this.items);
  final List<_Item> items;
  @override
  Widget build(BuildContext context) => DecoratedBox(
      decoration: BoxDecoration(
          color: AppColors.surface,
          borderRadius: BorderRadius.circular(18),
          border: Border.all(color: AppColors.divider),
          boxShadow: const [
            BoxShadow(
                color: Color(0x08182230), blurRadius: 12, offset: Offset(0, 4))
          ]),
      child: Column(
          children: List.generate(items.length, (index) => Column(children: [
                _UpdateTile(items[index]),
                if (index != items.length - 1)
                  const Divider(height: 1, indent: 60),
              ]))));
}

class _UpdateTile extends StatelessWidget {
  const _UpdateTile(this.item);
  final _Item item;
  @override
  Widget build(BuildContext context) => ListTile(
      contentPadding: const EdgeInsets.symmetric(horizontal: 12, vertical: 3),
      leading: Container(
          width: 38,
          height: 38,
          decoration: BoxDecoration(
              color: item.color.withOpacity(.09), shape: BoxShape.circle),
          child: Icon(item.icon, color: item.color, size: 20)),
      title: Text(item.title,
          maxLines: 2,
          overflow: TextOverflow.ellipsis,
          style: Theme.of(context)
              .textTheme
              .titleSmall
              ?.copyWith(fontWeight: FontWeight.w600)),
      subtitle: Text(item.subtitle,
          maxLines: 2, overflow: TextOverflow.ellipsis),
      trailing: _Chevron(color: item.color),
      onTap: item.onTap);
}

class _Chevron extends StatelessWidget {
  const _Chevron({required this.color, this.size = 24});
  final Color color;
  final double size;
  @override
  Widget build(BuildContext context) => Transform.flip(
      flipX: Directionality.of(context) == TextDirection.ltr,
      child: Icon(Icons.chevron_left_rounded, color: color, size: size));
}

bool _pending(StudentHomework item) => !const {'submitted', 'graded', 'closed_without_submission'}.contains(item.completionStatus);
bool _sameDay(DateTime a, DateTime b) => a.year == b.year && a.month == b.month && a.day == b.day;
DateTime _dateOnly(DateTime value) => DateTime(value.year, value.month, value.day);
String _date(DateTime value) => '${value.day}/${value.month}/${value.year}';
String _period(TimetableEntryModel entry) => '${entry.period.startTime} – ${entry.period.endTime}';
String _greeting(DateTime value) => value.hour < 12 ? 'صباح الخير' : value.hour < 18 ? 'مساء الخير' : 'مساء هادئ';
