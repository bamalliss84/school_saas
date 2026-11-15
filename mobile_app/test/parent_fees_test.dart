import 'package:dio/dio.dart';
import 'package:drift/native.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:school_saas_mobile/core/local_database/app_database.dart';
import 'package:school_saas_mobile/features/parent/data/parent_fees_repository.dart';
import 'package:school_saas_mobile/features/parent/domain/parent_fee_models.dart';
import 'package:school_saas_mobile/features/parent/presentation/parent_fees_controller.dart';
import 'package:school_saas_mobile/features/parent/presentation/parent_fees_screens.dart';

const scope = CacheScope(localUserKey: 'user:7', membershipId: 41, academicYearKey: '8');

Map<String, dynamic> feesJson({String overdue = '0.00', String remaining = '30000.00'}) => {
  'student_id': 1,
  'summary': {
    'currency': 'YER', 'total': '50000.00', 'paid': '20000.00', 'remaining': remaining, 'overdue': overdue,
    'overdue_count': overdue == '0.00' ? 0 : 1, 'fee_count': 2,
    'next_due': {'fee_id': 2, 'title': 'الفصل الثاني', 'due_date': '2027-01-10', 'balance': '25000.00'},
  },
  'fees': [
    {'id': 1, 'title': 'الفصل الأول', 'category_name': 'رسوم دراسية', 'net_amount': '25000.00', 'paid_amount': '20000.00',
     'balance': '5000.00', 'currency': 'YER', 'due_date': '2026-10-01', 'payment_state': 'partial',
     'installment_number': 1, 'installment_count': 2},
    {'id': 2, 'title': 'الفصل الثاني', 'category_name': 'رسوم دراسية', 'net_amount': '25000.00', 'paid_amount': '0.00',
     'balance': '25000.00', 'currency': 'YER', 'due_date': '2027-01-10', 'payment_state': 'unpaid',
     'installment_number': 2, 'installment_count': 2},
  ],
  'payments': [
    {'id': 9, 'receipt_number': 'R2026-000003', 'fee_title': 'الفصل الأول', 'amount': '20000.00', 'currency': 'YER',
     'method': 'cash', 'paid_on': '2026-10-02'},
  ],
};

Widget app(Widget child) => MaterialApp(
    home: Directionality(textDirection: TextDirection.rtl, child: Scaffold(body: child)));

Dio dioReturning(Object data, {List<RequestOptions>? log}) => Dio()
  ..interceptors.add(InterceptorsWrapper(onRequest: (options, handler) {
    log?.add(options);
    handler.resolve(Response(requestOptions: options, data: data));
  }));

void main() {
  test('fee models parse money, states and next due', () {
    final data = ParentFeesData.fromJson(feesJson(), DateTime.utc(2026, 11, 15));
    expect(data.summary.remaining, 30000);
    expect(data.summary.progress, closeTo(.4, .001));
    expect(data.summary.nextDueDate, '2027-01-10');
    expect(data.fees.first.state, FeePaymentState.partial);
    expect(data.payments.single.receiptNumber, 'R2026-000003');
    expect(formatMoney(1234567.5, 'YER'), '1,234,567.50 YER');
    expect(formatMoney(30000, null), '30,000');
  });

  test('repository calls the child fee endpoint and isolates cache per child and membership', () async {
    final log = <RequestOptions>[];
    final db = AppDatabase.forTesting(NativeDatabase.memory());
    addTearDown(db.close);
    final repository = ParentFeesRepository(dioReturning(feesJson(), log: log), db);
    await repository.refresh(scope, 1);
    expect(log.single.path, 'parents/me/children/1/fees/');
    expect((await repository.read(scope, 1))?.summary.remaining, 30000);
    expect(await repository.read(scope, 2), isNull);
    expect(await repository.read(const CacheScope(localUserKey: 'user:7', membershipId: 99, academicYearKey: '8'), 1), isNull);
  });

  test('repository falls back to cache offline and maps 404 to not allowed', () async {
    final db = AppDatabase.forTesting(NativeDatabase.memory());
    addTearDown(db.close);
    await ParentFeesRepository(dioReturning(feesJson()), db).refresh(scope, 1);
    final offline = Dio()
      ..interceptors.add(InterceptorsWrapper(onRequest: (options, handler) =>
          handler.reject(DioException(requestOptions: options, type: DioExceptionType.connectionError))));
    final cached = await ParentFeesRepository(offline, db).load(scope, 1);
    expect(cached.offline, isTrue);
    final forbidden = Dio()
      ..interceptors.add(InterceptorsWrapper(onRequest: (options, handler) => handler.reject(DioException(
            requestOptions: options,
            type: DioExceptionType.badResponse,
            response: Response(requestOptions: options, statusCode: 404),
          ))));
    expect(ParentFeesRepository(forbidden, db).refresh(scope, 2), throwsA(isA<ParentFeesUnavailable>()));
  });

  testWidgets('fees screen shows summary, installments and receipts read-only', (tester) async {
    final data = ParentFeesData.fromJson(feesJson(), DateTime.now().toUtc());
    await tester.pumpWidget(app(ParentFeesScreen(
      state: ParentFeesReady(data), childName: 'أحمد سالم', historical: false, onRefresh: () async {},
    )));
    expect(find.text('30,000 YER'), findsOneWidget);
    expect(find.text('الفصل الأول (قسط 1/2)'), findsOneWidget);
    expect(find.text('مدفوع جزئيًا'), findsOneWidget);
    await tester.scrollUntilVisible(find.textContaining('R2026-000003'), 200);
    expect(find.textContaining('R2026-000003'), findsOneWidget);
    expect(find.byType(ElevatedButton), findsNothing);
    expect(find.byType(FilledButton), findsNothing);
  });

  testWidgets('not-allowed state explains the financial permission', (tester) async {
    await tester.pumpWidget(app(ParentFeesScreen(
      state: const ParentFeesNotAllowed(), childName: 'أحمد', historical: false, onRefresh: () async {},
    )));
    expect(find.textContaining('لا تتوفر لك صلاحية'), findsOneWidget);
  });

  testWidgets('home alert highlights overdue dues and hides when nothing is owed', (tester) async {
    var opened = 0;
    final overdue = ParentFeesData.fromJson(feesJson(overdue: '5000.00'), DateTime.now().toUtc());
    await tester.pumpWidget(app(ParentFeeAlertCard(state: ParentFeesReady(overdue), onOpen: () => opened++)));
    expect(find.text('رسوم متأخرة'), findsOneWidget);
    expect(find.textContaining('5,000 YER'), findsOneWidget);
    await tester.tap(find.byKey(const Key('parent-fee-alert')));
    expect(opened, 1);

    final cleared = ParentFeesData.fromJson(feesJson(remaining: '0.00'), DateTime.now().toUtc());
    await tester.pumpWidget(app(ParentFeeAlertCard(state: ParentFeesReady(cleared), onOpen: () {})));
    expect(find.byKey(const Key('parent-fee-alert')), findsNothing);
    await tester.pumpWidget(app(ParentFeeAlertCard(state: const ParentFeesNotAllowed(), onOpen: () {})));
    expect(find.byKey(const Key('parent-fee-alert')), findsNothing);
  });
}
