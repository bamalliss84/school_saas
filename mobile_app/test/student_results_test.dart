import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:school_saas_mobile/features/student/results/data/results_repository.dart';
import 'package:school_saas_mobile/features/student/results/domain/result_models.dart';
import 'package:school_saas_mobile/features/student/results/presentation/results_controller.dart';
import 'package:school_saas_mobile/features/student/results/presentation/results_screens.dart';

StudentResult _result({
  required int id,
  required int examTypeId,
  required String examTypeName,
  String subject = 'الرياضيات',
  String term = 'الفصل الأول',
  bool published = true,
  String status = 'present',
  double? score = 18,
  double? percentage = 90,
}) =>
    StudentResult(
      id: id,
      examId: id,
      examTitle: 'اختبار $examTypeName',
      subject: subject,
      examDate: DateTime(2026, 8, 20),
      examTypeId: examTypeId,
      examTypeName: examTypeName,
      examTypeCode: 'TYPE_$examTypeId',
      totalMarks: 20,
      score: score,
      percentage: percentage,
      status: status,
      academicTermId: term == 'الفصل الأول' ? 1 : 2,
      academicTermName: term,
      isPublished: published,
    );

ResultsReady _ready(
  List<StudentResult> items, {
  String? term,
  String? subject,
  int? examTypeId,
}) =>
    ResultsReady(
      StudentResultsData(items, DateTime(2026, 8, 22)),
      term: term,
      subject: subject,
      examTypeId: examTypeId,
    );

Widget _resultsApp(ResultsReady state) => MaterialApp(
      home: Directionality(
        textDirection: TextDirection.rtl,
        child: Scaffold(
          body: StudentResultsScreen(
            state: state,
            historical: false,
            onTerm: (_) {},
            onSubject: (_) {},
            onExamType: (_) {},
            onOpen: (_) {},
            onRefresh: () async {},
          ),
        ),
      ),
    );

void main() {
  test('student result parses score total percentage and feedback contract',
      () {
    final result = StudentResult.fromJson({
      'id': 7,
      'exam': 3,
      'exam_title': 'اختبار منتصف الفصل',
      'subject_name': 'الرياضيات',
      'exam_date': '2026-08-19',
      'exam_type_id': 5,
      'exam_type_name': 'اختبار منتصف الفصل',
      'exam_type_code': 'MIDTERM',
      'total_marks': '20.00',
      'score': '18.00',
      'percentage': '90.00',
      'status': 'present',
      'academic_term_id': 2,
      'academic_term_name': 'الفصل الدراسي الأول',
      'remarks': 'أداء ممتاز',
      'is_published': true,
      'published_at': '2026-08-22T08:00:00Z',
    });

    expect(result.scoreLabel, '18 من 20');
    expect(result.percentageLabel, '90%');
    expect(result.examTypeName, 'اختبار منتصف الفصل');
    expect(result.examTypeCode, 'MIDTERM');
    expect(result.remarks, 'أداء ممتاز');
    expect(result.isPublished, isTrue);
  });

  test('student result shows attendance-style result status without fake score',
      () {
    final result = StudentResult.fromJson({
      'id': 8,
      'exam': 4,
      'exam_title': 'اختبار قصير',
      'subject_name': 'العلوم',
      'exam_date': '2026-08-20',
      'exam_type_id': 6,
      'exam_type_name': 'اختبار قصير',
      'exam_type_code': 'QUIZ',
      'total_marks': '10.00',
      'score': null,
      'percentage': null,
      'status': 'absent',
      'academic_term_id': 2,
      'academic_term_name': 'الفصل الدراسي الأول',
      'is_published': true,
    });
    expect(result.scoreLabel, 'غائب');
    expect(result.percentageLabel, '');
  });

  test('published present result displays its numeric score', () {
    final result = _result(
      id: 10,
      examTypeId: 1,
      examTypeName: 'اختبار',
    );

    expect(result.scoreLabel, '18 من 20');
    expect(result.percentageLabel, '90%');
  });

  for (final expectation in const [
    ('absent', 'غائب'),
    ('excused', 'غياب بعذر'),
    ('exempted', 'معفي'),
  ]) {
    test('published ${expectation.$1} result has no numeric score', () {
      final result = _result(
        id: 11,
        examTypeId: 1,
        examTypeName: 'اختبار',
        status: expectation.$1,
        score: 0,
        percentage: 0,
      );

      expect(result.scoreLabel, expectation.$2);
      expect(result.scoreLabel, isNot(contains('0')));
      expect(result.percentageLabel, isEmpty);
    });
  }

  test('unpublished approved-shaped result remains hidden', () {
    final state = _ready([
      _result(
        id: 12,
        examTypeId: 1,
        examTypeName: 'اختبار',
        published: false,
      ),
    ]);

    expect(state.visible, isEmpty);
  });

  test('pending unpublished-shaped result remains hidden', () {
    final state = _ready([
      _result(
        id: 13,
        examTypeId: 1,
        examTypeName: 'اختبار',
        published: false,
        status: 'not_graded',
        score: null,
        percentage: null,
      ),
    ]);

    expect(state.visible, isEmpty);
  });

  test('canonical reload preserves a published special status', () {
    final reloaded = StudentResult.fromJson({
      'id': 14,
      'exam': 4,
      'exam_title': 'اختبار العلوم',
      'subject_name': 'العلوم',
      'exam_date': '2026-09-18',
      'exam_type_id': 1,
      'exam_type_name': 'اختبار',
      'exam_type_code': 'EXAM',
      'total_marks': '20.00',
      'score': null,
      'percentage': null,
      'status': 'excused',
      'academic_term_id': 1,
      'academic_term_name': 'الفصل الأول',
      'is_published': true,
    });

    expect(_ready([reloaded]).visible.single.status, 'excused');
    expect(reloaded.scoreLabel, 'غياب بعذر');
    expect(reloaded.percentageLabel, isEmpty);
  });

  test('available exam types are dynamic, useful, renamed, and ordered by id',
      () {
    final state = _ready([
      _result(id: 1, examTypeId: 9, examTypeName: 'اختبار دوري'),
      _result(id: 2, examTypeId: 3, examTypeName: 'تقييم عملي'),
      _result(
          id: 3,
          examTypeId: 2,
          examTypeName: 'نوع غير منشور',
          published: false),
    ]);

    expect(
      state.availableExamTypes.map((type) => (type.id, type.label)).toList(),
      [(3, 'تقييم عملي'), (9, 'اختبار دوري')],
    );
  });

  test('term subject and stable exam type id filter together', () {
    final state = _ready(
      [
        _result(id: 1, examTypeId: 7, examTypeName: 'اختبار دوري'),
        _result(
            id: 2,
            examTypeId: 7,
            examTypeName: 'اختبار دوري',
            subject: 'العلوم'),
        _result(
            id: 3, examTypeId: 8, examTypeName: 'مشروع', term: 'الفصل الثاني'),
      ],
      term: 'الفصل الأول',
      subject: 'الرياضيات',
      examTypeId: 7,
    );

    expect(state.visible.map((item) => item.id), [1]);
    expect(state.availableExamTypes.map((type) => type.id), [7]);
  });

  test('exam type selection survives compatible filters and clears if invalid',
      () {
    final items = [
      _result(id: 1, examTypeId: 7, examTypeName: 'اختبار دوري'),
      _result(
          id: 2, examTypeId: 7, examTypeName: 'اختبار دوري', subject: 'العلوم'),
      _result(
          id: 3, examTypeId: 8, examTypeName: 'مشروع', term: 'الفصل الثاني'),
    ];

    final compatible =
        _ready(items, subject: 'العلوم', examTypeId: 7).normalizeExamType();
    final invalid =
        _ready(items, term: 'الفصل الثاني', subject: 'الرياضيات', examTypeId: 7)
            .normalizeExamType();

    expect(compatible.examTypeId, 7);
    expect(compatible.subject, 'العلوم');
    expect(invalid.examTypeId, isNull);
    expect(invalid.term, 'الفصل الثاني');
    expect(invalid.subject, 'الرياضيات');
  });

  test('empty and single type cases contain no fake metadata', () {
    expect(_ready(const []).availableExamTypes, isEmpty);
    final single =
        _ready([_result(id: 1, examTypeId: 44, examTypeName: 'شفهي')]);
    expect(single.availableExamTypes.length, 1);
    expect(single.availableExamTypes.single.label, 'شفهي');
  });

  testWidgets('chips card and details use backend exam type name',
      (tester) async {
    final result =
        _result(id: 1, examTypeId: 77, examTypeName: 'تقييم مهاري مخصص');
    await tester.pumpWidget(_resultsApp(_ready([result])));

    expect(find.text('الكل'), findsWidgets);
    expect(find.text('تقييم مهاري مخصص'), findsNWidgets(2));

    await tester.pumpWidget(MaterialApp(
      home: Directionality(
        textDirection: TextDirection.rtl,
        child: Scaffold(
          body: ResultDetailScreen(
            result: result,
            historical: false,
            onBack: () {},
          ),
        ),
      ),
    ));
    expect(find.text('تقييم مهاري مخصص'), findsOneWidget);
  });

  testWidgets('long dynamic exam type is safe at 320x480 and 150 percent',
      (tester) async {
    tester.view.physicalSize = const Size(320, 480);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);
    final result = _result(
      id: 1,
      examTypeId: 88,
      examTypeName:
          'تقييم شامل طويل جدًا للمهارات العلمية والتطبيقية للفصل الدراسي',
      subject: 'الرياضيات المتقدمة ذات الاسم الطويل',
    );

    await tester.pumpWidget(_resultsApp(_ready([result])));
    await tester.pump();

    expect(find.textContaining('تقييم شامل طويل جدًا'), findsWidgets);
    expect(tester.takeException(), isNull);
  });
}
