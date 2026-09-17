import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../../core/design_system/role_visual_tokens.dart';
import '../../../../core/errors/app_failure.dart';
import '../../../../core/local_database/app_database.dart';
import '../../homework/presentation/teacher_homework_screen.dart';
import '../../students/domain/teacher_students_models.dart';
import '../../students/presentation/teacher_students_controller.dart';
import '../domain/teacher_exam_models.dart';
import 'teacher_exam_controller.dart';

const _teacherBlue = RoleVisualTokens.teacher;

class TeacherWorkCenterScreen extends StatefulWidget {
  const TeacherWorkCenterScreen({
    super.key,
    required this.scope,
    required this.historical,
  });

  final CacheScope scope;
  final bool historical;

  @override
  State<TeacherWorkCenterScreen> createState() => _TeacherWorkCenterScreenState();
}

class _TeacherWorkCenterScreenState extends State<TeacherWorkCenterScreen> {
  int index = 0;

  @override
  Widget build(BuildContext context) => Column(children: [
        Padding(
          padding: const EdgeInsets.fromLTRB(16, 12, 16, 4),
          child: SegmentedButton<int>(
            segments: const [
              ButtonSegment(value: 0, icon: Icon(Icons.assignment_outlined), label: Text('الواجبات')),
              ButtonSegment(value: 1, icon: Icon(Icons.fact_check_outlined), label: Text('الاختبارات والنتائج')),
            ],
            selected: {index},
            showSelectedIcon: false,
            onSelectionChanged: (value) => setState(() => index = value.first),
          ),
        ),
        Expanded(
          child: IndexedStack(index: index, children: [
            TeacherHomeworkScreen(scope: widget.scope, historical: widget.historical),
            TeacherExamScreen(scope: widget.scope, historical: widget.historical),
          ]),
        ),
      ]);
}

class TeacherExamScreen extends ConsumerStatefulWidget {
  const TeacherExamScreen({
    super.key,
    required this.scope,
    required this.historical,
  });

  final CacheScope scope;
  final bool historical;

  @override
  ConsumerState<TeacherExamScreen> createState() => _TeacherExamScreenState();
}

class _TeacherExamScreenState extends ConsumerState<TeacherExamScreen> {
  int? assignmentId;

  ({CacheScope scope, int? assignmentId}) get query =>
      (scope: widget.scope, assignmentId: assignmentId);

  @override
  Widget build(BuildContext context) {
    final assignments = ref.watch(teacherAssignmentsProvider(widget.scope));
    final exams = ref.watch(teacherExamsProvider(query));
    return Column(children: [
      const Padding(
        padding: EdgeInsets.fromLTRB(18, 14, 18, 8),
        child: Row(children: [
          Icon(Icons.fact_check_outlined, color: _teacherBlue, size: 32),
          SizedBox(width: 10),
          Expanded(
            child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
              Text('الاختبارات والنتائج', style: TextStyle(fontSize: 22, fontWeight: FontWeight.w800)),
              Text('إدارة اختبارات تكليفاتك وإدخال نتائج الطلاب', style: TextStyle(color: Color(0xff667085))),
            ]),
          ),
        ]),
      ),
      Padding(
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 6),
        child: assignments.when(
          loading: () => const LinearProgressIndicator(),
          error: (error, _) => Text(_message(error)),
          data: (rows) => DropdownButtonFormField<int?>(
            value: assignmentId,
            isExpanded: true,
            decoration: const InputDecoration(labelText: 'التكليف', prefixIcon: Icon(Icons.school_outlined)),
            items: [
              const DropdownMenuItem<int?>(value: null, child: Text('كل تكليفاتي')),
              ...rows.map((row) => DropdownMenuItem<int?>(
                    value: row.id,
                    child: Text(_assignmentLabel(row), maxLines: 1, overflow: TextOverflow.ellipsis),
                  )),
            ],
            onChanged: (value) => setState(() => assignmentId = value),
          ),
        ),
      ),
      if (!widget.historical)
        const Padding(
          padding: EdgeInsets.fromLTRB(16, 4, 16, 8),
          child: _ContractNotice(),
        ),
      Expanded(
        child: exams.when(
          loading: () => const Center(child: CircularProgressIndicator()),
          error: (error, _) => _ExamError(
            message: _message(error),
            retry: () => ref.invalidate(teacherExamsProvider(query)),
          ),
          data: (items) => items.isEmpty
              ? const Center(child: Text('لا توجد اختبارات ضمن هذا التكليف'))
              : RefreshIndicator(
                  onRefresh: () async => ref.invalidate(teacherExamsProvider(query)),
                  child: ListView.separated(
                    padding: const EdgeInsets.fromLTRB(16, 6, 16, 24),
                    itemCount: items.length,
                    separatorBuilder: (_, __) => const SizedBox(height: 10),
                    itemBuilder: (context, index) {
                      final exam = items[index];
                      final assignment = _findAssignment(
                        assignments.asData?.value,
                        exam.assignmentId,
                      );
                      return _ExamCard(
                        exam: exam,
                        assignment: assignment,
                        onTap: () => _open(exam, assignment),
                      );
                    },
                  ),
                ),
        ),
      ),
    ]);
  }

  Future<void> _open(TeacherExam exam, TeacherAssignmentSummary? assignment) async {
    await Navigator.push(
      context,
      MaterialPageRoute(
        builder: (_) => TeacherExamDetailScreen(
          scope: widget.scope,
          exam: exam,
          assignment: assignment,
          historical: widget.historical,
        ),
      ),
    );
    ref.invalidate(teacherExamsProvider(query));
  }
}

class _ContractNotice extends StatelessWidget {
  const _ContractNotice();
  @override
  Widget build(BuildContext context) => Container(
        padding: const EdgeInsets.all(10),
        decoration: BoxDecoration(color: const Color(0xffeef4ff), borderRadius: BorderRadius.circular(12)),
        child: const Row(children: [
          Icon(Icons.info_outline, size: 19, color: _teacherBlue),
          SizedBox(width: 8),
          Expanded(child: Text('إنشاء اختبار جديد يتطلب فصلًا دراسيًا من الخادم؛ يمكنك حاليًا إدارة الاختبارات الموجودة ونتائجها.')),
        ]),
      );
}

class _ExamCard extends StatelessWidget {
  const _ExamCard({required this.exam, required this.assignment, required this.onTap});
  final TeacherExam exam;
  final TeacherAssignmentSummary? assignment;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) => Card(
        child: ListTile(
          contentPadding: const EdgeInsets.all(14),
          leading: const CircleAvatar(
            backgroundColor: Color(0xffedf2ff),
            child: Icon(Icons.quiz_outlined, color: _teacherBlue),
          ),
          title: Text(exam.title, style: const TextStyle(fontWeight: FontWeight.w700)),
          subtitle: Text([
            if (assignment != null) _assignmentLabel(assignment!),
            '${_date(exam.examDate)} • ${_number(exam.totalMarks)} درجة',
            _examStatus(exam.status),
          ].join('\n')),
          trailing: const Icon(Icons.chevron_left),
          onTap: onTap,
        ),
      );
}

class TeacherExamDetailScreen extends ConsumerStatefulWidget {
  const TeacherExamDetailScreen({
    super.key,
    required this.scope,
    required this.exam,
    required this.historical,
    this.assignment,
  });

  final CacheScope scope;
  final TeacherExam exam;
  final TeacherAssignmentSummary? assignment;
  final bool historical;

  @override
  ConsumerState<TeacherExamDetailScreen> createState() => _TeacherExamDetailScreenState();
}

class _TeacherExamDetailScreenState extends ConsumerState<TeacherExamDetailScreen> {
  final drafts = <int, TeacherExamResultEditState>{};
  bool initialized = false;
  bool saving = false;
  bool dirty = false;

  ({CacheScope scope, int examId}) get resultQuery =>
      (scope: widget.scope, examId: widget.exam.id);

  TeacherRosterRequest get rosterQuery => (
        scope: widget.scope,
        assignmentId: widget.exam.assignmentId,
        date: _apiDate(widget.exam.examDate),
      );

  @override
  Widget build(BuildContext context) {
    final results = ref.watch(teacherExamResultsProvider(resultQuery));
    final summary = ref.watch(teacherExamSummaryProvider(resultQuery));
    final roster = ref.watch(teacherRosterProvider(rosterQuery));
    final readyResults = results.asData?.value;
    final readyRoster = roster.asData?.value;
    if (!initialized && readyResults != null && readyRoster != null) {
      _initialize(readyRoster, readyResults);
    }
    return PopScope(
      canPop: !dirty,
      onPopInvokedWithResult: (didPop, _) async {
        if (!didPop && await _confirmDiscard() && mounted) Navigator.pop(context);
      },
      child: Scaffold(
        appBar: AppBar(
          title: Text(widget.exam.title),
          actions: [
            if (!widget.historical && widget.exam.editable)
              IconButton(tooltip: 'تعديل الاختبار', onPressed: _editExam, icon: const Icon(Icons.edit_outlined)),
            if (!widget.historical && widget.exam.editable)
              IconButton(tooltip: 'حذف الاختبار', onPressed: _deleteExam, icon: const Icon(Icons.delete_outline)),
          ],
        ),
        body: SafeArea(
          child: Column(children: [
            _ExamSummary(
              exam: widget.exam,
              assignment: widget.assignment,
              statistics: summary.asData?.value,
            ),
            Expanded(
              child: _body(results, roster),
            ),
            if (!widget.historical && initialized)
              SafeArea(
                top: false,
                child: Padding(
                  padding: const EdgeInsets.fromLTRB(16, 8, 16, 12),
                  child: FilledButton.icon(
                    onPressed: dirty && !saving ? _save : null,
                    icon: saving
                        ? const SizedBox.square(dimension: 18, child: CircularProgressIndicator(strokeWidth: 2))
                        : const Icon(Icons.save_outlined),
                    label: Text(saving ? 'جارٍ الحفظ...' : 'حفظ النتائج'),
                  ),
                ),
              ),
          ]),
        ),
      ),
    );
  }

  Widget _body(
    AsyncValue<List<TeacherExamResult>> results,
    AsyncValue<TeacherAssignmentRoster> roster,
  ) {
    if (results.isLoading || roster.isLoading) {
      return const Center(child: CircularProgressIndicator());
    }
    if (results.hasError) {
      return _ExamError(message: _message(results.error!), retry: _refresh);
    }
    if (roster.hasError) {
      return _ExamError(message: _message(roster.error!), retry: _refresh);
    }
    final students = roster.requireValue.students;
    if (students.isEmpty) return const Center(child: Text('لا يوجد طلاب في هذا التكليف'));
    return ListView.separated(
      keyboardDismissBehavior: ScrollViewKeyboardDismissBehavior.onDrag,
      padding: const EdgeInsets.all(16),
      itemCount: students.length,
      separatorBuilder: (_, __) => const SizedBox(height: 10),
      itemBuilder: (context, index) {
        final student = students[index];
        final draft = drafts[student.enrollmentId]!;
        return _ResultEditorCard(
          student: student,
          draft: draft,
          readOnly: widget.historical || !draft.editable,
          onChanged: () => setState(() => dirty = true),
          onSubmit: draft.submittable && !dirty
              ? () => _submit(draft.resultId!)
              : null,
        );
      },
    );
  }

  void _initialize(TeacherAssignmentRoster roster, List<TeacherExamResult> results) {
    final byEnrollment = {for (final result in results) result.enrollmentId: result};
    for (final student in roster.students) {
      final result = byEnrollment[student.enrollmentId];
      drafts[student.enrollmentId] = TeacherExamResultEditState.fromResult(
        enrollmentId: student.enrollmentId,
        result: result,
      );
    }
    initialized = true;
  }

  Future<void> _save() async {
    final invalid = drafts.values.any((draft) =>
        draft.usesScore &&
        (double.tryParse(draft.scoreText) == null ||
            double.parse(draft.scoreText) < 0 ||
            double.parse(draft.scoreText) > widget.exam.totalMarks));
    if (invalid) {
      _snack('أدخل درجة صحيحة من 0 إلى ${_number(widget.exam.totalMarks)} لكل طالب حاضر.');
      return;
    }
    setState(() => saving = true);
    try {
      final saved = await ref.read(teacherExamRepositoryProvider).saveResults(
            widget.exam.id,
            drafts.values
                .where((draft) => draft.editable)
                .map((draft) => draft.toDraft())
                .toList(),
          );
      if (!mounted) return;
      setState(() {
        _applyCanonicalResults(saved);
        dirty = false;
      });
      ref.invalidate(teacherExamResultsProvider(resultQuery));
      ref.invalidate(teacherExamSummaryProvider(resultQuery));
      _snack('تم حفظ النتائج.');
    } catch (error) {
      _snack(_message(error));
    } finally {
      if (mounted) setState(() => saving = false);
    }
  }

  Future<void> _submit(int resultId) async {
    try {
      final submitted =
          await ref.read(teacherExamRepositoryProvider).submitResult(resultId);
      if (!mounted) return;
      setState(() => drafts[submitted.enrollmentId]?.applyCanonical(submitted));
      ref.invalidate(teacherExamResultsProvider(resultQuery));
      ref.invalidate(teacherExamSummaryProvider(resultQuery));
      _snack('تم إرسال النتيجة للاعتماد.');
    } catch (error) {
      _snack(_message(error));
    }
  }

  void _applyCanonicalResults(List<TeacherExamResult> results) {
    for (final result in results) {
      drafts[result.enrollmentId]?.applyCanonical(result);
    }
  }

  Future<void> _editExam() async {
    final changed = await Navigator.push<bool>(
      context,
      MaterialPageRoute(builder: (_) => _TeacherExamEditor(exam: widget.exam)),
    );
    if (changed == true && mounted) Navigator.pop(context);
  }

  Future<void> _deleteExam() async {
    final yes = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('حذف الاختبار؟'),
        content: const Text('يسمح الخادم بحذف الاختبار المسودة الفارغ فقط.'),
        actions: [
          TextButton(onPressed: () => Navigator.pop(context, false), child: const Text('إلغاء')),
          FilledButton(onPressed: () => Navigator.pop(context, true), child: const Text('حذف')),
        ],
      ),
    );
    if (yes != true) return;
    try {
      await ref.read(teacherExamRepositoryProvider).deleteExam(widget.exam.id);
      if (mounted) Navigator.pop(context);
    } catch (error) {
      _snack(_message(error));
    }
  }

  Future<bool> _confirmDiscard() async {
    if (!dirty) return true;
    return await showDialog<bool>(
          context: context,
          builder: (context) => AlertDialog(
            title: const Text('تغييرات غير محفوظة'),
            content: const Text('هل تريد تجاهل تعديلات النتائج؟'),
            actions: [
              TextButton(onPressed: () => Navigator.pop(context, false), child: const Text('متابعة التعديل')),
              FilledButton(onPressed: () => Navigator.pop(context, true), child: const Text('تجاهل')),
            ],
          ),
        ) ??
        false;
  }

  void _refresh() {
    ref.invalidate(teacherExamResultsProvider(resultQuery));
    ref.invalidate(teacherExamSummaryProvider(resultQuery));
    ref.invalidate(teacherRosterProvider(rosterQuery));
  }

  void _snack(String message) {
    if (mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(message)));
  }
}

class _ResultEditorCard extends StatelessWidget {
  const _ResultEditorCard({
    required this.student,
    required this.draft,
    required this.readOnly,
    required this.onChanged,
    this.onSubmit,
  });
  final TeacherRosterStudent student;
  final TeacherExamResultEditState draft;
  final bool readOnly;
  final VoidCallback onChanged;
  final VoidCallback? onSubmit;

  @override
  Widget build(BuildContext context) => Card(
        child: Padding(
          padding: const EdgeInsets.all(14),
          child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            Text(student.fullName, style: const TextStyle(fontWeight: FontWeight.w700)),
            if (student.studentCode.isNotEmpty) Text(student.studentCode, style: Theme.of(context).textTheme.bodySmall),
            const SizedBox(height: 10),
            DropdownButtonFormField<String>(
              value: draft.status,
              decoration: const InputDecoration(labelText: 'الحالة'),
              items: teacherResultStatusLabels.entries
                  .map((entry) => DropdownMenuItem(value: entry.key, child: Text(entry.value)))
                  .toList(),
              onChanged: readOnly
                  ? null
                  : (value) {
                      if (value == null) return;
                      draft.selectStatus(value);
                      onChanged();
                    },
            ),
            if (draft.usesScore) ...[
              const SizedBox(height: 8),
              TextFormField(
                key: ValueKey('score-${draft.enrollmentId}'),
                initialValue: draft.scoreText,
                enabled: !readOnly,
                keyboardType: const TextInputType.numberWithOptions(decimal: true),
                decoration: const InputDecoration(labelText: 'الدرجة'),
                onChanged: (value) {
                  draft.scoreText = value;
                  onChanged();
                },
              ),
            ],
            const SizedBox(height: 8),
            TextFormField(
              key: ValueKey('remarks-${draft.enrollmentId}'),
              initialValue: draft.remarks,
              enabled: !readOnly,
              minLines: 1,
              maxLines: 3,
              decoration: const InputDecoration(labelText: 'ملاحظات (اختياري)'),
              onChanged: (value) {
                draft.remarks = value;
                onChanged();
              },
            ),
            const SizedBox(height: 8),
            Row(children: [
              Chip(label: Text(teacherResultWorkflowLabels[draft.workflowStatus] ?? draft.workflowStatus)),
              const Spacer(),
              if (onSubmit != null) TextButton.icon(onPressed: onSubmit, icon: const Icon(Icons.send_outlined), label: const Text('إرسال للاعتماد')),
            ]),
          ]),
        ),
      );
}

class _ExamSummary extends StatelessWidget {
  const _ExamSummary({
    required this.exam,
    this.assignment,
    this.statistics,
  });
  final TeacherExam exam;
  final TeacherAssignmentSummary? assignment;
  final Map<String, dynamic>? statistics;
  @override
  Widget build(BuildContext context) => Container(
        width: double.infinity,
        color: const Color(0xfff3f6fc),
        padding: const EdgeInsets.all(16),
        child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Text([
            if (assignment != null) _assignmentLabel(assignment!),
            '${_date(exam.examDate)} • ${_number(exam.totalMarks)} درجة',
            _examStatus(exam.status),
          ].join('\n')),
          if (statistics != null) ...[
            const SizedBox(height: 8),
            Wrap(spacing: 8, runSpacing: 6, children: [
              Chip(label: Text('النتائج: ${statistics!['total_results'] ?? 0}')),
              Chip(label: Text('المصحح: ${statistics!['scored_results'] ?? 0}')),
              if (statistics!['average'] != null)
                Chip(label: Text('المتوسط: ${statistics!['average']}')),
            ]),
          ],
        ]),
      );
}

class _TeacherExamEditor extends ConsumerStatefulWidget {
  const _TeacherExamEditor({required this.exam});
  final TeacherExam exam;
  @override
  ConsumerState<_TeacherExamEditor> createState() => _TeacherExamEditorState();
}

class _TeacherExamEditorState extends ConsumerState<_TeacherExamEditor> {
  late final TextEditingController title;
  late final TextEditingController marks;
  late final TextEditingController notes;
  late DateTime date;
  bool saving = false;

  @override
  void initState() {
    super.initState();
    title = TextEditingController(text: widget.exam.title);
    marks = TextEditingController(text: _number(widget.exam.totalMarks));
    notes = TextEditingController(text: widget.exam.notes);
    date = widget.exam.examDate;
  }

  @override
  void dispose() {
    title.dispose();
    marks.dispose();
    notes.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) => Scaffold(
        appBar: AppBar(title: const Text('تعديل الاختبار')),
        body: SafeArea(
          child: ListView(
            padding: EdgeInsets.fromLTRB(16, 16, 16, 24 + MediaQuery.viewInsetsOf(context).bottom),
            children: [
              TextField(controller: title, decoration: const InputDecoration(labelText: 'عنوان الاختبار')),
              const SizedBox(height: 12),
              ListTile(
                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12), side: const BorderSide(color: Color(0xffd0d5dd))),
                title: Text('تاريخ الاختبار: ${_date(date)}'),
                leading: const Icon(Icons.calendar_month_outlined),
                onTap: _pickDate,
              ),
              const SizedBox(height: 12),
              TextField(controller: marks, keyboardType: const TextInputType.numberWithOptions(decimal: true), decoration: const InputDecoration(labelText: 'الدرجة الكلية')),
              const SizedBox(height: 12),
              TextField(controller: notes, minLines: 3, maxLines: 6, decoration: const InputDecoration(labelText: 'ملاحظات')),
              const SizedBox(height: 20),
              FilledButton(onPressed: saving ? null : _save, child: Text(saving ? 'جارٍ الحفظ...' : 'حفظ التعديلات')),
            ],
          ),
        ),
      );

  Future<void> _pickDate() async {
    final picked = await showDatePicker(
      context: context,
      firstDate: DateTime(2020),
      lastDate: DateTime(2100),
      initialDate: date,
    );
    if (picked != null) setState(() => date = picked);
  }

  Future<void> _save() async {
    final total = double.tryParse(marks.text.trim());
    if (title.text.trim().isEmpty || total == null || total <= 0) {
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('أدخل عنوانًا ودرجة كلية صحيحة.')));
      return;
    }
    setState(() => saving = true);
    try {
      await ref.read(teacherExamRepositoryProvider).updateExam(TeacherExam(
            id: widget.exam.id,
            academicYearId: widget.exam.academicYearId,
            academicTermId: widget.exam.academicTermId,
            assignmentId: widget.exam.assignmentId,
            examTypeId: widget.exam.examTypeId,
            title: title.text.trim(),
            examDate: date,
            totalMarks: total,
            status: widget.exam.status,
            classroomId: widget.exam.classroomId,
            sectionId: widget.exam.sectionId,
            subjectId: widget.exam.subjectId,
            notes: notes.text.trim(),
          ));
      if (mounted) Navigator.pop(context, true);
    } catch (error) {
      if (mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(_message(error))));
    } finally {
      if (mounted) setState(() => saving = false);
    }
  }
}

class _ExamError extends StatelessWidget {
  const _ExamError({required this.message, required this.retry});
  final String message;
  final VoidCallback retry;
  @override
  Widget build(BuildContext context) => Center(
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: Column(mainAxisSize: MainAxisSize.min, children: [
            const Icon(Icons.error_outline, size: 42),
            const SizedBox(height: 8),
            Text(message, textAlign: TextAlign.center),
            TextButton(onPressed: retry, child: const Text('إعادة المحاولة')),
          ]),
        ),
      );
}

String _assignmentLabel(TeacherAssignmentSummary value) =>
    '${value.subject.name} • ${value.classroom.name} / ${value.section.name}';

TeacherAssignmentSummary? _findAssignment(
  List<TeacherAssignmentSummary>? values,
  int id,
) {
  if (values == null) return null;
  for (final value in values) {
    if (value.id == id) return value;
  }
  return null;
}

String _examStatus(String status) => switch (status) {
      'draft' => 'مسودة',
      'published' => 'منشور',
      'closed' => 'مغلق',
      'cancelled' => 'ملغي',
      _ => status,
    };

String _date(DateTime value) => '${value.year}/${value.month.toString().padLeft(2, '0')}/${value.day.toString().padLeft(2, '0')}';
String _apiDate(DateTime value) => '${value.year.toString().padLeft(4, '0')}-${value.month.toString().padLeft(2, '0')}-${value.day.toString().padLeft(2, '0')}';
String _number(double value) => value == value.roundToDouble() ? value.toInt().toString() : value.toString();

String _message(Object error) {
  if (error is AppFailure) return error.message;
  if (error is DioException) {
    return AppFailure.fromResponse(error.response?.statusCode, error.response?.data).message;
  }
  return 'تعذر إكمال العملية. حاول مرة أخرى.';
}
