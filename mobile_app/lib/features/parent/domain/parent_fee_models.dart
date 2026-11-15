/// Release 1.1 — read-only school fees for a guardian with financial access.
library;

double _money(Object? value) => double.tryParse('${value ?? 0}') ?? 0;

enum FeePaymentState { unpaid, partial, paid, overdue, cancelled }

FeePaymentState _state(Object? value) => switch ('$value') {
      'partial' => FeePaymentState.partial,
      'paid' => FeePaymentState.paid,
      'overdue' => FeePaymentState.overdue,
      'cancelled' => FeePaymentState.cancelled,
      _ => FeePaymentState.unpaid,
    };

String feeStateLabel(FeePaymentState state) => switch (state) {
      FeePaymentState.unpaid => 'غير مدفوع',
      FeePaymentState.partial => 'مدفوع جزئيًا',
      FeePaymentState.paid => 'مدفوع',
      FeePaymentState.overdue => 'متأخر',
      FeePaymentState.cancelled => 'ملغى',
    };

String paymentMethodLabel(String method) => switch (method) {
      'cash' => 'نقدًا',
      'bank_transfer' => 'تحويل بنكي',
      'card' => 'بطاقة',
      'cheque' => 'شيك',
      _ => 'أخرى',
    };

String formatMoney(double value, String? currency) {
  final fixed = value == value.roundToDouble()
      ? value.toStringAsFixed(0)
      : value.toStringAsFixed(2);
  final parts = fixed.split('.');
  final whole = parts.first.replaceAllMapped(
    RegExp(r'\B(?=(\d{3})+(?!\d))'),
    (_) => ',',
  );
  final text = parts.length > 1 ? '$whole.${parts[1]}' : whole;
  return currency == null || currency.isEmpty ? text : '$text $currency';
}

class FeeSummary {
  const FeeSummary({
    required this.currency,
    required this.total,
    required this.paid,
    required this.remaining,
    required this.overdue,
    required this.overdueCount,
    required this.feeCount,
    this.nextDueTitle,
    this.nextDueDate,
    this.nextDueBalance,
  });

  final String? currency;
  final double total;
  final double paid;
  final double remaining;
  final double overdue;
  final int overdueCount;
  final int feeCount;
  final String? nextDueTitle;
  final String? nextDueDate;
  final double? nextDueBalance;

  bool get hasDues => remaining > 0;
  double get progress => total <= 0 ? 0 : (paid / total).clamp(0, 1).toDouble();

  factory FeeSummary.fromJson(Map<String, dynamic> json) {
    final next = json['next_due'] is Map
        ? Map<String, dynamic>.from(json['next_due'] as Map)
        : null;
    return FeeSummary(
      currency: json['currency'] as String?,
      total: _money(json['total']),
      paid: _money(json['paid']),
      remaining: _money(json['remaining']),
      overdue: _money(json['overdue']),
      overdueCount: (json['overdue_count'] as num?)?.toInt() ?? 0,
      feeCount: (json['fee_count'] as num?)?.toInt() ?? 0,
      nextDueTitle: next?['title'] as String?,
      nextDueDate: next?['due_date'] as String?,
      nextDueBalance: next == null ? null : _money(next['balance']),
    );
  }
}

class ParentFee {
  const ParentFee({
    required this.id,
    required this.title,
    required this.categoryName,
    required this.netAmount,
    required this.paidAmount,
    required this.balance,
    required this.currency,
    required this.dueDate,
    required this.state,
    required this.installmentNumber,
    required this.installmentCount,
  });

  final int id;
  final String title;
  final String categoryName;
  final double netAmount;
  final double paidAmount;
  final double balance;
  final String currency;
  final String dueDate;
  final FeePaymentState state;
  final int installmentNumber;
  final int installmentCount;

  factory ParentFee.fromJson(Map<String, dynamic> json) => ParentFee(
        id: (json['id'] as num).toInt(),
        title: '${json['title'] ?? ''}',
        categoryName: '${json['category_name'] ?? ''}',
        netAmount: _money(json['net_amount']),
        paidAmount: _money(json['paid_amount']),
        balance: _money(json['balance']),
        currency: '${json['currency'] ?? ''}',
        dueDate: '${json['due_date'] ?? ''}',
        state: _state(json['payment_state']),
        installmentNumber: (json['installment_number'] as num?)?.toInt() ?? 1,
        installmentCount: (json['installment_count'] as num?)?.toInt() ?? 1,
      );
}

class ParentFeePayment {
  const ParentFeePayment({
    required this.id,
    required this.receiptNumber,
    required this.feeTitle,
    required this.amount,
    required this.currency,
    required this.method,
    required this.paidOn,
  });

  final int id;
  final String receiptNumber;
  final String feeTitle;
  final double amount;
  final String currency;
  final String method;
  final String paidOn;

  factory ParentFeePayment.fromJson(Map<String, dynamic> json) =>
      ParentFeePayment(
        id: (json['id'] as num).toInt(),
        receiptNumber: '${json['receipt_number'] ?? ''}',
        feeTitle: '${json['fee_title'] ?? ''}',
        amount: _money(json['amount']),
        currency: '${json['currency'] ?? ''}',
        method: '${json['method'] ?? ''}',
        paidOn: '${json['paid_on'] ?? ''}',
      );
}

class ParentFeesData {
  const ParentFeesData({
    required this.summary,
    required this.fees,
    required this.payments,
    required this.lastUpdated,
    this.offline = false,
  });

  final FeeSummary summary;
  final List<ParentFee> fees;
  final List<ParentFeePayment> payments;
  final DateTime lastUpdated;
  final bool offline;

  factory ParentFeesData.fromJson(
    Map<String, dynamic> json,
    DateTime lastUpdated, {
    bool offline = false,
  }) =>
      ParentFeesData(
        summary: FeeSummary.fromJson(
            Map<String, dynamic>.from(json['summary'] as Map? ?? const {})),
        fees: [
          for (final item in json['fees'] as List? ?? const [])
            ParentFee.fromJson(Map<String, dynamic>.from(item as Map)),
        ],
        payments: [
          for (final item in json['payments'] as List? ?? const [])
            ParentFeePayment.fromJson(Map<String, dynamic>.from(item as Map)),
        ],
        lastUpdated: lastUpdated,
        offline: offline,
      );
}
