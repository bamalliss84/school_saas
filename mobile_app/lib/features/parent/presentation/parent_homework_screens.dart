import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../../core/design_system/components.dart';
import '../../../../core/local_database/app_database.dart';
import '../data/parent_homework_repository.dart';
import '../domain/parent_homework_models.dart';
import 'parent_homework_controller.dart';

class ParentHomeworkListScreen extends StatefulWidget {
  const ParentHomeworkListScreen({
    super.key,
    required this.state,
    required this.childName,
    required this.historical,
    required this.onRefresh,
    required this.onOpen,
  });
  final ParentHomeworkState state;
  final String childName;
  final bool historical;
  final Future<void> Function() onRefresh;
  final ValueChanged<ParentHomework> onOpen;

  @override
  State<ParentHomeworkListScreen> createState() =>
      _ParentHomeworkListScreenState();
}

class _ParentHomeworkListScreenState extends State<ParentHomeworkListScreen> {
  String filter = 'all';

  @override
  Widget build(BuildContext context) {
    final state = widget.state;
    if (state is ParentHomeworkLoading) return const _HomeworkLoading();
    if (state is ParentHomeworkFailure) {
      return _HomeworkFailure(
          message: state.message, onRetry: widget.onRefresh);
    }
    final ready = state as ParentHomeworkReady;
    final items = ready.data.items.where(_matchesFilter).toList();
    return RefreshIndicator(
      onRefresh: widget.onRefresh,
      child: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          _HomeworkHeader(
            title: 'واجبات ${widget.childName}',
            historical: widget.historical,
          ),
          if (ready.data.offline) const OfflineCacheBanner(),
          if (ready.refreshing) const LinearProgressIndicator(),
          SingleChildScrollView(
            scrollDirection: Axis.horizontal,
            child: Row(
              children: [
                for (final option in const [
                  ('all', 'الكل'),
                  ('pending', 'قيد المتابعة'),
                  ('submitted', 'تم التسليم'),
                  ('reviewed', 'تمت المراجعة'),
                  ('graded', 'تم التقييم'),
                  ('overdue', 'متأخر'),
                ])
                  Padding(
                    padding: const EdgeInsetsDirectional.only(end: 8),
                    child: ChoiceChip(
                      label: Text(option.$2),
                      selected: filter == option.$1,
                      onSelected: (_) => setState(() => filter = option.$1),
                    ),
                  ),
              ],
            ),
          ),
          const SizedBox(height: 12),
          if (items.isEmpty)
            const _HomeworkEmpty(text: 'لا توجد واجبات')
          else
            for (final item in items)
              Card(
                child: ListTile(
                  onTap: () => widget.onOpen(item),
                  leading: const Icon(Icons.assignment_outlined),
                  title: Text(item.title),
                  subtitle: Text([
                    if (item.subject.isNotEmpty) item.subject,
                    'موعد التسليم ${_dateTime(item.dueDate)}',
                  ].join(' • ')),
                  trailing: _HomeworkStatusChip(item.completionStatus),
                ),
              ),
        ],
      ),
    );
  }

  bool _matchesFilter(ParentHomework item) => switch (filter) {
        'pending' => const {
            ParentHomeworkStatus.notStarted,
            ParentHomeworkStatus.draft,
            ParentHomeworkStatus.returned,
          }.contains(item.completionStatus),
        'submitted' => item.completionStatus == ParentHomeworkStatus.submitted,
        'reviewed' => item.completionStatus == ParentHomeworkStatus.reviewed,
        'graded' => item.completionStatus == ParentHomeworkStatus.graded,
        'overdue' => item.completionStatus == ParentHomeworkStatus.overdue,
        _ => true,
      };
}

class ParentHomeworkDetailPage extends ConsumerWidget {
  const ParentHomeworkDetailPage({
    super.key,
    required this.scope,
    required this.childId,
    required this.childName,
    required this.homework,
    required this.historical,
  });
  final CacheScope scope;
  final int childId;
  final String childName;
  final ParentHomework homework;
  final bool historical;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final query = (scope: scope, childId: childId, homework: homework);
    return Scaffold(
      appBar: AppBar(title: const Text('تفاصيل الواجب')),
      body: SafeArea(
        child: ParentHomeworkDetailScreen(
          state: ref.watch(parentHomeworkDetailProvider(query)),
          childName: childName,
          historical: historical,
          onRefresh:
              ref.read(parentHomeworkDetailProvider(query).notifier).refresh,
        ),
      ),
    );
  }
}

class ParentHomeworkDetailScreen extends StatelessWidget {
  const ParentHomeworkDetailScreen({
    super.key,
    required this.state,
    required this.childName,
    required this.historical,
    required this.onRefresh,
  });
  final ParentHomeworkDetailState state;
  final String childName;
  final bool historical;
  final Future<void> Function() onRefresh;

  @override
  Widget build(BuildContext context) {
    if (state is ParentHomeworkDetailLoading) return const _HomeworkLoading();
    if (state case ParentHomeworkDetailFailure(:final message)) {
      return _HomeworkFailure(message: message, onRetry: onRefresh);
    }
    final ready = state as ParentHomeworkDetailReady;
    final data = ready.data;
    final item = data.homework;
    final submission = data.submission;
    return RefreshIndicator(
      onRefresh: onRefresh,
      child: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          _HomeworkHeader(title: childName, historical: historical),
          if (data.offline) const OfflineCacheBanner(),
          if (ready.refreshing) const LinearProgressIndicator(),
          Card(
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(children: [
                    Expanded(
                      child: Text(item.title,
                          style: Theme.of(context).textTheme.titleLarge),
                    ),
                    _HomeworkStatusChip(item.completionStatus),
                  ]),
                  const SizedBox(height: 12),
                  if (item.description.isNotEmpty) Text(item.description),
                  const SizedBox(height: 12),
                  Text([item.subject, item.teacher]
                      .where((value) => value.isNotEmpty)
                      .join(' • ')),
                  Text('موعد التسليم: ${_dateTime(item.dueDate)}'),
                  if (item.publishedAt != null)
                    Text('تاريخ النشر: ${_dateTime(item.publishedAt!)}'),
                ],
              ),
            ),
          ),
          if (item.attachments.isNotEmpty) ...[
            const _SectionTitle('مرفقات الواجب'),
            for (final attachment in item.attachments)
              Card(
                child: ListTile(
                  leading: const Icon(Icons.attach_file),
                  title: Text(attachment.name),
                ),
              ),
          ],
          const _SectionTitle('تسليم الطالب'),
          if (submission == null)
            const Card(child: ListTile(title: Text('لا يوجد تسليم بعد')))
          else
            Card(
              child: Padding(
                padding: const EdgeInsets.all(16),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(ParentHomeworkStatus.fromApi(submission.status)
                        .arabicLabel),
                    if (submission.answer.isNotEmpty) ...[
                      const SizedBox(height: 8),
                      Text(submission.answer),
                    ],
                    if (submission.submittedAt != null)
                      Text(
                          'وقت التسليم: ${_dateTime(submission.submittedAt!)}'),
                    if (submission.isLate) const Text('تم التسليم متأخرًا'),
                    if (submission.grade != null)
                      Text(
                          'الدرجة: ${_number(submission.grade!)}${item.maxGrade == null ? '' : ' / ${_number(item.maxGrade!)}'}'),
                    if (submission.teacherNote.isNotEmpty)
                      Text('ملاحظة المعلم: ${submission.teacherNote}'),
                    if (submission.attachments.isNotEmpty) ...[
                      const SizedBox(height: 8),
                      for (final attachment in submission.attachments)
                        Text('• ${attachment.name}'),
                    ],
                  ],
                ),
              ),
            ),
        ],
      ),
    );
  }
}

class _HomeworkHeader extends StatelessWidget {
  const _HomeworkHeader({required this.title, required this.historical});
  final String title;
  final bool historical;
  @override
  Widget build(BuildContext context) => Padding(
        padding: const EdgeInsets.only(bottom: 12),
        child: Row(children: [
          Expanded(
              child: Text(title,
                  style: Theme.of(context).textTheme.headlineSmall)),
          if (historical) const Chip(label: Text('سياق تاريخي — للقراءة فقط')),
        ]),
      );
}

class _HomeworkStatusChip extends StatelessWidget {
  const _HomeworkStatusChip(this.status);
  final ParentHomeworkStatus status;
  @override
  Widget build(BuildContext context) => Chip(label: Text(status.arabicLabel));
}

class _SectionTitle extends StatelessWidget {
  const _SectionTitle(this.text);
  final String text;
  @override
  Widget build(BuildContext context) => Padding(
        padding: const EdgeInsets.only(top: 16, bottom: 8),
        child: Text(text, style: Theme.of(context).textTheme.titleMedium),
      );
}

class _HomeworkLoading extends StatelessWidget {
  const _HomeworkLoading();
  @override
  Widget build(BuildContext context) =>
      const Center(child: CircularProgressIndicator());
}

class _HomeworkFailure extends StatelessWidget {
  const _HomeworkFailure({required this.message, required this.onRetry});
  final String message;
  final Future<void> Function() onRetry;
  @override
  Widget build(BuildContext context) => Center(
        child: Column(mainAxisSize: MainAxisSize.min, children: [
          Text(message, textAlign: TextAlign.center),
          const SizedBox(height: 12),
          FilledButton(onPressed: onRetry, child: const Text('إعادة المحاولة')),
        ]),
      );
}

class _HomeworkEmpty extends StatelessWidget {
  const _HomeworkEmpty({required this.text});
  final String text;
  @override
  Widget build(BuildContext context) => Padding(
        padding: const EdgeInsets.symmetric(vertical: 40),
        child: Column(children: [
          const Icon(Icons.assignment_outlined, size: 48),
          const SizedBox(height: 12),
          Text(text),
        ]),
      );
}

String _dateTime(DateTime value) =>
    '${value.year}/${value.month.toString().padLeft(2, '0')}/${value.day.toString().padLeft(2, '0')} '
    '${value.hour.toString().padLeft(2, '0')}:${value.minute.toString().padLeft(2, '0')}';

String _number(double value) =>
    value % 1 == 0 ? value.toStringAsFixed(0) : value.toString();
