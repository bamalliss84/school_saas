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
          key: const PageStorageKey('student-attendance-list'),
          physics: const AlwaysScrollableScrollPhysics(),
          padding: const EdgeInsets.fromLTRB(
            AppSpacing.x4,
            AppSpacing.x2,
            AppSpacing.x4,
            AppSpacing.x6,
          ),
          children: [
            _AttendanceTitle(
              title: historical ? 'السجل الدراسي السابق' : 'الحضور',
              historical: historical,
              onBack: onBack,
            ),
            const SizedBox(height: AppSpacing.x3),
            _PeriodFilter(
              state: state,
              historical: historical,
              onChanged: onFilter,
            ),
            const SizedBox(height: AppSpacing.x3),
            AttendanceSummaryCard(summary: state.summary),
            const SizedBox(height: AppSpacing.x4),
            _AttendanceSectionHeader(lastUpdated: state.data.lastUpdated),
            const SizedBox(height: AppSpacing.x2),
            if (state.visible.isEmpty)
              _AttendanceEmptyState(
                offline: state.data.offline,
                filtered: state.data.records.isNotEmpty,
                onRetry: onRefresh,
              )
            else
              ...state.visible.map(
                (record) => Padding(
                  padding: const EdgeInsets.only(bottom: AppSpacing.x2),
                  child: AttendanceRecordCard(
                    record: record,
                    onTap: () => onOpen(record),
                  ),
                ),
              ),
          ],
        ),
      );
}

class _AttendanceTitle extends StatelessWidget {
  const _AttendanceTitle({
    required this.title,
    required this.historical,
    required this.onBack,
  });

  final String title;
  final bool historical;
  final VoidCallback onBack;

  @override
  Widget build(BuildContext context) => Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          IconButton(
            tooltip: 'رجوع',
            onPressed: onBack,
            icon: const Icon(Icons.arrow_back),
          ),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              mainAxisSize: MainAxisSize.min,
              children: [
                Text(
                  title,
                  style: Theme.of(context).textTheme.headlineMedium,
                  maxLines: 2,
                  overflow: TextOverflow.ellipsis,
                ),
                if (historical) ...[
                  const SizedBox(height: AppSpacing.x1),
                  const Align(
                    alignment: AlignmentDirectional.centerStart,
                    child: _ReadOnlyBadge(),
                  ),
                ],
              ],
            ),
          ),
        ],
      );
}

class _ReadOnlyBadge extends StatelessWidget {
  const _ReadOnlyBadge();

  @override
  Widget build(BuildContext context) => Container(
        padding: const EdgeInsets.symmetric(
          horizontal: AppSpacing.x2,
          vertical: AppSpacing.x1,
        ),
        decoration: BoxDecoration(
          color: AppColors.info.withOpacity(.08),
          borderRadius: BorderRadius.circular(AppRadius.chip),
        ),
        child: const Text(
          'للعرض فقط',
          style: TextStyle(
            color: AppColors.info,
            fontWeight: FontWeight.w600,
          ),
        ),
      );
}

class _PeriodFilter extends StatelessWidget {
  const _PeriodFilter({
    required this.state,
    required this.historical,
    required this.onChanged,
  });

  final AttendanceReady state;
  final bool historical;
  final ValueChanged<String> onChanged;

  @override
  Widget build(BuildContext context) => DropdownButtonFormField<String>(
        value: state.filterKey,
        isExpanded: true,
        decoration: InputDecoration(
          labelText: 'الفترة',
          filled: true,
          fillColor: AppColors.surface,
          contentPadding: const EdgeInsets.symmetric(
            horizontal: AppSpacing.x3,
            vertical: AppSpacing.x2,
          ),
          border: OutlineInputBorder(
            borderRadius: BorderRadius.circular(AppRadius.chip),
          ),
        ),
        items: [
          const DropdownMenuItem(
            value: 'all',
            child: Text('كل السنة الدراسية'),
          ),
          if (!historical)
            const DropdownMenuItem(
              value: 'month',
              child: Text('هذا الشهر'),
            ),
          ...state.data.terms.map(
            (term) => DropdownMenuItem(
              value: 'term:${term.id}',
              child: Text(
                term.name,
                maxLines: 1,
                overflow: TextOverflow.ellipsis,
              ),
            ),
          ),
        ],
        onChanged: (value) {
          if (value != null) onChanged(value);
        },
      );
}

class AttendanceSummaryCard extends StatelessWidget {
  const AttendanceSummaryCard({super.key, required this.summary});

  final AttendanceSummary summary;

  @override
  Widget build(BuildContext context) => AppCard(
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Row(
              children: [
                SizedBox(
                  width: 76,
                  height: 76,
                  child: Stack(
                    alignment: Alignment.center,
                    children: [
                      SizedBox.expand(
                        child: CircularProgressIndicator(
                          value: summary.total == 0
                              ? 0
                              : summary.percentage / 100,
                          strokeWidth: 7,
                          backgroundColor: AppColors.divider,
                          color: _attendanceRateColor(summary.percentage),
                        ),
                      ),
                      Text(
                        '${_percentage(summary.percentage)}%',
                        style: Theme.of(context)
                            .textTheme
                            .titleMedium
                            ?.copyWith(fontWeight: FontWeight.w700),
                      ),
                    ],
                  ),
                ),
                const SizedBox(width: AppSpacing.x4),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        'نسبة الحضور',
                        style: Theme.of(context).textTheme.titleMedium,
                      ),
                      const SizedBox(height: AppSpacing.x1),
                      Text(
                        _summaryMessage(summary),
                        style: Theme.of(context).textTheme.bodySmall?.copyWith(
                              color: AppColors.textSecondary,
                            ),
                      ),
                    ],
                  ),
                ),
              ],
            ),
            const SizedBox(height: AppSpacing.x4),
            Row(
              children: [
                Expanded(
                  child: _CountTile(
                    label: 'حاضر',
                    count: summary.present,
                    color: AppColors.success,
                    icon: Icons.check_circle_outline,
                  ),
                ),
                const SizedBox(width: AppSpacing.x2),
                Expanded(
                  child: _CountTile(
                    label: 'غائب',
                    count: summary.absent,
                    color: AppColors.error,
                    icon: Icons.cancel_outlined,
                  ),
                ),
              ],
            ),
            const SizedBox(height: AppSpacing.x2),
            Row(
              children: [
                Expanded(
                  child: _CountTile(
                    label: 'متأخر',
                    count: summary.late,
                    color: AppColors.warning,
                    icon: Icons.schedule_outlined,
                  ),
                ),
                const SizedBox(width: AppSpacing.x2),
                Expanded(
                  child: _CountTile(
                    label: 'بعذر',
                    count: summary.excused,
                    color: AppColors.info,
                    icon: Icons.verified_outlined,
                  ),
                ),
              ],
            ),
          ],
        ),
      );
}

class _CountTile extends StatelessWidget {
  const _CountTile({
    required this.label,
    required this.count,
    required this.color,
    required this.icon,
  });

  final String label;
  final int count;
  final Color color;
  final IconData icon;

  @override
  Widget build(BuildContext context) => Container(
        padding: const EdgeInsets.symmetric(
          horizontal: AppSpacing.x2,
          vertical: AppSpacing.x2,
        ),
        decoration: BoxDecoration(
          color: color.withOpacity(.08),
          borderRadius: BorderRadius.circular(AppRadius.chip),
          border: Border.all(color: color.withOpacity(.12)),
        ),
        child: Row(
          children: [
            Icon(icon, size: 18, color: color),
            const SizedBox(width: AppSpacing.x1),
            Expanded(
              child: Text(
                label,
                maxLines: 1,
                overflow: TextOverflow.ellipsis,
                style: Theme.of(context).textTheme.bodySmall,
              ),
            ),
            Text(
              '$count',
              style: TextStyle(color: color, fontWeight: FontWeight.w700),
            ),
          ],
        ),
      );
}

class _AttendanceSectionHeader extends StatelessWidget {
  const _AttendanceSectionHeader({required this.lastUpdated});

  final DateTime lastUpdated;

  @override
  Widget build(BuildContext context) => Row(
        crossAxisAlignment: CrossAxisAlignment.end,
        children: [
          Expanded(
            child: Text(
              'سجل الحضور',
              style: Theme.of(context).textTheme.titleLarge,
            ),
          ),
          LastUpdatedLabel(value: lastUpdated.toLocal()),
        ],
      );
}

class AttendanceRecordCard extends StatelessWidget {
  const AttendanceRecordCard({
    super.key,
    required this.record,
    required this.onTap,
  });

  final StudentAttendanceRecord record;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) => Material(
        color: AppColors.surface,
        borderRadius: BorderRadius.circular(AppRadius.card),
        child: InkWell(
          onTap: onTap,
          borderRadius: BorderRadius.circular(AppRadius.card),
          child: Container(
            padding: const EdgeInsets.all(AppSpacing.x3),
            decoration: BoxDecoration(
              borderRadius: BorderRadius.circular(AppRadius.card),
              border: Border.all(color: AppColors.divider),
            ),
            child: Row(
              children: [
                _StatusIcon(status: record.status),
                const SizedBox(width: AppSpacing.x3),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        _date(record.date),
                        style: Theme.of(context)
                            .textTheme
                            .titleMedium
                            ?.copyWith(fontWeight: FontWeight.w600),
                      ),
                      if (record.termName.isNotEmpty) ...[
                        const SizedBox(height: AppSpacing.x1),
                        Text(
                          record.termName,
                          maxLines: 1,
                          overflow: TextOverflow.ellipsis,
                          style: Theme.of(context).textTheme.bodySmall?.copyWith(
                                color: AppColors.textSecondary,
                              ),
                        ),
                      ],
                    ],
                  ),
                ),
                const SizedBox(width: AppSpacing.x2),
                _StatusLabel(status: record.status),
                const SizedBox(width: AppSpacing.x1),
                const Icon(
                  Icons.chevron_left,
                  size: 20,
                  color: AppColors.textSecondary,
                ),
              ],
            ),
          ),
        ),
      );
}

class StudentAttendanceDetailScreen extends StatelessWidget {
  const StudentAttendanceDetailScreen({
    super.key,
    required this.record,
    required this.historical,
    required this.onBack,
  });

  final StudentAttendanceRecord record;
  final bool historical;
  final VoidCallback onBack;

  @override
  Widget build(BuildContext context) => ListView(
        padding: const EdgeInsets.fromLTRB(
          AppSpacing.x4,
          AppSpacing.x2,
          AppSpacing.x4,
          AppSpacing.x6,
        ),
        children: [
          _AttendanceTitle(
            title: 'تفاصيل الحضور',
            historical: historical,
            onBack: onBack,
          ),
          const SizedBox(height: AppSpacing.x3),
          AppCard(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                Text(
                  _dateLong(record.date),
                  style: Theme.of(context)
                      .textTheme
                      .titleLarge
                      ?.copyWith(fontWeight: FontWeight.w700),
                ),
                const SizedBox(height: AppSpacing.x3),
                _AttendanceDetailStatus(status: record.status),
                const SizedBox(height: AppSpacing.x3),
                _DetailRow(label: 'الحالة', value: record.status.label),
                if (record.termName.isNotEmpty) ...[
                  const SizedBox(height: AppSpacing.x2),
                  _DetailRow(
                    label: 'الفصل الدراسي',
                    value: record.termName,
                  ),
                ],
                if (record.note.trim().isNotEmpty) ...[
                  const SizedBox(height: AppSpacing.x3),
                  const Divider(height: 1),
                  const SizedBox(height: AppSpacing.x3),
                  Text(
                    'ملاحظة المدرسة',
                    style: Theme.of(context).textTheme.titleMedium,
                  ),
                  const SizedBox(height: AppSpacing.x1),
                  Text(_cleanDemoNote(record.note)),
                ],
              ],
            ),
          ),
        ],
      );
}

class _AttendanceDetailStatus extends StatelessWidget {
  const _AttendanceDetailStatus({required this.status});

  final StudentAttendanceStatus status;

  @override
  Widget build(BuildContext context) => Container(
        padding: const EdgeInsets.all(AppSpacing.x3),
        decoration: BoxDecoration(
          color: _color(status).withOpacity(.10),
          borderRadius: BorderRadius.circular(AppRadius.card),
        ),
        child: Row(
          children: [
            Icon(_icon(status), color: _color(status), size: 28),
            const SizedBox(width: AppSpacing.x2),
            Expanded(
              child: Text(
                status.label,
                style: Theme.of(context).textTheme.titleLarge?.copyWith(
                      color: _color(status),
                      fontWeight: FontWeight.w700,
                    ),
              ),
            ),
          ],
        ),
      );
}

class _DetailRow extends StatelessWidget {
  const _DetailRow({required this.label, required this.value});

  final String label;
  final String value;

  @override
  Widget build(BuildContext context) => LayoutBuilder(
        builder: (context, constraints) {
          final textScale = MediaQuery.textScalerOf(context).scale(1);
          final compact = constraints.maxWidth < 280 || textScale > 1.2;
          final labelStyle = Theme.of(context).textTheme.bodyMedium;
          final valueStyle = labelStyle?.copyWith(fontWeight: FontWeight.w600);

          if (compact) {
            return Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              mainAxisSize: MainAxisSize.min,
              children: [
                Text('$label:', style: labelStyle),
                const SizedBox(height: AppSpacing.x1),
                Text(value, style: valueStyle),
              ],
            );
          }

          return Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Flexible(
                flex: 2,
                child: Text('$label:', style: labelStyle),
              ),
              const SizedBox(width: AppSpacing.x2),
              Expanded(
                flex: 3,
                child: Text(value, style: valueStyle),
              ),
            ],
          );
        },
      );
}

class StudentAttendanceLoadingView extends StatelessWidget {
  const StudentAttendanceLoadingView({super.key});

  @override
  Widget build(BuildContext context) => ListView(
        physics: const NeverScrollableScrollPhysics(),
        padding: const EdgeInsets.fromLTRB(
          AppSpacing.x4,
          AppSpacing.x2,
          AppSpacing.x4,
          AppSpacing.x6,
        ),
        children: const [
          _SkeletonBar(widthFactor: .45, height: 28),
          SizedBox(height: AppSpacing.x4),
          _SkeletonBar(height: 52),
          SizedBox(height: AppSpacing.x3),
          _SkeletonCard(height: 180),
          SizedBox(height: AppSpacing.x4),
          _SkeletonBar(widthFactor: .36, height: 22),
          SizedBox(height: AppSpacing.x2),
          _SkeletonCard(height: 72),
          SizedBox(height: AppSpacing.x2),
          _SkeletonCard(height: 72),
          SizedBox(height: AppSpacing.x2),
          _SkeletonCard(height: 72),
        ],
      );
}

class _SkeletonBar extends StatelessWidget {
  const _SkeletonBar({this.widthFactor = 1, required this.height});

  final double widthFactor;
  final double height;

  @override
  Widget build(BuildContext context) => FractionallySizedBox(
        alignment: AlignmentDirectional.centerStart,
        widthFactor: widthFactor,
        child: Container(
          height: height,
          decoration: BoxDecoration(
            color: AppColors.divider,
            borderRadius: BorderRadius.circular(AppRadius.chip),
          ),
        ),
      );
}

class _SkeletonCard extends StatelessWidget {
  const _SkeletonCard({required this.height});

  final double height;

  @override
  Widget build(BuildContext context) => Container(
        height: height,
        decoration: BoxDecoration(
          color: AppColors.surface,
          borderRadius: BorderRadius.circular(AppRadius.card),
          border: Border.all(color: AppColors.divider),
        ),
        child: const Padding(
          padding: EdgeInsets.all(AppSpacing.x4),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              _SkeletonBar(widthFactor: .58, height: 14),
              SizedBox(height: AppSpacing.x3),
              _SkeletonBar(widthFactor: .86, height: 12),
            ],
          ),
        ),
      );
}

class StudentAttendanceOfflineEmptyView extends StatelessWidget {
  const StudentAttendanceOfflineEmptyView({
    super.key,
    required this.onRetry,
    required this.onBack,
  });

  final Future<void> Function() onRetry;
  final VoidCallback onBack;

  @override
  Widget build(BuildContext context) => ListView(
        physics: const AlwaysScrollableScrollPhysics(),
        padding: const EdgeInsets.fromLTRB(
          AppSpacing.x4,
          AppSpacing.x2,
          AppSpacing.x4,
          AppSpacing.x6,
        ),
        children: [
          _AttendanceTitle(
            title: 'الحضور',
            historical: false,
            onBack: onBack,
          ),
          _CenteredAttendanceState(
            fillViewport: true,
            icon: Icons.wifi_off_outlined,
            title: 'لا تتوفر بيانات الحضور دون اتصال',
            message: 'اتصل بالإنترنت لتحميل سجل الحضور لأول مرة',
            actionLabel: 'إعادة المحاولة',
            onAction: onRetry,
          ),
        ],
      );
}

class StudentAttendanceErrorView extends StatelessWidget {
  const StudentAttendanceErrorView({
    super.key,
    required this.message,
    required this.onRetry,
    required this.onBack,
  });

  final String message;
  final Future<void> Function() onRetry;
  final VoidCallback onBack;

  @override
  Widget build(BuildContext context) => ListView(
        physics: const AlwaysScrollableScrollPhysics(),
        padding: const EdgeInsets.fromLTRB(
          AppSpacing.x4,
          AppSpacing.x2,
          AppSpacing.x4,
          AppSpacing.x6,
        ),
        children: [
          _AttendanceTitle(
            title: 'الحضور',
            historical: false,
            onBack: onBack,
          ),
          _CenteredAttendanceState(
            fillViewport: true,
            icon: Icons.travel_explore_outlined,
            title: 'تعذر تحميل سجل الحضور',
            message: message,
            actionLabel: 'إعادة المحاولة',
            onAction: onRetry,
          ),
        ],
      );
}

class _AttendanceEmptyState extends StatelessWidget {
  const _AttendanceEmptyState({
    required this.offline,
    required this.filtered,
    required this.onRetry,
  });

  final bool offline;
  final bool filtered;
  final Future<void> Function() onRetry;

  @override
  Widget build(BuildContext context) {
    if (offline && !filtered) {
      return _CenteredAttendanceState(
        icon: Icons.wifi_off_outlined,
        title: 'لا تتوفر بيانات الحضور دون اتصال',
        message: 'اتصل بالإنترنت لتحميل سجل الحضور لأول مرة',
        actionLabel: 'إعادة المحاولة',
        onAction: onRetry,
      );
    }
    return _CenteredAttendanceState(
      icon: Icons.event_available_outlined,
      title: filtered ? 'لا توجد سجلات في هذه الفترة' : 'لا توجد سجلات حضور',
      message: filtered
          ? 'جرّب اختيار فترة أخرى لعرض سجل الحضور'
          : 'لا توجد سجلات حضور خلال الفترة المحددة',
    );
  }
}

class _CenteredAttendanceState extends StatelessWidget {
  const _CenteredAttendanceState({
    required this.icon,
    required this.title,
    required this.message,
    this.actionLabel,
    this.onAction,
    this.fillViewport = false,
  });

  final IconData icon;
  final String title;
  final String message;
  final String? actionLabel;
  final Future<void> Function()? onAction;
  final bool fillViewport;

  @override
  Widget build(BuildContext context) {
    final minHeight = fillViewport
        ? (MediaQuery.sizeOf(context).height * .36)
            .clamp(176.0, 300.0)
            .toDouble()
        : 0.0;

    return ConstrainedBox(
      constraints: BoxConstraints(minHeight: minHeight),
      child: Padding(
        padding: const EdgeInsets.symmetric(
          vertical: AppSpacing.x4,
          horizontal: AppSpacing.x4,
        ),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(icon, size: 56, color: AppColors.disabled),
            const SizedBox(height: AppSpacing.x3),
            Text(
              title,
              textAlign: TextAlign.center,
              style: Theme.of(context)
                  .textTheme
                  .titleLarge
                  ?.copyWith(fontWeight: FontWeight.w700),
            ),
            const SizedBox(height: AppSpacing.x2),
            Text(
              message,
              textAlign: TextAlign.center,
              style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                    color: AppColors.textSecondary,
                  ),
            ),
            if (actionLabel != null && onAction != null) ...[
              const SizedBox(height: AppSpacing.x3),
              FilledButton(
                onPressed: () => onAction!(),
                child: Text(actionLabel!),
              ),
            ],
          ],
        ),
      ),
    );
  }
}

class _StatusIcon extends StatelessWidget {
  const _StatusIcon({required this.status});

  final StudentAttendanceStatus status;

  @override
  Widget build(BuildContext context) => Container(
        width: 34,
        height: 34,
        decoration: BoxDecoration(
          color: _color(status).withOpacity(.08),
          shape: BoxShape.circle,
        ),
        child: Icon(_icon(status), size: 20, color: _color(status)),
      );
}

class _StatusLabel extends StatelessWidget {
  const _StatusLabel({required this.status});

  final StudentAttendanceStatus status;

  @override
  Widget build(BuildContext context) => Container(
        padding: const EdgeInsets.symmetric(
          horizontal: AppSpacing.x2,
          vertical: AppSpacing.x1,
        ),
        decoration: BoxDecoration(
          color: _color(status).withOpacity(.08),
          borderRadius: BorderRadius.circular(AppRadius.chip),
        ),
        child: Text(
          status.label,
          style: TextStyle(
            color: _color(status),
            fontWeight: FontWeight.w600,
          ),
        ),
      );
}

Color _attendanceRateColor(double percentage) {
  if (percentage >= 90) return AppColors.success;
  if (percentage >= 75) return AppColors.info;
  if (percentage >= 60) return AppColors.warning;
  return AppColors.error;
}

String _summaryMessage(AttendanceSummary summary) {
  if (summary.total == 0) return 'لا توجد أيام مسجلة في الفترة الحالية';
  if (summary.absent == 0) return 'ممتاز! لم يتم تسجيل أي غياب خلال هذه الفترة';
  if (summary.absent == 1) return 'لديك يوم غياب واحد خلال هذه الفترة';
  return 'لديك ${summary.absent} أيام غياب خلال هذه الفترة';
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

const _weekdays = [
  'الاثنين',
  'الثلاثاء',
  'الأربعاء',
  'الخميس',
  'الجمعة',
  'السبت',
  'الأحد',
];

const _months = [
  'يناير',
  'فبراير',
  'مارس',
  'أبريل',
  'مايو',
  'يونيو',
  'يوليو',
  'أغسطس',
  'سبتمبر',
  'أكتوبر',
  'نوفمبر',
  'ديسمبر',
];

String _date(DateTime value) =>
    '${_weekdays[value.weekday - 1]}، ${value.day} ${_months[value.month - 1]} ${value.year}';

String _dateLong(DateTime value) => _date(value);

String _percentage(double value) => value == value.roundToDouble()
    ? value.toInt().toString()
    : value.toStringAsFixed(1);

String _cleanDemoNote(String value) => value.startsWith('DEMO attendance V1 | ')
    ? value.substring('DEMO attendance V1 | '.length)
    : value;
