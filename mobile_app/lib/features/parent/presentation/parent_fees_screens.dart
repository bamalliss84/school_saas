import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../../core/design_system/components.dart';
import '../../../../core/design_system/role_visual_tokens.dart';
import '../../../../core/local_database/app_database.dart';
import '../domain/parent_fee_models.dart';
import 'parent_fees_controller.dart';

const _danger = Color(0xffb42318);
const _success = Color(0xff067647);
const _warning = Color(0xffb54708);

Color _stateColor(FeePaymentState state) => switch (state) {
      FeePaymentState.paid => _success,
      FeePaymentState.overdue => _danger,
      FeePaymentState.partial => _warning,
      _ => Colors.blueGrey,
    };

/// Pushed page: watches the provider for the selected child.
class ParentFeesPage extends ConsumerWidget {
  const ParentFeesPage({
    super.key,
    required this.scope,
    required this.childId,
    required this.childName,
    required this.historical,
  });

  final CacheScope scope;
  final int childId;
  final String childName;
  final bool historical;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final query = (scope: scope, childId: childId);
    return Scaffold(
      appBar: AppBar(title: const Text('الرسوم والمدفوعات')),
      body: SafeArea(
        child: ParentFeesScreen(
          state: ref.watch(parentFeesProvider(query)),
          childName: childName,
          historical: historical,
          onRefresh: ref.read(parentFeesProvider(query).notifier).refresh,
        ),
      ),
    );
  }
}

class ParentFeesScreen extends StatelessWidget {
  const ParentFeesScreen({
    super.key,
    required this.state,
    required this.childName,
    required this.historical,
    required this.onRefresh,
  });

  final ParentFeesState state;
  final String childName;
  final bool historical;
  final Future<void> Function() onRefresh;

  @override
  Widget build(BuildContext context) => switch (state) {
        ParentFeesLoading() => const Center(child: CircularProgressIndicator()),
        ParentFeesNotAllowed() => const _Message(
            icon: Icons.lock_outline,
            text: 'لا تتوفر لك صلاحية الاطلاع على رسوم هذا الابن.\n'
                'تواصل مع إدارة المدرسة إذا كنت المسؤول المالي.',
          ),
        ParentFeesFailure(:final message) => _Message(
            icon: Icons.error_outline,
            text: message,
            onRetry: onRefresh,
          ),
        ParentFeesReady(:final data, :final refreshing) => RefreshIndicator(
            onRefresh: onRefresh,
            child: ListView(
              physics: const AlwaysScrollableScrollPhysics(),
              padding: const EdgeInsets.all(16),
              children: [
                if (refreshing) const LinearProgressIndicator(),
                if (data.offline) ...[
                  const OfflineCacheBanner(),
                  const SizedBox(height: 12),
                ],
                if (historical) ...[
                  const HistoricalContextBanner(),
                  const SizedBox(height: 12),
                ],
                Text(childName,
                    style: Theme.of(context)
                        .textTheme
                        .titleLarge
                        ?.copyWith(fontWeight: FontWeight.w800)),
                LastUpdatedLabel(value: data.lastUpdated.toLocal()),
                const SizedBox(height: 12),
                if (data.summary.feeCount == 0)
                  const _Message(
                    icon: Icons.receipt_long_outlined,
                    text: 'لا توجد رسوم مسجلة لهذا الابن.',
                  )
                else ...[
                  _SummaryCard(summary: data.summary),
                  const SizedBox(height: 20),
                  const _SectionTitle('الأقساط والمستحقات'),
                  for (final fee in data.fees) _FeeTile(fee: fee),
                  const SizedBox(height: 20),
                  const _SectionTitle('الدفعات والإيصالات'),
                  if (data.payments.isEmpty)
                    const Padding(
                      padding: EdgeInsets.all(12),
                      child: Text('لا توجد دفعات مسجلة بعد.'),
                    )
                  else
                    for (final payment in data.payments)
                      _PaymentTile(payment: payment),
                  const SizedBox(height: 16),
                  Text(
                    'الدفع يتم لدى إدارة المدرسة، ويظهر هنا بعد تسجيله مع رقم الإيصال.',
                    textAlign: TextAlign.center,
                    style: Theme.of(context).textTheme.bodySmall,
                  ),
                ],
              ],
            ),
          ),
      };
}

class _SummaryCard extends StatelessWidget {
  const _SummaryCard({required this.summary});
  final FeeSummary summary;

  @override
  Widget build(BuildContext context) {
    final currency = summary.currency;
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Text('المتبقي', style: Theme.of(context).textTheme.bodyMedium),
            Text(
              formatMoney(summary.remaining, currency),
              key: const Key('parent-fees-remaining'),
              style: Theme.of(context).textTheme.headlineSmall?.copyWith(
                    fontWeight: FontWeight.w800,
                    color: summary.overdue > 0 ? _danger : null,
                  ),
            ),
            const SizedBox(height: 10),
            ClipRRect(
              borderRadius: BorderRadius.circular(8),
              child: LinearProgressIndicator(
                value: summary.progress,
                minHeight: 8,
                color: _success,
                backgroundColor: _success.withOpacity(.12),
                semanticsLabel: 'نسبة السداد',
              ),
            ),
            const SizedBox(height: 12),
            Row(
              children: [
                Expanded(
                    child: _Stat('الإجمالي', formatMoney(summary.total, currency))),
                Expanded(
                    child: _Stat('المدفوع', formatMoney(summary.paid, currency))),
                Expanded(
                  child: _Stat(
                    'المتأخر',
                    formatMoney(summary.overdue, currency),
                    color: summary.overdue > 0 ? _danger : null,
                  ),
                ),
              ],
            ),
            if (summary.nextDueDate != null) ...[
              const Divider(height: 24),
              Row(
                children: [
                  const Icon(Icons.event_outlined, size: 20),
                  const SizedBox(width: 8),
                  Expanded(
                    child: Text(
                      'القسط القادم: ${summary.nextDueTitle ?? ''} — '
                      '${formatMoney(summary.nextDueBalance ?? 0, currency)} '
                      'بتاريخ ${summary.nextDueDate}',
                    ),
                  ),
                ],
              ),
            ],
          ],
        ),
      ),
    );
  }
}

class _Stat extends StatelessWidget {
  const _Stat(this.label, this.value, {this.color});
  final String label;
  final String value;
  final Color? color;

  @override
  Widget build(BuildContext context) => Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(label, style: Theme.of(context).textTheme.bodySmall),
          Text(value,
              style: TextStyle(fontWeight: FontWeight.w700, color: color)),
        ],
      );
}

class _SectionTitle extends StatelessWidget {
  const _SectionTitle(this.text);
  final String text;

  @override
  Widget build(BuildContext context) => Padding(
        padding: const EdgeInsets.only(bottom: 8),
        child: Text(text,
            style: Theme.of(context)
                .textTheme
                .titleMedium
                ?.copyWith(fontWeight: FontWeight.w700)),
      );
}

class _FeeTile extends StatelessWidget {
  const _FeeTile({required this.fee});
  final ParentFee fee;

  @override
  Widget build(BuildContext context) {
    final color = _stateColor(fee.state);
    final installment = fee.installmentCount > 1
        ? ' (قسط ${fee.installmentNumber}/${fee.installmentCount})'
        : '';
    return Card(
      child: ListTile(
        title: Text('${fee.title}$installment'),
        subtitle: Text(
          '${fee.categoryName} • الاستحقاق ${fee.dueDate}\n'
          'المدفوع ${formatMoney(fee.paidAmount, fee.currency)} من ${formatMoney(fee.netAmount, fee.currency)}',
        ),
        isThreeLine: true,
        trailing: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          crossAxisAlignment: CrossAxisAlignment.end,
          children: [
            Text(formatMoney(fee.balance, fee.currency),
                style: const TextStyle(fontWeight: FontWeight.w800)),
            const SizedBox(height: 4),
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
              decoration: BoxDecoration(
                color: color.withOpacity(.1),
                borderRadius: BorderRadius.circular(10),
              ),
              child: Text(feeStateLabel(fee.state),
                  style: TextStyle(color: color, fontSize: 12)),
            ),
          ],
        ),
      ),
    );
  }
}

class _PaymentTile extends StatelessWidget {
  const _PaymentTile({required this.payment});
  final ParentFeePayment payment;

  @override
  Widget build(BuildContext context) => Card(
        child: ListTile(
          leading: const Icon(Icons.receipt_long_outlined, color: _success),
          title: Text(formatMoney(payment.amount, payment.currency),
              style: const TextStyle(fontWeight: FontWeight.w700)),
          subtitle: Text(
            '${payment.feeTitle}\n${paymentMethodLabel(payment.method)} • ${payment.paidOn}',
          ),
          isThreeLine: true,
          trailing: Text('إيصال\n${payment.receiptNumber}',
              textAlign: TextAlign.center,
              style: Theme.of(context).textTheme.bodySmall),
        ),
      );
}

class _Message extends StatelessWidget {
  const _Message({required this.icon, required this.text, this.onRetry});
  final IconData icon;
  final String text;
  final Future<void> Function()? onRetry;

  @override
  Widget build(BuildContext context) => Padding(
        padding: const EdgeInsets.all(24),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(icon, size: 48, color: Colors.grey),
            const SizedBox(height: 12),
            Text(text, textAlign: TextAlign.center),
            if (onRetry != null)
              TextButton(
                  onPressed: onRetry, child: const Text('إعادة المحاولة')),
          ],
        ),
      );
}

/// Home-screen alert: shows dues for the selected child, hidden when nothing is owed
/// or the guardian has no financial access.
class ParentFeeAlertCard extends StatelessWidget {
  const ParentFeeAlertCard({super.key, required this.state, required this.onOpen});
  final ParentFeesState state;
  final VoidCallback onOpen;

  @override
  Widget build(BuildContext context) {
    final current = state;
    if (current is! ParentFeesReady || !current.data.summary.hasDues) {
      return const SizedBox.shrink();
    }
    final summary = current.data.summary;
    final overdue = summary.overdue > 0;
    final color = overdue ? _danger : RoleVisualTokens.parent;
    final message = overdue
        ? 'يوجد ${summary.overdueCount} قسط متأخر بمبلغ ${formatMoney(summary.overdue, summary.currency)}'
        : summary.nextDueDate != null
            ? 'القسط القادم ${formatMoney(summary.nextDueBalance ?? 0, summary.currency)} بتاريخ ${summary.nextDueDate}'
            : 'المتبقي ${formatMoney(summary.remaining, summary.currency)}';
    return Card(
      key: const Key('parent-fee-alert'),
      color: color.withOpacity(.07),
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(16),
        side: BorderSide(color: color.withOpacity(.35)),
      ),
      child: ListTile(
        onTap: onOpen,
        leading: Icon(
          overdue ? Icons.warning_amber_rounded : Icons.account_balance_wallet_outlined,
          color: color,
        ),
        title: Text(overdue ? 'رسوم متأخرة' : 'الرسوم المدرسية',
            style: TextStyle(fontWeight: FontWeight.w800, color: color)),
        subtitle: Text(message),
        trailing: const Icon(Icons.chevron_left),
      ),
    );
  }
}
