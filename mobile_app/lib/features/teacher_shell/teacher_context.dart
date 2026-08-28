import 'package:flutter/material.dart';

import '../../core/design_system/components.dart';
import '../../core/design_system/tokens.dart';
import '../../core/models/school_context.dart';
import 'teacher_shared.dart';

class TeacherContextScreen extends StatefulWidget {
  const TeacherContextScreen({
    super.key,
    required this.current,
    required this.contexts,
    required this.offline,
    required this.historicalOnly,
    required this.onBack,
    required this.onSelect,
  });

  final SchoolContext current;
  final List<SchoolContext> contexts;
  final bool offline;
  final bool historicalOnly;
  final VoidCallback onBack;
  final Future<void> Function(SchoolContext) onSelect;

  @override
  State<TeacherContextScreen> createState() => _TeacherContextScreenState();
}

class _TeacherContextScreenState extends State<TeacherContextScreen> {
  int? busyId;
  String? error;

  Future<void> _select(SchoolContext item) async {
    if (widget.offline || item.membershipId == widget.current.membershipId) {
      return;
    }
    setState(() {
      busyId = item.membershipId;
      error = null;
    });
    try {
      await widget.onSelect(item);
    } catch (_) {
      if (mounted) {
        setState(() => error = 'تعذر تغيير السياق. ما زلت في السياق السابق.');
      }
    } finally {
      if (mounted) setState(() => busyId = null);
    }
  }

  @override
  Widget build(BuildContext context) {
    final items = widget.historicalOnly
        ? widget.contexts.where((item) => item.isHistorical).toList()
        : widget.contexts;
    return TeacherNestedPage(
      title: widget.historicalOnly
          ? 'السجل الدراسي السابق'
          : 'تغيير المدرسة أو الدور',
      onBack: widget.onBack,
      child: ListView(children: [
        if (widget.offline) ...[
          const OfflineCacheBanner(),
          const SizedBox(height: AppSpacing.x3),
        ],
        if (error != null) ...[
          Text(error!, style: const TextStyle(color: AppColors.error)),
          const SizedBox(height: AppSpacing.x2),
        ],
        if (items.isEmpty)
          const AppEmptyState(message: 'لا توجد سجلات دراسية سابقة'),
        ...items.map((item) => Padding(
              padding: const EdgeInsets.only(bottom: AppSpacing.x3),
              child: _ContextOption(
                item: item,
                selected: item.membershipId == widget.current.membershipId,
                busy: busyId == item.membershipId,
                enabled: !widget.offline && busyId == null,
                onTap: () => _select(item),
              ),
            )),
      ]),
    );
  }
}

class _ContextOption extends StatelessWidget {
  const _ContextOption({
    required this.item,
    required this.selected,
    required this.busy,
    required this.enabled,
    required this.onTap,
  });

  final SchoolContext item;
  final bool selected;
  final bool busy;
  final bool enabled;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) => Container(
        decoration: BoxDecoration(
          border: selected
              ? Border.all(color: AppColors.primary, width: 1.5)
              : null,
          borderRadius: BorderRadius.circular(AppRadius.card),
        ),
        child: AppCard(
          child: ListTile(
            contentPadding: EdgeInsets.zero,
            title: Text(item.schoolName),
            subtitle: Padding(
              padding: const EdgeInsets.only(top: AppSpacing.x1),
              child: Wrap(
                spacing: AppSpacing.x2,
                runSpacing: AppSpacing.x1,
                children: [
                  TeacherSmallLabel(label: teacherRoleLabel(item.role)),
                  TeacherSmallLabel(
                    label: item.academicYearName ?? 'بدون عام دراسي',
                  ),
                  TeacherSmallLabel(
                    label: item.isHistorical ? 'للعرض فقط' : 'نشط',
                    color: item.isHistorical
                        ? AppColors.warning
                        : AppColors.success,
                  ),
                ],
              ),
            ),
            leading: selected
                ? const Icon(Icons.check_circle, color: AppColors.primary)
                : const Icon(Icons.circle_outlined, color: AppColors.disabled),
            trailing: busy
                ? const SizedBox.square(
                    dimension: 20,
                    child: CircularProgressIndicator(strokeWidth: 2),
                  )
                : null,
            enabled: enabled,
            onTap: selected ? null : onTap,
          ),
        ),
      );
}
