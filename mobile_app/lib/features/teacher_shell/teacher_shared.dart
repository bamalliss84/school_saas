import 'package:flutter/material.dart';

import '../../core/design_system/components.dart';
import '../../core/design_system/tokens.dart';

class TeacherNestedPage extends StatelessWidget {
  const TeacherNestedPage({
    super.key,
    required this.title,
    required this.onBack,
    required this.child,
  });

  final String title;
  final VoidCallback onBack;
  final Widget child;

  @override
  Widget build(BuildContext context) => Column(children: [
        TeacherPageTitle(title: title, onBack: onBack),
        Expanded(
          child: Padding(
            padding: const EdgeInsets.fromLTRB(
              AppSpacing.x4,
              AppSpacing.x2,
              AppSpacing.x4,
              AppSpacing.x4,
            ),
            child: child,
          ),
        ),
      ]);
}

class TeacherPageTitle extends StatelessWidget {
  const TeacherPageTitle({super.key, required this.title, this.onBack});

  final String title;
  final VoidCallback? onBack;

  @override
  Widget build(BuildContext context) => Padding(
        padding: const EdgeInsets.all(AppSpacing.x4),
        child: Row(children: [
          if (onBack != null)
            IconButton(
              tooltip: 'رجوع',
              onPressed: onBack,
              icon: const Icon(Icons.arrow_forward),
            ),
          Expanded(
            child: Text(
              title,
              style: Theme.of(context).textTheme.headlineMedium,
            ),
          ),
        ]),
      );
}

class TeacherSmallLabel extends StatelessWidget {
  const TeacherSmallLabel({
    super.key,
    required this.label,
    this.color = AppColors.primary,
  });

  final String label;
  final Color color;

  @override
  Widget build(BuildContext context) => Container(
        padding: const EdgeInsets.symmetric(
          horizontal: AppSpacing.x2,
          vertical: AppSpacing.x1,
        ),
        decoration: BoxDecoration(
          color: color.withOpacity(.1),
          borderRadius: BorderRadius.circular(AppRadius.chip),
        ),
        child: Text(label, style: TextStyle(color: color, fontSize: 12)),
      );
}

class TeacherInfoRow extends StatelessWidget {
  const TeacherInfoRow(this.label, this.value, {super.key});

  final String label;
  final String? value;

  @override
  Widget build(BuildContext context) => Padding(
        padding: const EdgeInsets.symmetric(vertical: AppSpacing.x2),
        child: Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Expanded(
            flex: 2,
            child: Text(label, style: Theme.of(context).textTheme.bodySmall),
          ),
          Expanded(
            flex: 3,
            child: Text(
              value?.trim().isNotEmpty == true ? value! : '—',
              textAlign: TextAlign.end,
            ),
          ),
        ]),
      );
}

String teacherRoleLabel(String role) => switch (role) {
      'teacher' => 'معلم',
      'parent' => 'ولي أمر',
      'student' => 'طالب',
      'school_admin' => 'إدارة المدرسة',
      'super_admin' => 'مدير النظام',
      _ => role,
    };
