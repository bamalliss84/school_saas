import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../../core/design_system/components.dart';
import '../../../../core/design_system/role_visual_tokens.dart';
import '../../../../core/design_system/tokens.dart';
import '../../../../core/local_database/app_database.dart';
import '../../students/domain/teacher_students_models.dart';
import '../../students/presentation/teacher_students_controller.dart';
import '../domain/teacher_attendance_models.dart';
import 'teacher_attendance_controller.dart';

class TeacherAttendanceScreen extends ConsumerStatefulWidget {
  const TeacherAttendanceScreen({
    super.key,
    required this.scope,
    required this.assignment,
    required this.initialDate,
    required this.onBack,
    required this.onDirtyChanged,
  });

  final CacheScope scope;
  final TeacherAssignmentSummary assignment;
  final DateTime initialDate;
  final VoidCallback onBack;
  final ValueChanged<bool> onDirtyChanged;

  @override
  ConsumerState<TeacherAttendanceScreen> createState() =>
      _TeacherAttendanceScreenState();
}

class _TeacherAttendanceScreenState
    extends ConsumerState<TeacherAttendanceScreen> {
  late DateTime selectedDate;
  final drafts = <int, TeacherAttendanceDraft>{};
  String? loadedSignature;
  bool saving = false;

  bool get dirty => drafts.values.any((item) => item.isDirty);

  String get dateKey => _apiDate(selectedDate);

  TeacherRosterRequest get rosterRequest => (
        scope: widget.scope,
        assignmentId: widget.assignment.id,
        date: dateKey,
      );

  @override
  void initState() {
    super.initState();
    selectedDate = widget.initialDate;
  }

  @override
  void didUpdateWidget(covariant TeacherAttendanceScreen oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.scope != widget.scope ||
        oldWidget.assignment.id != widget.assignment.id) {
      selectedDate = widget.initialDate;
      drafts.clear();
      loadedSignature = null;
      _notifyDirty(false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final roster = ref.watch(teacherRosterProvider(rosterRequest));
    return PopScope(
      canPop: false,
      onPopInvoked: (didPop) {
        if (!didPop) _tryLeave();
      },
      child: Column(children: [
        _AttendanceHeader(onBack: _tryLeave),
        Expanded(
          child: roster.when(
            loading: () => const _AttendanceLoading(),
            error: (_, __) => _AttendanceError(
              message:
                  'تعذر تحميل قائمة الطلاب. تحقق من الاتصال وحاول مرة أخرى.',
              onRetry: () => ref.invalidate(
                teacherRosterProvider(rosterRequest),
              ),
            ),
            data: (data) {
              _initializeDrafts(data);
              return _buildContent(data);
            },
          ),
        ),
      ]),
    );
  }

  Widget _buildContent(TeacherAssignmentRoster roster) => Column(children: [
        Expanded(
          child: ListView(
            padding: const EdgeInsets.fromLTRB(
              AppSpacing.x4,
              AppSpacing.x4,
              AppSpacing.x4,
              AppSpacing.x3,
            ),
            children: [
              _AssignmentDateCard(
                roster: roster,
                date: selectedDate,
                onDate: saving ? null : _selectDate,
              ),
              const SizedBox(height: AppSpacing.x3),
              Row(children: [
                Expanded(
                  child: Text(
                    'الحضور اليومي',
                    style: Theme.of(context).textTheme.titleLarge,
                  ),
                ),
                TextButton.icon(
                  onPressed: saving || roster.students.isEmpty
                      ? null
                      : () => _markAllPresent(roster.students),
                  icon: const Icon(Icons.done_all),
                  label: const Text('الجميع حاضر'),
                ),
              ]),
              const SizedBox(height: AppSpacing.x2),
              if (roster.students.isEmpty)
                const AppCard(
                  child: AppEmptyState(
                    message: 'لا يوجد طلاب مسجلون في هذه المجموعة',
                  ),
                )
              else
                ...roster.students.map((student) => Padding(
                      padding:
                          const EdgeInsets.only(bottom: AppSpacing.x2),
                      child: _AttendanceStudentCard(
                        student: student,
                        draft: drafts[student.enrollmentId]!,
                        enabled: !saving,
                        onStatus: (status) =>
                            _setStatus(student.enrollmentId, status),
                        onNote: () => _editNote(student),
                      ),
                    )),
            ],
          ),
        ),
        _SaveBar(
          dirty: dirty,
          saving: saving,
          changedCount: drafts.values.where((item) => item.isDirty).length,
          onSave: _save,
        ),
      ]);

  void _initializeDrafts(TeacherAssignmentRoster roster) {
    final signature = [
      roster.assignmentId,
      _apiDate(roster.date),
      ...roster.students.map((student) =>
          '${student.enrollmentId}:${student.attendance?.status}:${student.attendance?.note}'),
    ].join('|');
    if (loadedSignature == signature) return;
    drafts
      ..clear()
      ..addEntries(roster.students.map((student) {
        final status = student.attendance?.status;
        final note = student.attendance?.note ?? '';
        return MapEntry(
          student.enrollmentId,
          TeacherAttendanceDraft(
            enrollmentId: student.enrollmentId,
            originalStatus: status,
            pendingStatus: status,
            originalNote: note,
            pendingNote: note,
          ),
        );
      }));
    loadedSignature = signature;
    _notifyDirty(false);
  }

  void _setStatus(int enrollmentId, String status) {
    final current = drafts[enrollmentId]!;
    setState(() => drafts[enrollmentId] = current.copyWith(
          pendingStatus: status,
        ));
    _notifyDirty(dirty);
  }

  void _markAllPresent(List<TeacherRosterStudent> students) {
    setState(() {
      for (final student in students) {
        final current = drafts[student.enrollmentId]!;
        drafts[student.enrollmentId] = current.copyWith(
          pendingStatus: 'present',
        );
      }
    });
    _notifyDirty(dirty);
  }

  Future<void> _editNote(TeacherRosterStudent student) async {
    final current = drafts[student.enrollmentId]!;
    final note = await showModalBottomSheet<String>(
      context: context,
      isScrollControlled: true,
      builder: (_) => _NoteEditorSheet(
        studentName: student.fullName,
        initialNote: current.pendingNote,
      ),
    );
    if (note == null || !mounted) return;
    final pendingStatus = current.pendingStatus ?? 'present';
    setState(() => drafts[student.enrollmentId] = current.copyWith(
          pendingStatus: pendingStatus,
          pendingNote: note,
        ));
    _notifyDirty(dirty);
  }

  Future<void> _selectDate() async {
    if (dirty && !await _confirmDiscard()) return;
    if (!mounted) return;
    final chosen = await showDatePicker(
      context: context,
      initialDate: selectedDate,
      firstDate: DateTime(2000),
      lastDate: DateTime(2100),
      helpText: 'اختر تاريخ الحضور',
    );
    if (chosen == null || !mounted || _sameDate(chosen, selectedDate)) return;
    setState(() {
      selectedDate = chosen;
      drafts.clear();
      loadedSignature = null;
    });
    _notifyDirty(false);
  }

  Future<void> _save() async {
    final changes = drafts.values
        .where((item) => item.isDirty && item.pendingStatus != null)
        .toList(growable: false);
    if (changes.isEmpty || saving) return;
    setState(() => saving = true);
    try {
      final result = await ref
          .read(teacherAttendanceRepositoryProvider)
          .saveBulk(
            assignmentId: widget.assignment.id,
            date: dateKey,
            changes: changes,
          );
      if (!result.success) throw StateError('attendance save rejected');
      final canonical = await ref.refresh(
        teacherRosterProvider(rosterRequest).future,
      );
      if (!mounted) return;
      setState(() {
        loadedSignature = null;
        saving = false;
        _initializeDrafts(canonical);
      });
      _notifyDirty(false);
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('تم حفظ حضور ${result.total} طالب بنجاح'),
        ),
      );
    } catch (error) {
      if (!mounted) return;
      setState(() => saving = false);
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(_attendanceErrorMessage(error))),
      );
    }
  }

  Future<void> _tryLeave() async {
    if (dirty && !await _confirmDiscard()) return;
    widget.onDirtyChanged(false);
    widget.onBack();
  }

  Future<bool> _confirmDiscard() async {
    final discard = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('لديك تغييرات غير محفوظة'),
        content: const Text('هل تريد تجاهل مسودة الحضور؟'),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context, false),
            child: const Text('متابعة التعديل'),
          ),
          FilledButton(
            onPressed: () => Navigator.pop(context, true),
            child: const Text('تجاهل التغييرات'),
          ),
        ],
      ),
    );
    return discard ?? false;
  }

  void _notifyDirty(bool value) {
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (mounted) widget.onDirtyChanged(value);
    });
  }
}

class _NoteEditorSheet extends StatefulWidget {
  const _NoteEditorSheet({
    required this.studentName,
    required this.initialNote,
  });

  final String studentName;
  final String initialNote;

  @override
  State<_NoteEditorSheet> createState() => _NoteEditorSheetState();
}

class _NoteEditorSheetState extends State<_NoteEditorSheet> {
  late final TextEditingController controller;

  @override
  void initState() {
    super.initState();
    controller = TextEditingController(text: widget.initialNote);
  }

  @override
  void dispose() {
    controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) => AnimatedPadding(
        duration: const Duration(milliseconds: 180),
        curve: Curves.easeOut,
        padding: EdgeInsets.only(
          bottom: MediaQuery.viewInsetsOf(context).bottom,
        ),
        child: SafeArea(
          top: false,
          child: SingleChildScrollView(
            keyboardDismissBehavior: ScrollViewKeyboardDismissBehavior.onDrag,
            padding: const EdgeInsets.all(AppSpacing.x4),
            child: Column(mainAxisSize: MainAxisSize.min, children: [
              Text(
                'ملاحظة — ${widget.studentName}',
                maxLines: 2,
                overflow: TextOverflow.ellipsis,
                textAlign: TextAlign.center,
                style: Theme.of(context).textTheme.titleMedium,
              ),
              const SizedBox(height: AppSpacing.x3),
              TextField(
                controller: controller,
                autofocus: true,
                minLines: 2,
                maxLines: 4,
                decoration: const InputDecoration(
                  hintText: 'ملاحظة اختيارية',
                ),
              ),
              const SizedBox(height: AppSpacing.x3),
              Row(children: [
                Expanded(
                  child: OutlinedButton(
                    onPressed: () => Navigator.pop(context),
                    child: const Text('إلغاء'),
                  ),
                ),
                const SizedBox(width: AppSpacing.x2),
                Expanded(
                  child: FilledButton(
                    onPressed: () =>
                        Navigator.pop(context, controller.text.trim()),
                    child: const Text('إضافة إلى المسودة'),
                  ),
                ),
              ]),
            ]),
          ),
        ),
      );
}

class _AttendanceHeader extends StatelessWidget {
  const _AttendanceHeader({required this.onBack});
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
            child: Text('تسجيل الحضور',
                style: Theme.of(context).textTheme.headlineMedium),
          ),
        ]),
      );
}

class _AssignmentDateCard extends StatelessWidget {
  const _AssignmentDateCard({
    required this.roster,
    required this.date,
    required this.onDate,
  });

  final TeacherAssignmentRoster roster;
  final DateTime date;
  final VoidCallback? onDate;

  @override
  Widget build(BuildContext context) => AppCard(
        child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Text(roster.subject.name,
              style: Theme.of(context).textTheme.titleLarge),
          const SizedBox(height: AppSpacing.x1),
          Text('${roster.classroom.name} — ${roster.section.name}'),
          const SizedBox(height: AppSpacing.x2),
          OutlinedButton.icon(
            onPressed: onDate,
            icon: const Icon(Icons.calendar_today_outlined),
            label: Text(_displayDate(date)),
          ),
        ]),
      );
}

class _AttendanceStudentCard extends StatelessWidget {
  const _AttendanceStudentCard({
    required this.student,
    required this.draft,
    required this.enabled,
    required this.onStatus,
    required this.onNote,
  });

  final TeacherRosterStudent student;
  final TeacherAttendanceDraft draft;
  final bool enabled;
  final ValueChanged<String> onStatus;
  final VoidCallback onNote;

  @override
  Widget build(BuildContext context) => AppCard(
        child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Row(children: [
            CircleAvatar(
              backgroundColor:
                  RoleVisualTokens.softSurface(AppVisualRole.teacher),
              foregroundColor: RoleVisualTokens.teacher,
              child: Text(student.fullName.trim().isEmpty
                  ? '—'
                  : student.fullName.trim().characters.first),
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
                    Text(student.studentCode,
                        style: Theme.of(context).textTheme.bodySmall),
                ],
              ),
            ),
            IconButton(
              tooltip: 'ملاحظة',
              onPressed: enabled ? onNote : null,
              icon: Icon(
                draft.pendingNote.isEmpty
                    ? Icons.note_add_outlined
                    : Icons.sticky_note_2_outlined,
                color: draft.pendingNote.isEmpty
                    ? AppColors.textSecondary
                    : RoleVisualTokens.teacher,
              ),
            ),
          ]),
          const SizedBox(height: AppSpacing.x2),
          if (draft.isDirty) ...[
            Text(
              'معدّل في المسودة',
              style: Theme.of(context).textTheme.bodySmall?.copyWith(
                    color: RoleVisualTokens.teacher,
                    fontWeight: FontWeight.w700,
                  ),
            ),
            const SizedBox(height: AppSpacing.x1),
          ],
          Wrap(
            spacing: AppSpacing.x2,
            runSpacing: AppSpacing.x2,
            children: teacherAttendanceStatuses.map((status) {
              final selected = draft.pendingStatus == status;
              return ChoiceChip(
                selected: selected,
                onSelected: enabled ? (_) => onStatus(status) : null,
                label: Text(teacherAttendanceLabel(status)),
                selectedColor:
                    RoleVisualTokens.softSurface(AppVisualRole.teacher),
                side: BorderSide(
                  color: selected
                      ? RoleVisualTokens.teacher
                      : AppColors.divider,
                ),
              );
            }).toList(growable: false),
          ),
          if (draft.pendingNote.isNotEmpty) ...[
            const SizedBox(height: AppSpacing.x2),
            Text(
              draft.pendingNote,
              maxLines: 2,
              overflow: TextOverflow.ellipsis,
              style: Theme.of(context).textTheme.bodySmall,
            ),
          ],
        ]),
      );
}

class _SaveBar extends StatelessWidget {
  const _SaveBar({
    required this.dirty,
    required this.saving,
    required this.changedCount,
    required this.onSave,
  });

  final bool dirty;
  final bool saving;
  final int changedCount;
  final VoidCallback onSave;

  @override
  Widget build(BuildContext context) => SafeArea(
        top: false,
        child: Container(
          padding: const EdgeInsets.all(AppSpacing.x3),
          decoration: const BoxDecoration(
            color: AppColors.surface,
            border: Border(top: BorderSide(color: AppColors.divider)),
          ),
          child: AppPrimaryButton(
            label: saving
                ? 'جارٍ الحفظ...'
                : dirty
                    ? 'حفظ التغييرات ($changedCount)'
                    : 'لا توجد تغييرات',
            onPressed: dirty && !saving ? onSave : null,
          ),
        ),
      );
}

class _AttendanceLoading extends StatelessWidget {
  const _AttendanceLoading();
  @override
  Widget build(BuildContext context) => ListView(
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

class _AttendanceError extends StatelessWidget {
  const _AttendanceError({required this.message, required this.onRetry});
  final String message;
  final VoidCallback onRetry;

  @override
  Widget build(BuildContext context) => ListView(
        padding: const EdgeInsets.all(AppSpacing.x4),
        children: [
          AppCard(
            child: Column(children: [
              const Icon(Icons.error_outline,
                  size: 42, color: AppColors.error),
              const SizedBox(height: AppSpacing.x3),
              Text(message, textAlign: TextAlign.center),
              const SizedBox(height: AppSpacing.x3),
              AppPrimaryButton(label: 'إعادة المحاولة', onPressed: onRetry),
            ]),
          ),
        ],
      );
}

String _attendanceErrorMessage(Object error) {
  var source = error.toString();
  if (error is DioException) {
    source = error.response?.data.toString() ?? source;
    if (error.response?.statusCode == 403) {
      return 'هذا السياق للعرض فقط ولا يسمح بتعديل الحضور.';
    }
  }
  final lower = source.toLowerCase();
  if (lower.contains('no academic term covers')) {
    return 'لا توجد فترة دراسية تغطي التاريخ المحدد.';
  }
  if (lower.contains('multiple academic terms') ||
      lower.contains('ambiguous')) {
    return 'إعداد الفترات الدراسية لهذا التاريخ غير واضح. تواصل مع الإدارة.';
  }
  if (lower.contains('invalid attendance scope') ||
      lower.contains('invalid attendance relationships')) {
    return 'لا يمكن حفظ الحضور لهذه المجموعة أو لهذا التاريخ.';
  }
  if (lower.contains('status')) return 'حالة حضور غير صالحة.';
  return 'تعذر حفظ الحضور. تحقق من الاتصال وحاول مرة أخرى.';
}

String _apiDate(DateTime value) =>
    '${value.year.toString().padLeft(4, '0')}-'
    '${value.month.toString().padLeft(2, '0')}-'
    '${value.day.toString().padLeft(2, '0')}';

String _displayDate(DateTime value) =>
    '${value.day}/${value.month}/${value.year}';

bool _sameDate(DateTime first, DateTime second) =>
    first.year == second.year &&
    first.month == second.month &&
    first.day == second.day;
