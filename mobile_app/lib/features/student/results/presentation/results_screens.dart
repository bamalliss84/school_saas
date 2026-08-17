import 'package:flutter/material.dart';
import 'package:intl/intl.dart';

import '../../../../core/design_system/components.dart';
import '../../../../core/design_system/tokens.dart';
import '../domain/result_models.dart';
import 'results_controller.dart';

class StudentResultsScreen extends StatelessWidget {
  const StudentResultsScreen({
    super.key, required this.state, required this.historical,
    required this.onTerm, required this.onSubject, required this.onOpen,
    required this.onRefresh,
  });
  final ResultsReady state;
  final bool historical;
  final ValueChanged<String?> onTerm;
  final ValueChanged<String?> onSubject;
  final ValueChanged<StudentResult> onOpen;
  final Future<void> Function() onRefresh;

  @override
  Widget build(BuildContext context) {
    if (state.selected != null) {
      return ResultDetailScreen(result: state.selected!, historical: historical,
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
          if (state.data.offline) ...[
            const OfflineCacheBanner(),
            const SizedBox(height: AppSpacing.x2),
          ],
          Row(children: [
            Expanded(child: _filter(
              value: state.term, hint: 'الفصل الدراسي',
              values: state.data.terms, onChanged: onTerm)),
            const SizedBox(width: AppSpacing.x2),
            Expanded(child: _filter(
              value: state.subject, hint: 'المادة',
              values: state.data.subjects, onChanged: onSubject)),
          ]),
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

  Widget _filter({required String? value, required String hint,
      required List<String> values, required ValueChanged<String?> onChanged}) =>
      DropdownButtonFormField<String>(
        value: value,
        isExpanded: true,
        decoration: InputDecoration(labelText: hint, border: const OutlineInputBorder()),
        items: [
          DropdownMenuItem<String>(value: null, child: Text('$hint: الكل')),
          ...values.map((v) => DropdownMenuItem(value: v, child: Text(v,
              overflow: TextOverflow.ellipsis))),
        ],
        onChanged: onChanged,
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
          Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            Text(result.subject, style: Theme.of(context).textTheme.titleMedium),
            const SizedBox(height: AppSpacing.x1),
            Text(result.examTitle, style: Theme.of(context).textTheme.bodyMedium),
            const SizedBox(height: AppSpacing.x1),
            Row(children: [
              Text(result.scoreLabel, style: Theme.of(context).textTheme.titleMedium),
              if (result.percentageLabel.isNotEmpty) ...[
                const SizedBox(width: AppSpacing.x3),
                Text(result.percentageLabel,
                    style: Theme.of(context).textTheme.titleMedium?.copyWith(
                        color: AppColors.success)),
              ],
            ]),
          ])),
          const Icon(Icons.assessment_outlined),
        ]),
      ),
    ),
  );
}

class ResultDetailScreen extends StatelessWidget {
  const ResultDetailScreen({super.key, required this.result,
      required this.historical, required this.onBack});
  final StudentResult result;
  final bool historical;
  final VoidCallback onBack;

  @override
  Widget build(BuildContext context) => ListView(
    padding: const EdgeInsets.all(AppSpacing.x4),
    children: [
      Row(children: [
        IconButton(onPressed: onBack, icon: const Icon(Icons.arrow_back)),
        Expanded(child: Text('تفاصيل النتيجة',
            style: Theme.of(context).textTheme.headlineMedium)),
        const Chip(label: Text('للعرض فقط')),
      ]),
      const SizedBox(height: AppSpacing.x3),
      AppCard(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        Text(result.subject, style: Theme.of(context).textTheme.titleLarge),
        const SizedBox(height: AppSpacing.x1),
        Text(result.examTitle),
        const SizedBox(height: AppSpacing.x3),
        Row(children: [
          Text(result.scoreLabel, style: Theme.of(context).textTheme.headlineMedium),
          if (result.percentageLabel.isNotEmpty) ...[
            const SizedBox(width: AppSpacing.x4),
            Text(result.percentageLabel,
                style: Theme.of(context).textTheme.headlineMedium?.copyWith(
                    color: AppColors.success)),
          ],
        ]),
      ])),
      const SizedBox(height: AppSpacing.x3),
      Text('تاريخ الاختبار: ${_date(result.examDate)}'),
      if (result.publishedAt != null)
        Text('تاريخ نشر النتيجة: ${_date(result.publishedAt!)}'),
      if (result.remarks.trim().isNotEmpty) ...[
        const SizedBox(height: AppSpacing.x3),
        Text('ملاحظة المعلم:', style: Theme.of(context).textTheme.titleMedium),
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

String _date(DateTime value) => DateFormat('yyyy/MM/dd').format(value.toLocal());
