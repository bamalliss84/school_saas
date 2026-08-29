import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../../core/design_system/components.dart';
import '../../../../core/design_system/role_visual_tokens.dart';
import '../../../../core/design_system/tokens.dart';
import '../../../../core/local_database/app_database.dart';
import '../../attendance/presentation/teacher_attendance_screen.dart';
import '../domain/teacher_students_models.dart';
import 'teacher_students_controller.dart';

class TeacherStudentsScreen extends ConsumerStatefulWidget {
  const TeacherStudentsScreen({
    super.key,
    required this.scope,
    required this.historical,
    required this.onDirtyChanged,
  });

  final CacheScope scope;
  final bool historical;
  final ValueChanged<bool> onDirtyChanged;

  @override
  ConsumerState<TeacherStudentsScreen> createState() =>
      _TeacherStudentsScreenState();
}

class _TeacherStudentsScreenState extends ConsumerState<TeacherStudentsScreen> {
  TeacherAssignmentSummary? selectedAssignment;
  bool attendanceMode = false;

  @override
  void didUpdateWidget(covariant TeacherStudentsScreen oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.scope != widget.scope) selectedAssignment = null;
    if (oldWidget.scope != widget.scope) {
      attendanceMode = false;
      WidgetsBinding.instance.addPostFrameCallback((_) {
        if (mounted) widget.onDirtyChanged(false);
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    final selected = selectedAssignment;
    if (selected != null) {
      if (attendanceMode) {
        return TeacherAttendanceScreen(
          scope: widget.scope,
          assignment: selected,
          initialDate: DateTime.now(),
          onDirtyChanged: widget.onDirtyChanged,
          onBack: () => setState(() => attendanceMode = false),
        );
      }
      return _RosterView(
        scope: widget.scope,
        assignment: selected,
        historical: widget.historical,
        onBack: () => setState(() => selectedAssignment = null),
        onAttendance: widget.historical
            ? null
            : () => setState(() => attendanceMode = true),
      );
    }
    final assignments = ref.watch(teacherAssignmentsProvider(widget.scope));
    return Column(children: [
      const _StudentsHeader(),
      Expanded(
        child: RefreshIndicator(
          onRefresh: () async {
            await ref.refresh(
              teacherAssignmentsProvider(widget.scope).future,
            );
          },
          child: assignments.when(
            loading: () => const _AssignmentsLoading(),
            error: (_, __) => _ErrorList(
              message: 'تعذر تحميل التكليفات التدريسية',
              onRetry: () =>
                  ref.invalidate(teacherAssignmentsProvider(widget.scope)),
            ),
            data: (items) => _AssignmentsList(
              assignments: items,
              historical: widget.historical,
              onSelected: (item) =>
                  setState(() => selectedAssignment = item),
            ),
          ),
        ),
      ),
    ]);
  }
}

class _StudentsHeader extends StatelessWidget {
  const _StudentsHeader();

  @override
  Widget build(BuildContext context) => Container(
        width: double.infinity,
        color: RoleVisualTokens.softSurface(AppVisualRole.teacher),
        padding: const EdgeInsets.all(AppSpacing.x4),
        child: Row(children: [
          Container(
            padding: const EdgeInsets.all(AppSpacing.x2),
            decoration: BoxDecoration(
              color: Colors.white,
              borderRadius: BorderRadius.circular(AppRadius.chip),
            ),
            child: const Icon(Icons.groups_outlined,
                color: RoleVisualTokens.teacher),
          ),
          const SizedBox(width: AppSpacing.x3),
          Expanded(
            child: Text('الطلاب والحضور',
                style: Theme.of(context).textTheme.headlineMedium),
          ),
        ]),
      );
}

class _AssignmentsList extends StatelessWidget {
  const _AssignmentsList({
    required this.assignments,
    required this.historical,
    required this.onSelected,
  });

  final List<TeacherAssignmentSummary> assignments;
  final bool historical;
  final ValueChanged<TeacherAssignmentSummary> onSelected;

  @override
  Widget build(BuildContext context) => ListView(
        physics: const AlwaysScrollableScrollPhysics(),
        padding: const EdgeInsets.fromLTRB(
          AppSpacing.x4, AppSpacing.x4, AppSpacing.x4, AppSpacing.x6),
        children: [
          if (historical) ...[
            const _ReadOnlyNotice(),
            const SizedBox(height: AppSpacing.x4),
          ],
          Text('فصولي ومجموعاتي',
              style: Theme.of(context).textTheme.titleLarge),
          const SizedBox(height: AppSpacing.x1),
          Text(
            'اختر المادة والمجموعة لعرض قائمة الطلاب.',
            style: Theme.of(context).textTheme.bodySmall,
          ),
          const SizedBox(height: AppSpacing.x3),
          if (assignments.isEmpty)
            const AppCard(
              child: AppEmptyState(
                message: 'لا توجد تكليفات تدريسية في هذا السياق',
              ),
            )
          else
            ...assignments.map((item) => Padding(
                  padding: const EdgeInsets.only(bottom: AppSpacing.x2),
                  child: _AssignmentCard(
                    assignment: item,
                    onTap: () => onSelected(item),
                  ),
                )),
        ],
      );
}

class _AssignmentCard extends StatelessWidget {
  const _AssignmentCard({required this.assignment, required this.onTap});

  final TeacherAssignmentSummary assignment;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) => Material(
        color: AppColors.surface,
        borderRadius: BorderRadius.circular(AppRadius.card),
        child: InkWell(
          onTap: onTap,
          borderRadius: BorderRadius.circular(AppRadius.card),
          child: Container(
            padding: const EdgeInsets.all(AppSpacing.x4),
            decoration: BoxDecoration(
              border: Border.all(color: AppColors.divider.withOpacity(.75)),
              borderRadius: BorderRadius.circular(AppRadius.card),
            ),
            child: Row(children: [
              Container(
                padding: const EdgeInsets.all(AppSpacing.x3),
                decoration: BoxDecoration(
                  color: RoleVisualTokens.softSurface(AppVisualRole.teacher),
                  borderRadius: BorderRadius.circular(AppRadius.chip),
                ),
                child: const Icon(Icons.menu_book_outlined,
                    color: RoleVisualTokens.teacher),
              ),
              const SizedBox(width: AppSpacing.x3),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      assignment.subject.name,
                      maxLines: 2,
                      overflow: TextOverflow.ellipsis,
                      style: Theme.of(context).textTheme.titleMedium,
                    ),
                    const SizedBox(height: AppSpacing.x1),
                    Text(
                      '${assignment.classroom.name} — ${assignment.section.name}',
                      maxLines: 2,
                      overflow: TextOverflow.ellipsis,
                      style: Theme.of(context).textTheme.bodyMedium,
                    ),
                  ],
                ),
              ),
              const SizedBox(width: AppSpacing.x2),
              const Icon(Icons.chevron_left, color: AppColors.textSecondary),
            ]),
          ),
        ),
      );
}

class _RosterView extends ConsumerStatefulWidget {
  const _RosterView({
    required this.scope,
    required this.assignment,
    required this.historical,
    required this.onBack,
    required this.onAttendance,
  });

  final CacheScope scope;
  final TeacherAssignmentSummary assignment;
  final bool historical;
  final VoidCallback onBack;
  final VoidCallback? onAttendance;

  @override
  ConsumerState<_RosterView> createState() => _RosterViewState();
}

class _RosterViewState extends ConsumerState<_RosterView> {
  String query = '';

  String get date {
    final now = DateTime.now();
    return '${now.year.toString().padLeft(4, '0')}-'
        '${now.month.toString().padLeft(2, '0')}-'
        '${now.day.toString().padLeft(2, '0')}';
  }

  TeacherRosterRequest get request => (
        scope: widget.scope,
        assignmentId: widget.assignment.id,
        date: date,
      );

  @override
  Widget build(BuildContext context) {
    final roster = ref.watch(teacherRosterProvider(request));
    return Column(children: [
      _RosterHeader(onBack: widget.onBack),
      Expanded(
        child: RefreshIndicator(
          onRefresh: () async {
            await ref.refresh(teacherRosterProvider(request).future);
          },
          child: roster.when(
            loading: () => const _AssignmentsLoading(),
            error: (_, __) => _ErrorList(
              message: 'تعذر تحميل قائمة الطلاب',
              onRetry: () => ref.invalidate(teacherRosterProvider(request)),
            ),
            data: (data) => _RosterList(
              roster: data,
              historical: widget.historical,
              query: query,
              onSearch: (value) => setState(() => query = value),
              onAttendance: widget.onAttendance,
            ),
          ),
        ),
      ),
    ]);
  }
}

class _RosterHeader extends StatelessWidget {
  const _RosterHeader({required this.onBack});

  final VoidCallback onBack;

  @override
  Widget build(BuildContext context) => Container(
        color: RoleVisualTokens.softSurface(AppVisualRole.teacher),
        padding: const EdgeInsets.all(AppSpacing.x3),
        child: Row(children: [
          IconButton(
            tooltip: 'رجوع',
            onPressed: onBack,
            icon: const Icon(Icons.arrow_forward),
          ),
          Expanded(
            child: Text('قائمة الطلاب',
                style: Theme.of(context).textTheme.headlineMedium),
          ),
        ]),
      );
}

class _RosterList extends StatelessWidget {
  const _RosterList({
    required this.roster,
    required this.historical,
    required this.query,
    required this.onSearch,
    required this.onAttendance,
  });

  final TeacherAssignmentRoster roster;
  final bool historical;
  final String query;
  final ValueChanged<String> onSearch;
  final VoidCallback? onAttendance;

  @override
  Widget build(BuildContext context) {
    final normalized = query.trim().toLowerCase();
    final students = roster.students.where((item) {
      if (normalized.isEmpty) return true;
      return item.fullName.toLowerCase().contains(normalized) ||
          item.studentCode.toLowerCase().contains(normalized);
    }).toList(growable: false);
    return ListView(
      physics: const AlwaysScrollableScrollPhysics(),
      padding: const EdgeInsets.fromLTRB(
        AppSpacing.x4, AppSpacing.x4, AppSpacing.x4, AppSpacing.x6),
      children: [
        if (historical) ...[
          const _ReadOnlyNotice(),
          const SizedBox(height: AppSpacing.x3),
        ],
        AppCard(
          child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            Text(roster.subject.name,
                style: Theme.of(context).textTheme.titleLarge),
            const SizedBox(height: AppSpacing.x1),
            Text('${roster.classroom.name} — ${roster.section.name}'),
            Text(
              '${_formatDate(roster.date)} • ${roster.totalStudents} طالب',
              style: Theme.of(context).textTheme.bodySmall,
            ),
            if (roster.recordedCount > 0)
              Text(
                'حالة حضور مسجلة لـ ${roster.recordedCount} طالب — للعرض فقط',
                style: Theme.of(context).textTheme.bodySmall,
              ),
            if (onAttendance != null) ...[
              const SizedBox(height: AppSpacing.x3),
              AppPrimaryButton(
                label: 'تسجيل الحضور',
                onPressed: onAttendance,
              ),
            ],
          ]),
        ),
        const SizedBox(height: AppSpacing.x3),
        TextField(
          onChanged: onSearch,
          textInputAction: TextInputAction.search,
          decoration: const InputDecoration(
            hintText: 'البحث باسم الطالب أو رقمه',
            prefixIcon: Icon(Icons.search),
          ),
        ),
        const SizedBox(height: AppSpacing.x3),
        if (roster.students.isEmpty)
          const AppCard(
            child: AppEmptyState(
              message: 'لا يوجد طلاب مسجلون في هذه المجموعة',
            ),
          )
        else if (students.isEmpty)
          const AppCard(
            child: AppEmptyState(message: 'لا توجد نتائج مطابقة للبحث'),
          )
        else
          ...students.map((student) => Padding(
                padding: const EdgeInsets.only(bottom: AppSpacing.x2),
                child: _StudentRow(student: student),
              )),
      ],
    );
  }
}

class _StudentRow extends StatelessWidget {
  const _StudentRow({required this.student});

  final TeacherRosterStudent student;

  @override
  Widget build(BuildContext context) => AppCard(
        child: Row(children: [
          CircleAvatar(
            backgroundColor:
                RoleVisualTokens.softSurface(AppVisualRole.teacher),
            foregroundColor: RoleVisualTokens.teacher,
            child: Text(
              student.fullName.trim().isEmpty
                  ? '—'
                  : student.fullName.trim().characters.first,
            ),
          ),
          const SizedBox(width: AppSpacing.x3),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  student.fullName,
                  maxLines: 2,
                  overflow: TextOverflow.ellipsis,
                  style: Theme.of(context).textTheme.titleMedium,
                ),
                if (student.studentCode.isNotEmpty)
                  Text(
                    student.studentCode,
                    style: Theme.of(context).textTheme.bodySmall,
                  ),
                if (student.attendance?.note.isNotEmpty == true)
                  Text(
                    student.attendance!.note,
                    maxLines: 2,
                    overflow: TextOverflow.ellipsis,
                    style: Theme.of(context).textTheme.bodySmall,
                  ),
              ],
            ),
          ),
          if (student.attendance != null) ...[
            const SizedBox(width: AppSpacing.x2),
            _AttendanceChip(status: student.attendance!.status),
          ],
        ]),
      );
}

class _AttendanceChip extends StatelessWidget {
  const _AttendanceChip({required this.status});

  final String status;

  @override
  Widget build(BuildContext context) {
    final (label, color) = switch (status) {
      'present' => ('حاضر', AppColors.success),
      'late' => ('متأخر', AppColors.warning),
      'absent' => ('غائب', AppColors.error),
      'excused' => ('بعذر', AppColors.info),
      _ => (status, AppColors.textSecondary),
    };
    return Container(
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
}

class _ReadOnlyNotice extends StatelessWidget {
  const _ReadOnlyNotice();

  @override
  Widget build(BuildContext context) => const AppCard(
        child: Row(children: [
          Icon(Icons.history_edu_outlined, color: AppColors.warning),
          SizedBox(width: AppSpacing.x3),
          Expanded(child: Text('سياق سنة دراسية سابقة — للعرض فقط')),
        ]),
      );
}

class _AssignmentsLoading extends StatelessWidget {
  const _AssignmentsLoading();

  @override
  Widget build(BuildContext context) => ListView(
        physics: const AlwaysScrollableScrollPhysics(),
        padding: const EdgeInsets.all(AppSpacing.x4),
        children: const [
          AppSkeletonCard(),
          SizedBox(height: AppSpacing.x3),
          AppSkeletonCard(),
          SizedBox(height: AppSpacing.x3),
          AppSkeletonCard(),
        ],
      );
}

class _ErrorList extends StatelessWidget {
  const _ErrorList({required this.message, required this.onRetry});

  final String message;
  final VoidCallback onRetry;

  @override
  Widget build(BuildContext context) => ListView(
        physics: const AlwaysScrollableScrollPhysics(),
        padding: const EdgeInsets.all(AppSpacing.x4),
        children: [
          AppCard(
            child: Column(children: [
              const Icon(Icons.cloud_off_outlined,
                  size: 42, color: AppColors.error),
              const SizedBox(height: AppSpacing.x3),
              Text(message, style: Theme.of(context).textTheme.titleMedium),
              const SizedBox(height: AppSpacing.x3),
              AppPrimaryButton(label: 'إعادة المحاولة', onPressed: onRetry),
            ]),
          ),
        ],
      );
}

String _formatDate(DateTime value) =>
    '${value.day}/${value.month}/${value.year}';
