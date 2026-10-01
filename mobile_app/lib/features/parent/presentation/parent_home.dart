import 'package:flutter/material.dart';

import '../../../../core/design_system/components.dart';
import '../../../../core/design_system/role_visual_tokens.dart';
import '../../../../core/models/school_context.dart';
import '../domain/parent_models.dart';
import 'parent_controller.dart';

class ParentHome extends StatelessWidget {
  const ParentHome({
    super.key,
    required this.state,
    required this.contextInfo,
    required this.onSelectChild,
    required this.onRefresh,
  });

  final ParentState state;
  final SchoolContext contextInfo;
  final Future<void> Function(int childId) onSelectChild;
  final Future<void> Function() onRefresh;

  @override
  Widget build(BuildContext context) => switch (state) {
        ParentLoading() => const Center(child: CircularProgressIndicator()),
        ParentFailure(:final message) => _ParentError(
            message: message,
            onRetry: onRefresh,
          ),
        ParentReady(:final data, :final refreshing) => _ParentHomeReady(
            data: data,
            refreshing: refreshing,
            contextInfo: contextInfo,
            onSelectChild: onSelectChild,
            onRefresh: onRefresh,
          ),
      };
}

class _ParentHomeReady extends StatelessWidget {
  const _ParentHomeReady({
    required this.data,
    required this.refreshing,
    required this.contextInfo,
    required this.onSelectChild,
    required this.onRefresh,
  });

  final ParentFoundationData data;
  final bool refreshing;
  final SchoolContext contextInfo;
  final Future<void> Function(int childId) onSelectChild;
  final Future<void> Function() onRefresh;

  @override
  Widget build(BuildContext context) {
    if (data.children.isEmpty) {
      return RefreshIndicator(
        onRefresh: onRefresh,
        child: ListView(
          physics: const AlwaysScrollableScrollPhysics(),
          padding: const EdgeInsets.all(24),
          children: const [
            SizedBox(height: 120),
            Icon(Icons.family_restroom, size: 56, color: Colors.grey),
            SizedBox(height: 16),
            Text(
              'لا يوجد أبناء مرتبطون بهذا السياق',
              textAlign: TextAlign.center,
            ),
          ],
        ),
      );
    }
    final child = data.selectedChild!;
    final enrollment = data.selectedEnrollment;
    return RefreshIndicator(
      onRefresh: onRefresh,
      child: ListView(
        physics: const AlwaysScrollableScrollPhysics(),
        padding: const EdgeInsets.all(16),
        children: [
          if (refreshing) const LinearProgressIndicator(),
          if (data.offline) ...[
            const OfflineCacheBanner(),
            const SizedBox(height: 12),
            const Text(
              'تعرض هذه الصفحة بيانات محفوظة حتى يعود الاتصال.',
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: 12),
          ],
          if (contextInfo.isHistorical) ...[
            const _ReadOnlyBanner(),
            const SizedBox(height: 12),
          ],
          _Header(contextInfo: contextInfo),
          const SizedBox(height: 16),
          if (data.children.length > 1)
            _ChildSelector(
              children: data.children,
              selectedId: child.id,
              onChanged: onSelectChild,
            )
          else
            _SingleChildLabel(child: child),
          const SizedBox(height: 16),
          Card(
            child: Padding(
              padding: const EdgeInsets.all(18),
              child: Column(
                children: [
                  CircleAvatar(
                    radius: 30,
                    backgroundColor: RoleVisualTokens.parent.withOpacity(.12),
                    child: const Icon(
                      Icons.person_outline,
                      color: RoleVisualTokens.parent,
                      size: 32,
                    ),
                  ),
                  const SizedBox(height: 10),
                  Text(
                    child.fullName,
                    textAlign: TextAlign.center,
                    style: Theme.of(context).textTheme.titleLarge?.copyWith(
                          fontWeight: FontWeight.w800,
                        ),
                  ),
                  if (child.studentCode.isNotEmpty)
                    Text('رقم الطالب: ${child.studentCode}'),
                  const Divider(height: 28),
                  _InfoRow('المدرسة', contextInfo.schoolName),
                  _InfoRow(
                    'العام الدراسي',
                    enrollment?.academicYear.name ??
                        contextInfo.academicYearName ??
                        '—',
                  ),
                  _InfoRow('الصف', enrollment?.classroomName ?? '—'),
                  _InfoRow('الشعبة', enrollment?.sectionName ?? '—'),
                  _InfoRow('صلة القرابة', _relationship(child.relationship)),
                ],
              ),
            ),
          ),
          if (enrollment == null) ...[
            const SizedBox(height: 12),
            const Text(
              'لا توجد بيانات تسجيل دراسي للطفل في هذا السياق.',
              textAlign: TextAlign.center,
            ),
          ],
        ],
      ),
    );
  }
}

class _Header extends StatelessWidget {
  const _Header({required this.contextInfo});
  final SchoolContext contextInfo;

  @override
  Widget build(BuildContext context) => Row(
        children: [
          Container(
            padding: const EdgeInsets.all(12),
            decoration: BoxDecoration(
              color: RoleVisualTokens.parent.withOpacity(.12),
              borderRadius: BorderRadius.circular(16),
            ),
            child: const Icon(
              Icons.family_restroom,
              color: RoleVisualTokens.parent,
            ),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  'الرئيسية',
                  style: Theme.of(context).textTheme.headlineSmall?.copyWith(
                        fontWeight: FontWeight.w800,
                      ),
                ),
                Text(
                  contextInfo.schoolName,
                  maxLines: 2,
                  overflow: TextOverflow.ellipsis,
                ),
              ],
            ),
          ),
        ],
      );
}

class _ChildSelector extends StatelessWidget {
  const _ChildSelector({
    required this.children,
    required this.selectedId,
    required this.onChanged,
  });
  final List<ParentChild> children;
  final int selectedId;
  final Future<void> Function(int) onChanged;

  @override
  Widget build(BuildContext context) => Card(
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 4),
          child: DropdownButton<int>(
            key: const Key('parent-child-selector'),
            value: selectedId,
            isExpanded: true,
            underline: const SizedBox.shrink(),
            items: [
              for (final child in children)
                DropdownMenuItem(
                  value: child.id,
                  child: Text(
                    child.fullName,
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                  ),
                ),
            ],
            onChanged: (value) {
              if (value != null) onChanged(value);
            },
          ),
        ),
      );
}

class _SingleChildLabel extends StatelessWidget {
  const _SingleChildLabel({required this.child});
  final ParentChild child;

  @override
  Widget build(BuildContext context) => Card(
        child: ListTile(
          leading: const Icon(Icons.person_outline),
          title: const Text('الابن المرتبط'),
          subtitle: Text(child.fullName),
        ),
      );
}

class _InfoRow extends StatelessWidget {
  const _InfoRow(this.label, this.value);
  final String label;
  final String value;

  @override
  Widget build(BuildContext context) => Padding(
        padding: const EdgeInsets.symmetric(vertical: 6),
        child: Row(
          children: [
            SizedBox(width: 120, child: Text(label)),
            Expanded(
              child: Text(
                value,
                textAlign: TextAlign.end,
                style: const TextStyle(fontWeight: FontWeight.w700),
              ),
            ),
          ],
        ),
      );
}

class _ReadOnlyBanner extends StatelessWidget {
  const _ReadOnlyBanner();

  @override
  Widget build(BuildContext context) => Container(
        padding: const EdgeInsets.all(12),
        decoration: BoxDecoration(
          color: RoleVisualTokens.parent.withOpacity(.09),
          borderRadius: BorderRadius.circular(12),
        ),
        child: const Text(
          'سياق تاريخي — للقراءة فقط',
          textAlign: TextAlign.center,
        ),
      );
}

class _ParentError extends StatelessWidget {
  const _ParentError({required this.message, required this.onRetry});
  final String message;
  final Future<void> Function() onRetry;

  @override
  Widget build(BuildContext context) => Center(
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              const Icon(Icons.error_outline, size: 48),
              const SizedBox(height: 12),
              Text(message, textAlign: TextAlign.center),
              TextButton(
                onPressed: onRetry,
                child: const Text('إعادة المحاولة'),
              ),
            ],
          ),
        ),
      );
}

String _relationship(String value) => switch (value) {
      'father' => 'الأب',
      'mother' => 'الأم',
      'brother' => 'الأخ',
      'sister' => 'الأخت',
      'guardian' => 'ولي الأمر',
      'other' => 'أخرى',
      _ => value.isEmpty ? '—' : value,
    };
