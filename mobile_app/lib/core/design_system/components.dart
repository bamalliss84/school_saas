import 'package:flutter/material.dart';
import '../models/school_context.dart';
import 'tokens.dart';

class AppCard extends StatelessWidget {
  const AppCard({super.key, required this.child});
  final Widget child;
  @override
  Widget build(BuildContext context) => Card(
        shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(AppRadius.card)),
        child:
            Padding(padding: const EdgeInsets.all(AppSpacing.x4), child: child),
      );
}

class AppPrimaryButton extends StatelessWidget {
  const AppPrimaryButton({super.key, required this.label, this.onPressed});
  final String label;
  final VoidCallback? onPressed;
  @override
  Widget build(BuildContext context) => SizedBox(
        width: double.infinity,
        height: 48,
        child: FilledButton(onPressed: onPressed, child: Text(label)),
      );
}

class AppSecondaryButton extends StatelessWidget {
  const AppSecondaryButton({super.key, required this.label, this.onPressed});
  final String label;
  final VoidCallback? onPressed;
  @override
  Widget build(BuildContext context) => SizedBox(
        height: 48,
        child: OutlinedButton(onPressed: onPressed, child: Text(label)),
      );
}

class AppTextField extends StatelessWidget {
  const AppTextField(
      {super.key,
      required this.controller,
      required this.label,
      this.obscureText = false});
  final TextEditingController controller;
  final String label;
  final bool obscureText;
  @override
  Widget build(BuildContext context) => TextField(
        controller: controller,
        obscureText: obscureText,
        decoration: InputDecoration(labelText: label),
      );
}

class StatusChip extends StatelessWidget {
  const StatusChip(
      {super.key, required this.label, this.icon = Icons.info_outline});
  final String label;
  final IconData icon;
  @override
  Widget build(BuildContext context) =>
      Chip(avatar: Icon(icon, size: 18), label: Text(label));
}

class StudentAppHeader extends StatelessWidget {
  const StudentAppHeader(
      {super.key,
      required this.schoolName,
      this.studentName,
      this.academicYear,
      this.onNotifications,
      this.notificationCount = 0});
  final String schoolName;
  final String? studentName;
  final String? academicYear;
  final VoidCallback? onNotifications;
  final int notificationCount;
  @override
  Widget build(BuildContext context) => Padding(
        padding: const EdgeInsets.all(AppSpacing.x4),
        child: Row(children: [
          const CircleAvatar(child: Icon(Icons.person_outline)),
          const SizedBox(width: AppSpacing.x3),
          Expanded(
              child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                if (studentName?.isNotEmpty == true)
                  Text(studentName!,
                      maxLines: 1, overflow: TextOverflow.ellipsis),
                Text(
                    [schoolName, academicYear]
                        .where((value) => value?.isNotEmpty == true)
                        .join(' • '),
                    maxLines: 2,
                    overflow: TextOverflow.ellipsis,
                    style: Theme.of(context).textTheme.bodySmall),
              ])),
          if (onNotifications != null)
            Badge(
              isLabelVisible: notificationCount > 0,
              label: Text(notificationCount > 99 ? '99+' : '$notificationCount'),
              child: IconButton(
                tooltip: 'الإشعارات',
                onPressed: onNotifications,
                icon: const Icon(Icons.notifications_none),
              ),
            ),
        ]),
      );
}

class HistoricalContextBanner extends StatelessWidget {
  const HistoricalContextBanner({super.key, this.context});
  final SchoolContext? context;
  @override
  Widget build(BuildContext context) => Semantics(
        label: 'سياق تاريخي للعرض فقط',
        child: Container(
          width: double.infinity,
          color: const Color(0xfffff4e5),
          padding: const EdgeInsets.all(AppSpacing.x3),
          child: Text(
            this.context == null
                ? 'سياق تاريخي — العرض فقط'
                : 'السجل الدراسي السابق\n${this.context!.schoolName} • ${this.context!.academicYearName ?? ''}\nللعرض فقط',
            textAlign: TextAlign.center,
          ),
        ),
      );
}

class OfflineCacheBanner extends StatelessWidget {
  const OfflineCacheBanner({super.key});
  @override
  Widget build(BuildContext context) => Container(
        width: double.infinity,
        margin: const EdgeInsets.symmetric(horizontal: AppSpacing.x4),
        padding: const EdgeInsets.all(AppSpacing.x3),
        decoration: BoxDecoration(
          color: AppColors.info.withOpacity(.08),
          borderRadius: BorderRadius.circular(AppRadius.chip),
        ),
        child: const Row(children: [
          Icon(Icons.cloud_off_outlined, color: AppColors.info),
          SizedBox(width: AppSpacing.x2),
          Expanded(
            child: Text(
              'لا يوجد اتصال بالإنترنت\nيتم عرض آخر بيانات محفوظة',
              maxLines: 2,
              overflow: TextOverflow.ellipsis,
            ),
          ),
        ]),
      );
}

String formatLastUpdated(DateTime value, DateTime now) {
  final difference = now.difference(value);
  if (difference.inMinutes < 1) return 'آخر تحديث الآن';
  if (difference.inMinutes < 60) {
    return 'آخر تحديث منذ ${difference.inMinutes} دقائق';
  }
  final time =
      '${value.hour.toString().padLeft(2, '0')}:${value.minute.toString().padLeft(2, '0')}';
  if (value.year == now.year &&
      value.month == now.month &&
      value.day == now.day) return 'آخر تحديث اليوم $time';
  final yesterday = now.subtract(const Duration(days: 1));
  if (value.year == yesterday.year &&
      value.month == yesterday.month &&
      value.day == yesterday.day) return 'آخر تحديث أمس $time';
  return 'آخر تحديث ${value.day}/${value.month} $time';
}

class LastUpdatedLabel extends StatelessWidget {
  const LastUpdatedLabel({super.key, required this.value, this.now});
  final DateTime value;
  final DateTime? now;
  @override
  Widget build(BuildContext context) =>
      Text(formatLastUpdated(value, now ?? DateTime.now()),
          style: Theme.of(context).textTheme.bodySmall);
}

class AppEmptyState extends StatelessWidget {
  const AppEmptyState({super.key, this.message = 'لا توجد بيانات'});
  final String message;
  @override
  Widget build(BuildContext context) => Center(child: Text(message));
}

class AppErrorState extends StatelessWidget {
  const AppErrorState({super.key, this.message = 'تعذر تحميل البيانات'});
  final String message;
  @override
  Widget build(BuildContext context) => Center(child: Text(message));
}

class AppSkeletonCard extends StatelessWidget {
  const AppSkeletonCard({super.key});
  @override
  Widget build(BuildContext context) => const AppCard(
      child: SizedBox(
          height: 72, child: Center(child: LinearProgressIndicator())));
}
