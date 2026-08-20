import 'package:flutter/material.dart';
import '../../../../core/design_system/components.dart';
import '../../../../core/design_system/tokens.dart';
import '../domain/attendance_models.dart';
import 'attendance_controller.dart';

class StudentAttendanceScreen extends StatelessWidget {
  const StudentAttendanceScreen({
    super.key,
    required this.state,
    required this.historical,
    required this.onFilter,
    required this.onOpen,
    required this.onRefresh,
    required this.onBack,
  });
  final AttendanceReady state;
  final bool historical;
  final ValueChanged<String> onFilter;
  final ValueChanged<StudentAttendanceRecord> onOpen;
  final Future<void> Function() onRefresh;
  final VoidCallback onBack;

  @override
  Widget build(BuildContext context) => RefreshIndicator(
        onRefresh: onRefresh,
        child: ListView(
          padding: const EdgeInsets.all(AppSpacing.x4),
          children: [
            Row(children: [
              IconButton(onPressed: onBack, icon: const Icon(Icons.arrow_back)),
              Expanded(child: Text(
                historical ? 'حضور السجل السابق' : 'الحضور',
                style: Theme.of(context).textTheme.headlineMedium,
              )),
              if (historical) const Chip(label: Text('للعرض فقط')),
            ]),
            const SizedBox(height: AppSpacing.x3),
            _PeriodFilter(state: state, historical: historical, onChanged: onFilter),
            const SizedBox(height: AppSpacing.x3),
            AttendanceSummaryCard(summary: state.summary),
            const SizedBox(height: AppSpacing.x4),
            Row(mainAxisAlignment: MainAxisAlignment.spaceBetween, children: [
              Text('سجل الحضور', style: Theme.of(context).textTheme.titleLarge),
              LastUpdatedLabel(value: state.data.lastUpdated.toLocal()),
            ]),
            const SizedBox(height: AppSpacing.x2),
            if (state.visible.isEmpty)
              const AppEmptyState(message: 'لا توجد سجلات حضور للفترة المحددة')
            else
              ...state.visible.map((record) => Padding(
                padding: const EdgeInsets.only(bottom: AppSpacing.x2),
                child: AttendanceRecordCard(
                  record: record, onTap: () => onOpen(record)),
              )),
          ],
        ),
      );
}

class _PeriodFilter extends StatelessWidget {
  const _PeriodFilter({required this.state, required this.historical, required this.onChanged});
  final AttendanceReady state;
  final bool historical;
  final ValueChanged<String> onChanged;

  @override
  Widget build(BuildContext context) => DropdownButtonFormField<String>(
        value: state.filterKey,
        isExpanded: true,
        decoration: const InputDecoration(
          labelText: 'الفترة', border: OutlineInputBorder(),
        ),
        items: [
          const DropdownMenuItem(value: 'all', child: Text('كل السنة الدراسية')),
          if (!historical)
            const DropdownMenuItem(value: 'month', child: Text('هذا الشهر')),
          ...state.data.terms.map((term) => DropdownMenuItem(
            value: 'term:${term.id}',
            child: Text(term.name, maxLines: 1, overflow: TextOverflow.ellipsis),
          )),
        ],
        onChanged: (value) { if (value != null) onChanged(value); },
      );
}

class AttendanceSummaryCard extends StatelessWidget {
  const AttendanceSummaryCard({super.key, required this.summary});
  final AttendanceSummary summary;

  @override
  Widget build(BuildContext context) => AppCard(
        child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Row(children: [
            Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
              const Text('نسبة الحضور'),
              Text('${_percentage(summary.percentage)}%',
                  style: Theme.of(context).textTheme.headlineMedium),
            ])),
            SizedBox(
              width: 64, height: 64,
              child: CircularProgressIndicator(
                value: summary.total == 0 ? 0 : summary.percentage / 100,
                strokeWidth: 7,
                backgroundColor: AppColors.divider,
              ),
            ),
          ]),
          const SizedBox(height: AppSpacing.x4),
          Wrap(spacing: AppSpacing.x2, runSpacing: AppSpacing.x2, children: [
            _CountChip(label: 'حاضر', count: summary.present,
                color: AppColors.success, icon: Icons.check_circle_outline),
            _CountChip(label: 'غائب', count: summary.absent,
                color: AppColors.error, icon: Icons.cancel_outlined),
            _CountChip(label: 'متأخر', count: summary.late,
                color: AppColors.warning, icon: Icons.schedule_outlined),
            _CountChip(label: 'بعذر', count: summary.excused,
                color: AppColors.info, icon: Icons.verified_outlined),
          ]),
        ]),
      );
}

class _CountChip extends StatelessWidget {
  const _CountChip({required this.label, required this.count,
      required this.color, required this.icon});
  final String label;
  final int count;
  final Color color;
  final IconData icon;
  @override
  Widget build(BuildContext context) => Container(
    padding: const EdgeInsets.symmetric(horizontal: AppSpacing.x3, vertical: AppSpacing.x2),
    decoration: BoxDecoration(color: color.withOpacity(.08),
        borderRadius: BorderRadius.circular(AppRadius.chip)),
    child: Row(mainAxisSize: MainAxisSize.min, children: [
      Icon(icon, size: 18, color: color),
      const SizedBox(width: AppSpacing.x1),
      Text('$label $count'),
    ]),
  );
}

class AttendanceRecordCard extends StatelessWidget {
  const AttendanceRecordCard({super.key, required this.record, required this.onTap});
  final StudentAttendanceRecord record;
  final VoidCallback onTap;
  @override
  Widget build(BuildContext context) => AppCard(
    child: InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(AppRadius.card),
      child: Padding(
        padding: const EdgeInsets.all(AppSpacing.x1),
        child: Row(children: [
          _StatusIcon(status: record.status),
          const SizedBox(width: AppSpacing.x3),
          Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            Text(_date(record.date), style: Theme.of(context).textTheme.titleMedium),
            if (record.termName.isNotEmpty)
              Text(record.termName, maxLines: 1, overflow: TextOverflow.ellipsis,
                  style: Theme.of(context).textTheme.bodySmall),
          ])),
          _StatusLabel(status: record.status),
          const SizedBox(width: AppSpacing.x1),
          const Icon(Icons.chevron_left),
        ]),
      ),
    ),
  );
}

class StudentAttendanceDetailScreen extends StatelessWidget {
  const StudentAttendanceDetailScreen({super.key, required this.record,
      required this.historical, required this.onBack});
  final StudentAttendanceRecord record;
  final bool historical;
  final VoidCallback onBack;

  @override
  Widget build(BuildContext context) => ListView(
    padding: const EdgeInsets.all(AppSpacing.x4),
    children: [
      Row(children: [
        IconButton(onPressed: onBack, icon: const Icon(Icons.arrow_back)),
        Expanded(child: Text('تفاصيل الحضور',
            style: Theme.of(context).textTheme.headlineMedium)),
        const Chip(label: Text('للعرض فقط')),
      ]),
      const SizedBox(height: AppSpacing.x3),
      AppCard(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        Text(_dateLong(record.date), style: Theme.of(context).textTheme.titleLarge),
        const SizedBox(height: AppSpacing.x3),
        Row(children: [
          const Text('الحالة: '),
          _StatusLabel(status: record.status),
        ]),
        if (record.termName.isNotEmpty) ...[
          const SizedBox(height: AppSpacing.x2),
          Text('الفصل الدراسي: ${record.termName}'),
        ],
        if (record.note.trim().isNotEmpty) ...[
          const SizedBox(height: AppSpacing.x3),
          Text('ملاحظة المدرسة:', style: Theme.of(context).textTheme.titleMedium),
          const SizedBox(height: AppSpacing.x1),
          Text(_cleanDemoNote(record.note)),
        ],
      ])),
      if (historical) ...[
        const SizedBox(height: AppSpacing.x3),
        const Chip(label: Text('السجل السابق — للعرض فقط')),
      ],
    ],
  );
}

class _StatusIcon extends StatelessWidget {
  const _StatusIcon({required this.status});
  final StudentAttendanceStatus status;
  @override
  Widget build(BuildContext context) => Icon(_icon(status), color: _color(status));
}
class _StatusLabel extends StatelessWidget {
  const _StatusLabel({required this.status});
  final StudentAttendanceStatus status;
  @override
  Widget build(BuildContext context) => Container(
    padding: const EdgeInsets.symmetric(horizontal: AppSpacing.x2, vertical: AppSpacing.x1),
    decoration: BoxDecoration(color: _color(status).withOpacity(.08),
        borderRadius: BorderRadius.circular(AppRadius.chip)),
    child: Text(status.label, style: TextStyle(color: _color(status))),
  );
}

Color _color(StudentAttendanceStatus status) => switch (status) {
  StudentAttendanceStatus.present => AppColors.success,
  StudentAttendanceStatus.absent => AppColors.error,
  StudentAttendanceStatus.late => AppColors.warning,
  StudentAttendanceStatus.excused => AppColors.info,
};
IconData _icon(StudentAttendanceStatus status) => switch (status) {
  StudentAttendanceStatus.present => Icons.check_circle_outline,
  StudentAttendanceStatus.absent => Icons.cancel_outlined,
  StudentAttendanceStatus.late => Icons.schedule_outlined,
  StudentAttendanceStatus.excused => Icons.verified_outlined,
};
const _weekdays = ['الاثنين', 'الثلاثاء', 'الأربعاء', 'الخميس', 'الجمعة', 'السبت', 'الأحد'];
const _months = ['يناير', 'فبراير', 'مارس', 'أبريل', 'مايو', 'يونيو',
  'يوليو', 'أغسطس', 'سبتمبر', 'أكتوبر', 'نوفمبر', 'ديسمبر'];
String _date(DateTime value) =>
    '${_weekdays[value.weekday - 1]}، ${value.day} ${_months[value.month - 1]} ${value.year}';
String _dateLong(DateTime value) => _date(value);
String _percentage(double value) => value == value.roundToDouble()
    ? value.toInt().toString() : value.toStringAsFixed(1);
String _cleanDemoNote(String value) => value.startsWith('DEMO attendance V1 | ')
    ? value.substring('DEMO attendance V1 | '.length) : value;
