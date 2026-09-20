import 'package:flutter/material.dart';
import 'package:intl/intl.dart';

import '../../../../core/design_system/components.dart';
import '../../../../core/design_system/tokens.dart';
import '../domain/result_models.dart';
import 'results_controller.dart';

class StudentResultsScreen extends StatelessWidget {
  const StudentResultsScreen({
    super.key,
    required this.state,
    required this.historical,
    required this.onTerm,
    required this.onSubject,
    required this.onExamType,
    required this.onOpen,
    required this.onRefresh,
  });
  final ResultsReady state;
  final bool historical;
  final ValueChanged<String?> onTerm;
  final ValueChanged<String?> onSubject;
  final ValueChanged<int?> onExamType;
  final ValueChanged<StudentResult> onOpen;
  final Future<void> Function() onRefresh;

  @override
  Widget build(BuildContext context) {
    if (state.selected != null) {
      return ResultDetailScreen(
          result: state.selected!,
          historical: historical,
          onBack: () => Navigator.maybePop(context));
    }
    return RefreshIndicator(
      onRefresh: onRefresh,
      child: ListView(
        padding: const EdgeInsets.all(AppSpacing.x4),
        children: [
          Text(historical ? 'السجل الدراسي السابق' : 'النتائج',
              style: Theme.of(context).textTheme.headlineMedium),
          const SizedBox(height: AppSpacing.x3),
          Row(children: [
            Expanded(
                child: _filter(
                    value: state.term,
                    hint: 'الفصل الدراسي',
                    values: state.data.terms,
                    onChanged: onTerm)),
            const SizedBox(width: AppSpacing.x2),
            Expanded(
                child: _filter(
                    value: state.subject,
                    hint: 'المادة',
                    values: state.data.subjects,
                    onChanged: onSubject)),
          ]),
          if (state.availableExamTypes.isNotEmpty) ...[
            const SizedBox(height: AppSpacing.x3),
            SingleChildScrollView(
              scrollDirection: Axis.horizontal,
              child: Padding(
                padding: const EdgeInsets.symmetric(horizontal: AppSpacing.x1),
                child: Row(
                  children: [
                    _typeChip(context, label: 'الكل', value: null),
                    ...state.availableExamTypes.map((type) => Padding(
                          padding: const EdgeInsetsDirectional.only(
                              start: AppSpacing.x2),
                          child: _typeChip(context,
                              label: type.label, value: type.id),
                        )),
                  ],
                ),
              ),
            ),
          ],
          const SizedBox(height: AppSpacing.x3),
          if (state.visible.isEmpty)
            const AppEmptyState(message: 'لا توجد نتائج منشورة')
          else
            ...state.visible.map((item) => Padding(
                  padding: const EdgeInsets.only(bottom: AppSpacing.x3),
                  child: ResultCard(result: item, onTap: () => onOpen(item)),
                )),
          if (state.data.items.isNotEmpty) ...[
            const SizedBox(height: AppSpacing.x1),
            LastUpdatedLabel(value: state.data.lastUpdated.toLocal()),
          ],
        ],
      ),
    );
  }

  Widget _filter(
          {required String? value,
          required String hint,
          required List<String> values,
          required ValueChanged<String?> onChanged}) =>
      DropdownButtonFormField<String>(
        value: value,
        isExpanded: true,
        decoration: InputDecoration(
            labelText: hint, border: const OutlineInputBorder()),
        selectedItemBuilder: (context) => [
          const Text('الكل',
              maxLines: 1, overflow: TextOverflow.fade, softWrap: false),
          ...values.map((v) => Text(v,
              maxLines: 1, overflow: TextOverflow.fade, softWrap: false)),
        ],
        items: [
          DropdownMenuItem<String>(value: null, child: Text('$hint: الكل')),
          ...values.map((v) => DropdownMenuItem(value: v, child: Text(v))),
        ],
        onChanged: onChanged,
      );

  Widget _typeChip(BuildContext context,
          {required String label, required int? value}) =>
      ChoiceChip(
        label: ConstrainedBox(
          constraints: const BoxConstraints(maxWidth: 200),
          child: Text(label, maxLines: 1, overflow: TextOverflow.ellipsis),
        ),
        visualDensity: VisualDensity.compact,
        materialTapTargetSize: MaterialTapTargetSize.shrinkWrap,
        selected: state.examTypeId == value,
        onSelected: (_) => onExamType(value),
      );
}

class ResultCard extends StatelessWidget {
  const ResultCard({super.key, required this.result, required this.onTap});
  final StudentResult result;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) => AppCard(
        child: InkWell(
          onTap: onTap,
          borderRadius: BorderRadius.circular(AppRadius.card),
          child: Padding(
            padding: const EdgeInsets.all(AppSpacing.x1),
            child: Row(children: [
              Expanded(
                  child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                    Text(result.subject,
                        maxLines: 2,
                        overflow: TextOverflow.ellipsis,
                        style: Theme.of(context).textTheme.titleMedium),
                    const SizedBox(height: AppSpacing.x1),
                    Text(result.examTitle,
                        maxLines: 2,
                        overflow: TextOverflow.ellipsis,
                        style: Theme.of(context).textTheme.bodyMedium),
                    if (result.examTypeName.trim().isNotEmpty) ...[
                      const SizedBox(height: AppSpacing.x1),
                      Align(
                        alignment: AlignmentDirectional.centerStart,
                        child: _ExamTypeBadge(label: result.examTypeName),
                      ),
                    ],
                    const SizedBox(height: AppSpacing.x1),
                    Wrap(
                        spacing: AppSpacing.x3,
                        runSpacing: AppSpacing.x1,
                        crossAxisAlignment: WrapCrossAlignment.center,
                        children: [
                      Text(result.scoreLabel,
                          style: Theme.of(context).textTheme.titleMedium),
                      if (result.percentageLabel.isNotEmpty)
                        Text(result.percentageLabel,
                            style: Theme.of(context)
                                .textTheme
                                .titleMedium
                                ?.copyWith(color: AppColors.success)),
                    ]),
                  ])),
              const SizedBox(width: AppSpacing.x2),
              Container(
                width: 32,
                height: 32,
                decoration: BoxDecoration(
                  color: AppColors.primary.withOpacity(0.06),
                  borderRadius: BorderRadius.circular(AppRadius.chip),
                ),
                child: const Icon(Icons.assessment_outlined,
                    size: 18, color: AppColors.textSecondary),
              ),
            ]),
          ),
        ),
      );
}

class ResultDetailScreen extends StatelessWidget {
  const ResultDetailScreen(
      {super.key,
      required this.result,
      required this.historical,
      required this.onBack});
  final StudentResult result;
  final bool historical;
  final VoidCallback onBack;

  @override
  Widget build(BuildContext context) => ListView(
        padding: const EdgeInsets.all(AppSpacing.x4),
        children: [
          Row(children: [
            IconButton(onPressed: onBack, icon: const Icon(Icons.arrow_back)),
            Expanded(
                child: Text('تفاصيل النتيجة',
                    style: Theme.of(context).textTheme.headlineMedium)),
            const Chip(label: Text('للعرض فقط')),
          ]),
          const SizedBox(height: AppSpacing.x3),
          AppCard(
              child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                Text(result.subject,
                    style: Theme.of(context).textTheme.titleLarge),
                const SizedBox(height: AppSpacing.x1),
                Text(result.examTitle),
                if (result.examTypeName.trim().isNotEmpty) ...[
                  const SizedBox(height: AppSpacing.x1),
                  _ExamTypeBadge(label: result.examTypeName),
                ],
                const SizedBox(height: AppSpacing.x3),
                Wrap(
                    spacing: AppSpacing.x4,
                    runSpacing: AppSpacing.x1,
                    crossAxisAlignment: WrapCrossAlignment.center,
                    children: [
                  Text(result.scoreLabel,
                      style: Theme.of(context).textTheme.headlineMedium),
                  if (result.percentageLabel.isNotEmpty)
                    Text(result.percentageLabel,
                        style: Theme.of(context)
                            .textTheme
                            .headlineMedium
                            ?.copyWith(color: AppColors.success)),
                ]),
              ])),
          const SizedBox(height: AppSpacing.x3),
          Text('تاريخ الاختبار: ${_date(result.examDate)}'),
          if (result.publishedAt != null)
            Text('تاريخ نشر النتيجة: ${_date(result.publishedAt!)}'),
          if (result.remarks.trim().isNotEmpty) ...[
            const SizedBox(height: AppSpacing.x3),
            Text('ملاحظة المعلم:',
                style: Theme.of(context).textTheme.titleMedium),
            const SizedBox(height: AppSpacing.x1),
            Text(result.remarks),
          ],
          if (historical) ...[
            const SizedBox(height: AppSpacing.x3),
            const Chip(label: Text('السجل السابق — للعرض فقط')),
          ],
        ],
      );
}

class _ExamTypeBadge extends StatelessWidget {
  const _ExamTypeBadge({required this.label});
  final String label;

  @override
  Widget build(BuildContext context) => Container(
        constraints: const BoxConstraints(maxWidth: double.infinity),
        padding: const EdgeInsets.symmetric(
          horizontal: AppSpacing.x2,
          vertical: AppSpacing.x1,
        ),
        decoration: BoxDecoration(
          color: AppColors.primary.withOpacity(0.08),
          border: Border.all(color: AppColors.primary.withOpacity(0.18)),
          borderRadius: BorderRadius.circular(AppRadius.chip),
        ),
        child: Text(
          label,
          maxLines: 1,
          overflow: TextOverflow.ellipsis,
          style: Theme.of(context)
              .textTheme
              .labelSmall
              ?.copyWith(color: AppColors.primary),
        ),
      );
}

String _date(DateTime value) =>
    DateFormat('yyyy/MM/dd').format(value.toLocal());
