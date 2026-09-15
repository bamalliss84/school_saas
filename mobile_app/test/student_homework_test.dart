import 'package:dio/dio.dart';
import 'package:drift/native.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:school_saas_mobile/core/local_database/app_database.dart';
import 'package:school_saas_mobile/features/student/homework/data/homework_local_data_source.dart';
import 'package:school_saas_mobile/features/student/homework/data/homework_remote_data_source.dart';
import 'package:school_saas_mobile/features/student/homework/data/homework_repository.dart';
import 'package:school_saas_mobile/features/student/homework/domain/homework_models.dart';
import 'package:school_saas_mobile/features/student/homework/presentation/homework_controller.dart';
import 'package:school_saas_mobile/features/student/homework/presentation/homework_screens.dart';

Map<String, dynamic> homeworkJson({
  int id = 11,
  String completion = 'not_started',
  bool canCreate = true,
  bool canSubmit = true,
  String teacherNote = '',
  String? grade,
  String submissionType = 'text',
}) =>
    {
      'id': id,
      'title': 'تمارين المعادلات والجبر',
      'description': 'حل الأسئلة المطلوبة مع توضيح خطوات الحل.',
      'subject_name': 'الرياضيات',
      'classroom_id': 6,
      'section_id': 1,
      'teacher': 'معلم الرياضيات',
      'due_date': '2026-08-20T09:00:00Z',
      'completion_status': completion,
      'submission_type': submissionType,
      'can_create_draft': canCreate,
      'can_final_submit': canSubmit,
      'max_grade': '10',
      'grade': grade,
      'teacher_note': teacherNote,
      'attachments': [
        {
          'id': 2,
          'file': 'http://example.test/question.pdf',
          'original_name': 'questions.pdf',
          'content_type': 'application/pdf',
          'file_size': 1024,
        }
      ],
    };

Map<String, dynamic> submissionJson({
  int id = 21,
  String status = 'draft',
  String answer = 'إجابتي',
  bool canEdit = true,
  bool canSubmit = true,
  String? teacherNote,
  DateTime? returnedAt,
}) =>
    {
      'id': id,
      'answer': answer,
      'status': status,
      'can_edit': canEdit,
      'can_submit': canSubmit,
      'teacher_note': teacherNote ??
          (status == 'returned' || status == 'reviewed'
              ? 'راجع السؤال الرابع'
              : ''),
      'grade': status == 'graded' ? '9' : null,
      'returned_at': returnedAt?.toIso8601String(),
      'attachments': [
        {
          'id': 7,
          'file': 'http://example.test/answer.pdf',
          'original_name': 'answer.pdf',
          'content_type': 'application/pdf',
          'file_size': 2048,
        }
      ],
    };

class FakeHomeworkRemote implements HomeworkRemoteDataSource {
  FakeHomeworkRemote({
    this.fail = false,
    this.httpStatus,
    this.submissionRow,
    this.homeworkRow,
  });
  bool fail;
  int? httpStatus;
  Map<String, dynamic>? submissionRow;
  Map<String, dynamic>? homeworkRow;
  bool finalSubmitted = false;

  void check() {
    if (httpStatus != null) {
      final request = RequestOptions(path: '/homework');
      throw DioException(
        requestOptions: request,
        response: Response(requestOptions: request, statusCode: httpStatus),
        type: DioExceptionType.badResponse,
      );
    }
    if (fail) throw DioException(requestOptions: RequestOptions());
  }

  @override
  Future<List<Map<String, dynamic>>> list() async {
    check();
    return [homeworkRow ?? homeworkJson()];
  }

  @override
  Future<Map<String, dynamic>> detail(int homeworkId) async {
    check();
    return homeworkRow ?? homeworkJson(id: homeworkId);
  }

  @override
  Future<Map<String, dynamic>?> submission(int homeworkId) async {
    check();
    return submissionRow;
  }

  @override
  Future<Map<String, dynamic>> createSubmission(int homeworkId) async {
    check();
    submissionRow = submissionJson();
    return submissionRow!;
  }

  @override
  Future<Map<String, dynamic>> updateAnswer(
      int submissionId, String answer) async {
    check();
    submissionRow = submissionJson(id: submissionId, answer: answer);
    return submissionRow!;
  }

  @override
  Future<Map<String, dynamic>> finalSubmit(int submissionId) async {
    check();
    finalSubmitted = true;
    submissionRow = submissionJson(
        id: submissionId,
        status: 'submitted',
        canEdit: false,
        canSubmit: false);
    return submissionRow!;
  }

  @override
  Future<List<Map<String, dynamic>>> uploadSubmissionAttachments(
      int submissionId, List<String> paths) async {
    check();
    return [
      {
        'id': 8,
        'file': 'http://example.test/upload.pdf',
        'original_name': 'upload.pdf',
        'content_type': 'application/pdf',
        'file_size': 100,
      }
    ];
  }

  @override
  Future<void> deleteSubmissionAttachment(
      int submissionId, int attachmentId) async {
    check();
  }

  @override
  Future<String> downloadAttachment(String url, String fileName) async {
    check();
    return '/app/$fileName';
  }
}

const scopeA = CacheScope(
    localUserKey: 'user:1', membershipId: 10, academicYearKey: '2026');
const scopeB = CacheScope(
    localUserKey: 'user:1', membershipId: 20, academicYearKey: '2026');
const scopeOtherUser = CacheScope(
    localUserKey: 'user:2', membershipId: 10, academicYearKey: '2026');

void main() {
  test('homework and submission parsing preserves backend lifecycle', () {
    final returned = StudentHomework.fromJson(
        homeworkJson(completion: 'returned', teacherNote: 'راجع الحل'));
    final graded = HomeworkSubmissionModel.fromJson(
        submissionJson(status: 'graded', canEdit: false, canSubmit: false));
    expect(returned.completionStatus, 'returned');
    expect(returned.teacherNote, 'راجع الحل');
    expect(returned.attachments.single.name, 'questions.pdf');
    expect(graded.status, 'graded');
    expect(graded.grade, 9);
    expect(graded.attachments.single.name, 'answer.pdf');
    expect(graded.canEdit, isFalse);
  });

  test('list and detail cache are isolated by membership and user', () async {
    final db = AppDatabase.forTesting(NativeDatabase.memory());
    addTearDown(db.close);
    final local = HomeworkLocalDataSource(db);
    final repo = StudentHomeworkRepository(FakeHomeworkRemote(), local);
    await repo.refreshList(scopeA);
    await repo.loadDetail(scopeA, 11);
    expect((await repo.readList(scopeA))!.items.single.id, 11);
    expect(await repo.readList(scopeB), isNull);
    expect(await repo.readList(scopeOtherUser), isNull);
    expect(await db.readHomeworkItem(scopeB, 11), isNull);
  });

  test('local draft persists and remains isolated', () async {
    final db = AppDatabase.forTesting(NativeDatabase.memory());
    addTearDown(db.close);
    final local = HomeworkLocalDataSource(db);
    const draft =
        HomeworkLocalDraft(answer: 'حل محفوظ', studentNote: 'ملاحظة شخصية');
    await local.saveDraft(scopeA, 11, draft);
    expect((await local.readDraft(scopeA, 11)).answer, 'حل محفوظ');
    expect((await local.readDraft(scopeB, 11)).answer, isEmpty);
    expect((await local.readDraft(scopeOtherUser, 11)).studentNote, isEmpty);
  });

  Future<String> listStatusWithDraft({
    required String completion,
    required String submissionType,
    required bool persistDraft,
    String answer = 'draft answer',
  }) async {
    final db = AppDatabase.forTesting(NativeDatabase.memory());
    addTearDown(db.close);
    final local = HomeworkLocalDataSource(db);
    if (persistDraft) {
      await local.saveDraft(
        scopeA,
        11,
        HomeworkLocalDraft(answer: answer),
      );
    }
    final repo = StudentHomeworkRepository(
      FakeHomeworkRemote(
        homeworkRow: homeworkJson(
          completion: completion,
          submissionType: submissionType,
        ),
      ),
      local,
    );
    return (await repo.refreshList(scopeA)).items.single.completionStatus;
  }

  test('no persisted local draft leaves student list not started', () async {
    expect(
      await listStatusWithDraft(
        completion: 'not_started',
        submissionType: 'text',
        persistDraft: false,
      ),
      'not_started',
    );
  });

  test('persisted local draft projects student list as draft', () async {
    expect(
      await listStatusWithDraft(
        completion: 'not_started',
        submissionType: 'text',
        persistDraft: true,
      ),
      'draft',
    );
  });

  test('persisted intentionally-empty draft still projects as draft',
      () async {
    expect(
      await listStatusWithDraft(
        completion: 'not_started',
        submissionType: 'text',
        persistDraft: true,
        answer: '',
      ),
      'draft',
    );
  });

  test('local draft never overrides authoritative remote lifecycle', () async {
    for (final status in ['submitted', 'returned', 'graded', 'reviewed']) {
      expect(
        await listStatusWithDraft(
          completion: status,
          submissionType: 'text',
          persistDraft: true,
        ),
        status,
      );
    }
  });

  test('view-only homework never projects local draft status', () async {
    expect(
      await listStatusWithDraft(
        completion: 'view_only',
        submissionType: 'none',
        persistDraft: true,
      ),
      'view_only',
    );
  });

  test('successful save updates list status immediately', () async {
    final db = AppDatabase.forTesting(NativeDatabase.memory());
    addTearDown(db.close);
    final remote = FakeHomeworkRemote();
    final repo = StudentHomeworkRepository(remote, HomeworkLocalDataSource(db));
    final controller = HomeworkController(repo, scopeA);
    await controller.load();
    await controller.open(11);
    await controller.saveDraft(const HomeworkLocalDraft(answer: 'saved'));
    controller.closeDetail();
    expect(
      (controller.state as HomeworkReady).list.items.single.completionStatus,
      'draft',
    );
  });

  test('offline detail falls back to cache and keeps local draft', () async {
    final db = AppDatabase.forTesting(NativeDatabase.memory());
    addTearDown(db.close);
    final remote = FakeHomeworkRemote();
    final local = HomeworkLocalDataSource(db);
    final repo = StudentHomeworkRepository(remote, local);
    await repo.loadDetail(scopeA, 11);
    await repo.saveDraft(
        scopeA, 11, const HomeworkLocalDraft(answer: 'offline answer'));
    remote.fail = true;
    final cached = await repo.loadDetail(scopeA, 11);
    expect(cached.offline, isTrue);
    expect(cached.homework.title, isNotEmpty);
    expect(cached.draft.answer, 'offline answer');
  });

  test('HTTP authorization failure never falls back to cached homework', () async {
    final db = AppDatabase.forTesting(NativeDatabase.memory());
    addTearDown(db.close);
    final remote = FakeHomeworkRemote();
    final local = HomeworkLocalDataSource(db);
    final repo = StudentHomeworkRepository(remote, local);
    await repo.loadDetail(scopeA, 11);
    remote.httpStatus = 403;
    expect(() => repo.loadDetail(scopeA, 11), throwsA(isA<DioException>()));
  });

  test('offline without cache reports failure', () async {
    final db = AppDatabase.forTesting(NativeDatabase.memory());
    addTearDown(db.close);
    final repo = StudentHomeworkRepository(
        FakeHomeworkRemote(fail: true), HomeworkLocalDataSource(db));
    expect(() => repo.loadDetail(scopeA, 999), throwsA(isA<DioException>()));
  });

  test('failed final submit preserves local draft', () async {
    final db = AppDatabase.forTesting(NativeDatabase.memory());
    addTearDown(db.close);
    final remote = FakeHomeworkRemote();
    final local = HomeworkLocalDataSource(db);
    final repo = StudentHomeworkRepository(remote, local);
    await repo.saveDraft(
        scopeA, 11, const HomeworkLocalDraft(answer: 'keep me'));
    final detail = await repo.loadDetail(scopeA, 11);
    remote.fail = true;
    expect(() => repo.submit(scopeA, detail), throwsA(isA<DioException>()));
    expect((await local.readDraft(scopeA, 11)).answer, 'keep me');
  });

  test('successful final submit clears draft only after confirmation',
      () async {
    final db = AppDatabase.forTesting(NativeDatabase.memory());
    addTearDown(db.close);
    final remote = FakeHomeworkRemote();
    final local = HomeworkLocalDataSource(db);
    final repo = StudentHomeworkRepository(remote, local);
    await repo.saveDraft(
        scopeA, 11, const HomeworkLocalDraft(answer: 'submit me'));
    final detail = await repo.loadDetail(scopeA, 11);
    await repo.submit(scopeA, detail);
    expect(remote.finalSubmitted, isTrue);
    expect((await local.readDraft(scopeA, 11)).answer, isEmpty);
  });

  test('controller blocks final submit from offline cached detail', () async {
    final db = AppDatabase.forTesting(NativeDatabase.memory());
    addTearDown(db.close);
    final remote = FakeHomeworkRemote();
    final repo = StudentHomeworkRepository(remote, HomeworkLocalDataSource(db));
    await repo.refreshList(scopeA);
    await repo.loadDetail(scopeA, 11);
    remote.fail = true;
    final controller = HomeworkController(repo, scopeA);
    await controller.load();
    await controller.open(11);
    expect(
        (controller.state as HomeworkReady).detail, isA<HomeworkDetailReady>());
    expect(await controller.submit(), isFalse);
    expect(remote.finalSubmitted, isFalse);
  });

  Future<void> pumpHomeworkDetail(
    WidgetTester tester, {
    required String submissionType,
    HomeworkDetailData? data,
    Future<void> Function(HomeworkLocalDraft)? onSave,
  }) async {
    await tester.binding.setSurfaceSize(const Size(800, 1600));
    addTearDown(() => tester.binding.setSurfaceSize(null));
    final item = StudentHomework.fromJson(
      homeworkJson(submissionType: submissionType),
    );
    await tester.pumpWidget(MaterialApp(
      home: Scaffold(
        body: StudentHomeworkDetailScreen(
          data: data ??
              HomeworkDetailData(
                  item, const HomeworkLocalDraft(), DateTime(2026)),
          historical: false,
          submitting: false,
          onBack: () {},
          onSave: onSave ?? (_) async {},
          onSubmit: () async => false,
          onUploadAttachments: (_) async => false,
          onDeleteAttachment: (_) async => false,
          onDownload: (_) async => '',
        ),
      ),
    ));
    await tester.pumpAndSettle();
  }

  HomeworkDetailData returnedDetail({
    HomeworkLocalDraft? draft,
    String answer = 'this is my solve',
    DateTime? returnedAt,
  }) {
    final homework = StudentHomework.fromJson(homeworkJson(
      completion: 'returned',
      canCreate: false,
      canSubmit: true,
    )).withSubmission(HomeworkSubmissionModel.fromJson(submissionJson(
      status: 'returned',
      answer: answer,
      returnedAt: returnedAt,
    )));
    return HomeworkDetailData(
      homework,
      draft ?? const HomeworkLocalDraft(),
      DateTime(2026),
    );
  }

  String answerFieldText(WidgetTester tester) =>
      tester.widget<TextField>(find.byType(TextField).first).controller!.text;

  testWidgets('returned submission without local draft prefills remote answer',
      (tester) async {
    await pumpHomeworkDetail(
      tester,
      submissionType: 'text',
      data: returnedDetail(),
    );
    expect(answerFieldText(tester), 'this is my solve');
  });

  testWidgets('returned submission prefers persisted local revision draft',
      (tester) async {
    await pumpHomeworkDetail(
      tester,
      submissionType: 'text',
      data: returnedDetail(
        draft: HomeworkLocalDraft(
          answer: 'my revised answer',
          updatedAt: DateTime(2026),
        ),
      ),
    );
    expect(answerFieldText(tester), 'my revised answer');
  });

  testWidgets('returned submission preserves persisted empty revision draft',
      (tester) async {
    await pumpHomeworkDetail(
      tester,
      submissionType: 'text',
      data: returnedDetail(
        draft: HomeworkLocalDraft(answer: '', updatedAt: DateTime(2026)),
      ),
    );
    expect(answerFieldText(tester), isEmpty);
  });

  testWidgets('new homework without submission keeps empty answer behavior',
      (tester) async {
    await pumpHomeworkDetail(tester, submissionType: 'text');
    expect(answerFieldText(tester), isEmpty);
  });

  testWidgets('mounted detail refreshes on transition into returned lifecycle',
      (tester) async {
    await pumpHomeworkDetail(tester, submissionType: 'text');
    await pumpHomeworkDetail(
      tester,
      submissionType: 'text',
      data: returnedDetail(),
    );
    expect(answerFieldText(tester), 'this is my solve');
  });

  testWidgets('ordinary rebuild does not overwrite active student edits',
      (tester) async {
    final data = returnedDetail(returnedAt: DateTime(2026, 9, 12));
    await pumpHomeworkDetail(
      tester,
      submissionType: 'text',
      data: data,
    );
    await tester.enterText(find.byType(TextField).first, 'revision in progress');
    await pumpHomeworkDetail(
      tester,
      submissionType: 'text',
      data: data,
    );
    expect(answerFieldText(tester), 'revision in progress');
  });

  testWidgets('new returnedAt lifecycle refreshes untouched controller',
      (tester) async {
    await pumpHomeworkDetail(
      tester,
      submissionType: 'text',
      data: returnedDetail(
        answer: 'first submitted answer',
        returnedAt: DateTime(2026, 9, 12),
      ),
    );
    await pumpHomeworkDetail(
      tester,
      submissionType: 'text',
      data: returnedDetail(
        answer: 'second submitted answer',
        returnedAt: DateTime(2026, 9, 13),
      ),
    );
    expect(answerFieldText(tester), 'second submitted answer');
  });

  testWidgets('non-persisted empty placeholder does not mask server answer',
      (tester) async {
    await pumpHomeworkDetail(
      tester,
      submissionType: 'text',
      data: returnedDetail(draft: const HomeworkLocalDraft(answer: '')),
    );
    expect(answerFieldText(tester), 'this is my solve');
  });

  testWidgets('reviewed homework shows feedback and remains read only',
      (tester) async {
    final homework = StudentHomework.fromJson(homeworkJson(
      completion: 'reviewed',
      canCreate: false,
      canSubmit: false,
      teacherNote: 'أحسنت، تمت مراجعة الإجابة',
    )).withSubmission(HomeworkSubmissionModel.fromJson(submissionJson(
      status: 'reviewed',
      canEdit: false,
      canSubmit: false,
      teacherNote: 'أحسنت، تمت مراجعة الإجابة',
    )));
    await pumpHomeworkDetail(
      tester,
      submissionType: 'text',
      data: HomeworkDetailData(
        homework,
        const HomeworkLocalDraft(),
        DateTime(2026),
      ),
    );
    expect(find.text('تمت المراجعة'), findsWidgets);
    expect(find.text('أحسنت، تمت مراجعة الإجابة'), findsOneWidget);
    expect(find.text('إجابتي'), findsNothing);
    expect(find.text('إرسال الواجب'), findsNothing);
    expect(find.byType(TextField), findsNothing);
  });

  testWidgets('successful Save Draft shows confirmation without navigating',
      (tester) async {
    var saved = false;
    await pumpHomeworkDetail(
      tester,
      submissionType: 'text',
      onSave: (_) async {
        saved = true;
      },
    );
    await tester.tap(find.text('حفظ كمسودة'));
    await tester.pump();
    expect(saved, isTrue);
    expect(find.text('تم حفظ المسودة'), findsOneWidget);
    expect(find.text('إجابتي'), findsOneWidget);
  });

  testWidgets('failed Save Draft does not show success confirmation',
      (tester) async {
    await pumpHomeworkDetail(
      tester,
      submissionType: 'text',
      onSave: (_) => Future<void>.error(StateError('save failed')),
    );
    await tester.tap(find.text('حفظ كمسودة'));
    await tester.pump();
    expect(find.text('تم حفظ المسودة'), findsNothing);
  });

  testWidgets('homework detail labels instructions and teacher attachments',
      (tester) async {
    await pumpHomeworkDetail(tester, submissionType: 'text');
    expect(find.text('المطلوب'), findsOneWidget);
    expect(find.text('حل الأسئلة المطلوبة مع توضيح خطوات الحل.'), findsOneWidget);
    expect(find.text('مرفقات المعلم'), findsOneWidget);
    expect(find.text('questions.pdf'), findsOneWidget);
    expect(find.text('إجابتي'), findsOneWidget);
    expect(find.text('إرفاق صورة أو PDF'), findsNothing);
  });

  testWidgets('none submission hides answer upload and submit', (tester) async {
    await pumpHomeworkDetail(tester, submissionType: 'none');
    expect(find.text('هذا الواجب للمتابعة فقط ولا يحتاج إلى تسليم إلكتروني.'),
        findsOneWidget);
    expect(find.text('إجابتي'), findsNothing);
    expect(find.text('إرفاق صورة أو PDF'), findsNothing);
    expect(find.text('حفظ كمسودة'), findsNothing);
    expect(find.text('إرسال الواجب'), findsNothing);
    expect(find.byType(TextField), findsNothing);
  });

  testWidgets('attachment submission shows upload without text answer',
      (tester) async {
    await pumpHomeworkDetail(tester, submissionType: 'attachment');
    expect(find.text('إجابتي'), findsNothing);
    expect(find.text('إرفاق صورة أو PDF'), findsOneWidget);
    expect(find.text('إرسال الواجب'), findsOneWidget);
  });

  testWidgets('text and attachment submission shows both controls',
      (tester) async {
    await pumpHomeworkDetail(tester, submissionType: 'text_and_attachment');
    expect(find.text('إجابتي'), findsOneWidget);
    expect(find.text('إرفاق صورة أو PDF'), findsOneWidget);
    expect(find.text('إرسال الواجب'), findsOneWidget);
  });

  testWidgets('historical detail is read only', (tester) async {
    final item = StudentHomework.fromJson(homeworkJson());
    await tester.pumpWidget(MaterialApp(
      home: Scaffold(
        body: StudentHomeworkDetailScreen(
          data: HomeworkDetailData(
              item, const HomeworkLocalDraft(), DateTime(2026)),
          historical: true,
          submitting: false,
          onBack: () {},
          onSave: (_) async {},
          onSubmit: () async => false,
          onUploadAttachments: (_) async => false,
          onDeleteAttachment: (_) async => false,
          onDownload: (_) async => '',
        ),
      ),
    ));
    expect(find.text('السجل الدراسي السابق — للعرض فقط'), findsOneWidget);
    expect(find.text('إرسال الواجب'), findsNothing);
    expect(find.byType(TextField), findsNothing);
  });

  testWidgets('long Arabic homework tolerates 150 percent text scale',
      (tester) async {
    await tester.binding.setSurfaceSize(const Size(320, 640));
    addTearDown(() => tester.binding.setSurfaceSize(null));
    final item = StudentHomework.fromJson({
      ...homeworkJson(),
      'title': 'واجب اللغة العربية الطويل جدًا في القراءة والتحليل والنحو',
      'teacher': 'المعلم صاحب الاسم العربي الطويل للاختبار',
    });
    await tester.pumpWidget(MaterialApp(
      home: MediaQuery(
        data: const MediaQueryData(textScaler: TextScaler.linear(1.5)),
        child: Directionality(
          textDirection: TextDirection.rtl,
          child: Scaffold(body: HomeworkCard(homework: item, onTap: () {})),
        ),
      ),
    ));
    expect(tester.takeException(), isNull);
  });

  test('homework submission type parsing keeps legacy default and mode flags', () {
    final base = <String, dynamic>{
      'id': 501,
      'title': 'Mode demo',
      'description': 'Details',
      'subject_name': 'Math',
      'classroom_id': 1,
      'section_id': 1,
      'teacher': 'Teacher',
      'due_date': '2026-09-01T10:00:00Z',
      'completion_status': 'not_started',
      'can_create_draft': true,
      'can_final_submit': true,
      'attachments': const [],
    };
    final legacy = StudentHomework.fromJson(base);
    expect(legacy.submissionType, 'text');
    expect(legacy.acceptsText, isTrue);
    expect(legacy.acceptsAttachments, isFalse);

    final attachment = StudentHomework.fromJson(
      {...base, 'submission_type': 'attachment'},
    );
    expect(attachment.acceptsText, isFalse);
    expect(attachment.acceptsAttachments, isTrue);

    final viewOnly = StudentHomework.fromJson(
      {...base, 'submission_type': 'none'},
    );
    expect(viewOnly.requiresElectronicSubmission, isFalse);
    expect(viewOnly.canEditDraft, isTrue);
    expect(viewOnly.canEditElectronicDraft, isFalse);
  });

}
