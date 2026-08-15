import 'package:flutter/material.dart';

import '../../../../core/design_system/components.dart';
import '../../../../core/design_system/tokens.dart';
import '../data/homework_repository.dart';
import '../domain/homework_models.dart';
import 'homework_controller.dart';

const homeworkFilters = <String?, String>{
  null: 'الكل',
  'not_started': 'لم يبدأ',
  'draft': 'قيد العمل',
  'submitted': 'تم التسليم',
  'returned': 'أعيد للمراجعة',
  'graded': 'تم التصحيح',
  'overdue': 'متأخر',
  'closed_without_submission': 'مغلق',
};

class StudentHomeworkListScreen extends StatelessWidget {
  const StudentHomeworkListScreen({
    super.key,
    required this.state,
    required this.onFilter,
    required this.onOpen,
    required this.onRefresh,
  });

  final HomeworkReady state;
  final ValueChanged<String?> onFilter;
  final ValueChanged<int> onOpen;
  final Future<void> Function() onRefresh;

  @override
  Widget build(BuildContext context) => RefreshIndicator(
        onRefresh: onRefresh,
        child: ListView(
          padding: const EdgeInsets.all(AppSpacing.x4),
          children: [
            Text('الواجبات', style: Theme.of(context).textTheme.headlineMedium),
            const SizedBox(height: AppSpacing.x3),
            SizedBox(
              height: 42,
              child: ListView.separated(
                scrollDirection: Axis.horizontal,
                itemCount: homeworkFilters.length,
                separatorBuilder: (_, __) =>
                    const SizedBox(width: AppSpacing.x2),
                itemBuilder: (_, index) {
                  final entry = homeworkFilters.entries.elementAt(index);
                  return ChoiceChip(
                    label: Text(entry.value),
                    selected: state.filter == entry.key,
                    onSelected: (_) => onFilter(entry.key),
                  );
                },
              ),
            ),
            const SizedBox(height: AppSpacing.x4),
            if (state.visible.isEmpty)
              const AppEmptyState(message: 'لا توجد واجبات في هذه الحالة')
            else
              ...state.visible.map((item) => Padding(
                    padding: const EdgeInsets.only(bottom: AppSpacing.x3),
                    child: HomeworkCard(
                        homework: item, onTap: () => onOpen(item.id)),
                  )),
          ],
        ),
      );
}

class HomeworkCard extends StatelessWidget {
  const HomeworkCard({super.key, required this.homework, required this.onTap});
  final StudentHomework homework;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) => AppCard(
        child: InkWell(
          onTap: onTap,
          borderRadius: BorderRadius.circular(AppRadius.card),
          child: Padding(
            padding: const EdgeInsets.all(AppSpacing.x1),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(children: [
                  Expanded(
                    child: Text(homework.title,
                        maxLines: 2,
                        overflow: TextOverflow.ellipsis,
                        style: Theme.of(context).textTheme.titleMedium),
                  ),
                  const SizedBox(width: AppSpacing.x2),
                  HomeworkStatusChip(status: homework.completionStatus),
                ]),
                const SizedBox(height: AppSpacing.x2),
                Text(
                  '${homework.subject} • ${homework.teacher}',
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                  style: Theme.of(context).textTheme.bodySmall,
                ),
                const SizedBox(height: AppSpacing.x1),
                Text('موعد التسليم: ${_date(homework.dueDate)}',
                    style: Theme.of(context).textTheme.bodySmall),
              ],
            ),
          ),
        ),
      );
}

class HomeworkStatusChip extends StatelessWidget {
  const HomeworkStatusChip({super.key, required this.status});
  final String status;

  @override
  Widget build(BuildContext context) {
    final color = switch (status) {
      'graded' => AppColors.success,
      'returned' => AppColors.warning,
      'overdue' || 'closed_without_submission' => AppColors.error,
      'submitted' => AppColors.info,
      _ => AppColors.textSecondary,
    };
    return Container(
      padding: const EdgeInsets.symmetric(
          horizontal: AppSpacing.x2, vertical: AppSpacing.x1),
      decoration: BoxDecoration(
        color: color.withOpacity(.1),
        borderRadius: BorderRadius.circular(AppRadius.chip),
      ),
      child: Text(homeworkFilters[status] ?? status,
          style: Theme.of(context).textTheme.bodySmall?.copyWith(color: color)),
    );
  }
}

class StudentHomeworkDetailScreen extends StatefulWidget {
  const StudentHomeworkDetailScreen({
    super.key,
    required this.data,
    required this.historical,
    required this.submitting,
    required this.onBack,
    required this.onSave,
    required this.onSubmit,
    required this.onDownload,
  });

  final HomeworkDetailData data;
  final bool historical;
  final bool submitting;
  final VoidCallback onBack;
  final Future<void> Function(HomeworkLocalDraft) onSave;
  final Future<bool> Function() onSubmit;
  final Future<String> Function(HomeworkAttachment) onDownload;

  @override
  State<StudentHomeworkDetailScreen> createState() =>
      _StudentHomeworkDetailScreenState();
}

class _StudentHomeworkDetailScreenState
    extends State<StudentHomeworkDetailScreen> {
  late final TextEditingController answer;
  late final TextEditingController note;

  @override
  void initState() {
    super.initState();
    answer = TextEditingController(text: widget.data.draft.answer);
    note = TextEditingController(text: widget.data.draft.studentNote);
  }

  @override
  void dispose() {
    answer.dispose();
    note.dispose();
    super.dispose();
  }

  HomeworkLocalDraft get draft => HomeworkLocalDraft(
        answer: answer.text,
        studentNote: note.text,
        localFiles: widget.data.draft.localFiles,
      );

  @override
  Widget build(BuildContext context) {
    final item = widget.data.homework;
    final editable = !widget.historical && item.canEditDraft;
    return ListView(
      padding: const EdgeInsets.all(AppSpacing.x4),
      children: [
        Row(children: [
          IconButton(
              onPressed: widget.onBack, icon: const Icon(Icons.arrow_back)),
          Expanded(
            child: Text('تفاصيل الواجب',
                style: Theme.of(context).textTheme.headlineMedium),
          ),
          HomeworkStatusChip(status: item.completionStatus),
        ]),
        const SizedBox(height: AppSpacing.x3),
        AppCard(
          child:
              Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            Text(item.title, style: Theme.of(context).textTheme.titleLarge),
            const SizedBox(height: AppSpacing.x2),
            Text('${item.subject} • ${item.teacher}'),
            Text('الصف ${item.classroomId} • الشعبة ${item.sectionId}',
                style: Theme.of(context).textTheme.bodySmall),
            const Divider(height: AppSpacing.x6),
            Text(item.description.isEmpty ? 'لا يوجد وصف' : item.description),
            const SizedBox(height: AppSpacing.x3),
            Text('موعد التسليم: ${_date(item.dueDate)}'),
            if (item.maxGrade != null) Text('الدرجة القصوى: ${item.maxGrade}'),
          ]),
        ),
        if (item.attachments.isNotEmpty) ...[
          const SizedBox(height: AppSpacing.x4),
          Text('المرفقات', style: Theme.of(context).textTheme.titleLarge),
          const SizedBox(height: AppSpacing.x2),
          ...item.attachments.map((attachment) => AppCard(
                child: ListTile(
                  contentPadding: EdgeInsets.zero,
                  leading: const Icon(Icons.attach_file),
                  title: Text(attachment.name),
                  subtitle: Text(attachment.contentType),
                  trailing: IconButton(
                    tooltip: 'تنزيل',
                    icon: const Icon(Icons.download_outlined),
                    onPressed: widget.data.offline
                        ? null
                        : () async {
                            final messenger = ScaffoldMessenger.of(context);
                            final path = await widget.onDownload(attachment);
                            if (mounted) {
                              messenger.showSnackBar(
                                  SnackBar(content: Text('تم التنزيل: $path')));
                            }
                          },
                  ),
                ),
              )),
        ],
        if (item.completionStatus == 'returned' ||
            item.completionStatus == 'graded') ...[
          const SizedBox(height: AppSpacing.x4),
          AppCard(
            child:
                Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
              Text(
                  item.completionStatus == 'returned'
                      ? 'أعيد للمراجعة'
                      : 'تم التصحيح',
                  style: Theme.of(context).textTheme.titleLarge),
              if (item.grade != null)
                Text('الدرجة: ${item.grade} / ${item.maxGrade ?? '-'}'),
              if (item.teacherNote.isNotEmpty) Text(item.teacherNote),
            ]),
          ),
        ],
        if (editable) ...[
          const SizedBox(height: AppSpacing.x4),
          Text('إجابتي', style: Theme.of(context).textTheme.titleLarge),
          const SizedBox(height: AppSpacing.x2),
          TextField(
            controller: answer,
            minLines: 5,
            maxLines: 10,
            decoration: const InputDecoration(hintText: 'اكتب إجابتك...'),
          ),
          const SizedBox(height: AppSpacing.x3),
          TextField(
            controller: note,
            minLines: 2,
            maxLines: 4,
            decoration: const InputDecoration(
                labelText: 'ملاحظة شخصية',
                helperText: 'تحفظ على هذا الجهاز ولا ترسل للمعلم'),
          ),
          const SizedBox(height: AppSpacing.x3),
          AppSecondaryButton(
              label: 'حفظ كمسودة', onPressed: () => widget.onSave(draft)),
          const SizedBox(height: AppSpacing.x2),
          AppPrimaryButton(
            label: item.completionStatus == 'returned'
                ? 'إعادة الإرسال'
                : 'إرسال الواجب',
            onPressed: widget.submitting
                ? null
                : () async {
                    final messenger = ScaffoldMessenger.of(context);
                    await widget.onSave(draft);
                    if (widget.data.offline) {
                      if (mounted) {
                        messenger.showSnackBar(const SnackBar(
                            content:
                                Text('يتطلب إرسال الواجب اتصالاً بالإنترنت')));
                      }
                      return;
                    }
                    final success = await widget.onSubmit();
                    if (mounted) {
                      messenger.showSnackBar(SnackBar(
                          content: Text(success
                              ? 'تم إرسال الواجب بنجاح'
                              : 'تعذر إرسال الواجب. المسودة محفوظة')));
                    }
                  },
          ),
        ],
        if (widget.historical)
          const Padding(
            padding: EdgeInsets.only(top: AppSpacing.x4),
            child: Text('السجل الدراسي السابق — للعرض فقط',
                textAlign: TextAlign.center),
          ),
      ],
    );
  }
}

String _date(DateTime value) =>
    '${value.day}/${value.month}/${value.year} ${value.hour.toString().padLeft(2, '0')}:${value.minute.toString().padLeft(2, '0')}';
