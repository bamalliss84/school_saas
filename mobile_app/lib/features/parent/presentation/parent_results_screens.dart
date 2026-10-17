import 'package:flutter/material.dart';
import 'package:intl/intl.dart';

import '../../../../core/design_system/components.dart';
import '../domain/parent_result_models.dart';
import 'parent_results_controller.dart';

class ParentResultsScreen extends StatelessWidget {
  const ParentResultsScreen({super.key, required this.state, required this.childName,
      required this.historical, required this.onRefresh, required this.onOpen});
  final ParentResultsState state;
  final String childName;
  final bool historical;
  final Future<void> Function() onRefresh;
  final ValueChanged<ParentResult> onOpen;

  @override
  Widget build(BuildContext context) {
    if (state is ParentResultsLoading) {
      return const Center(child: CircularProgressIndicator());
    }
    if (state case ParentResultsFailure(:final message)) {
      return Center(child: Column(mainAxisSize: MainAxisSize.min, children: [
        Text(message, textAlign: TextAlign.center),
        const SizedBox(height: 12),
        FilledButton(onPressed: onRefresh, child: const Text('إعادة المحاولة')),
      ]));
    }
    final ready = state as ParentResultsReady;
    return RefreshIndicator(
      onRefresh: onRefresh,
      child: ListView(padding: const EdgeInsets.all(16), children: [
        Row(children: [
          Expanded(child: Text('نتائج $childName',
              style: Theme.of(context).textTheme.headlineSmall)),
          if (historical) const Chip(label: Text('سياق تاريخي — للقراءة فقط')),
        ]),
        if (ready.data.offline) const OfflineCacheBanner(),
        if (ready.refreshing) const LinearProgressIndicator(),
        const SizedBox(height: 12),
        if (ready.data.items.isEmpty)
          const Padding(
            padding: EdgeInsets.symmetric(vertical: 40),
            child: Column(children: [
              Icon(Icons.assessment_outlined, size: 48),
              SizedBox(height: 12),
              Text('لا توجد نتائج منشورة'),
            ]),
          )
        else
          for (final item in ready.data.items)
            Card(child: ListTile(
              leading: const Icon(Icons.assessment_outlined),
              title: Text(item.subject),
              subtitle: Text([
                item.examTitle,
                if (item.examTypeName.isNotEmpty) item.examTypeName,
                if (item.termName.isNotEmpty) item.termName,
                _date(item.examDate),
              ].join(' • ')),
              trailing: Text(item.scoreLabel),
              onTap: () => onOpen(item),
            )),
      ]),
    );
  }
}

class ParentResultDetailScreen extends StatelessWidget {
  const ParentResultDetailScreen({super.key, required this.result, required this.historical});
  final ParentResult result;
  final bool historical;

  @override
  Widget build(BuildContext context) => Scaffold(
    appBar: AppBar(title: const Text('تفاصيل النتيجة')),
    body: ListView(padding: const EdgeInsets.all(16), children: [
      Row(children: [
        Expanded(child: Text(result.subject,
            style: Theme.of(context).textTheme.headlineSmall)),
        const Chip(label: Text('للعرض فقط')),
      ]),
      const SizedBox(height: 12),
      Card(child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Text(result.examTitle, style: Theme.of(context).textTheme.titleLarge),
          if (result.examTypeName.isNotEmpty) Text(result.examTypeName),
          const SizedBox(height: 16),
          Text(result.scoreLabel, style: Theme.of(context).textTheme.headlineMedium),
          if (result.percentageLabel.isNotEmpty) Text(result.percentageLabel),
        ]),
      )),
      Text('تاريخ الاختبار: ${_date(result.examDate)}'),
      if (result.termName.isNotEmpty) Text('الفصل: ${result.termName}'),
      if (result.publishedAt != null) Text('تاريخ النشر: ${_date(result.publishedAt!)}'),
      if (result.remarks.trim().isNotEmpty) ...[
        const SizedBox(height: 16),
        Text('ملاحظة المعلم:', style: Theme.of(context).textTheme.titleMedium),
        Text(result.remarks),
      ],
      if (historical) ...[
        const SizedBox(height: 16),
        const Chip(label: Text('السجل السابق — للعرض فقط')),
      ],
    ]),
  );
}

String _date(DateTime value) => DateFormat('yyyy/MM/dd').format(value.toLocal());
