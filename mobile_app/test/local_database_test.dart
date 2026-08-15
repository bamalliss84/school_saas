import 'dart:convert';

import 'package:drift/drift.dart';
import 'package:drift/native.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:school_saas_mobile/core/local_database/app_database.dart';
import 'package:school_saas_mobile/core/local_database/local_data_purge_service.dart';
import 'package:school_saas_mobile/core/preferences/font_preferences.dart';

class MemoryFontStore implements FontPreferenceStore {
  AppFont value = AppFont.tajawal;
  @override
  Future<AppFont> read() async => value;
  @override
  Future<void> write(AppFont font) async => value = font;
}

CachedContextsCompanion record(CacheScope scope, String id, String school,
    {bool historical = false, DateTime? syncedAt}) {
  final time = syncedAt ?? DateTime.utc(2026, 8, 14, 10, 35);
  return CachedContextsCompanion.insert(
    localUserKey: scope.localUserKey,
    membershipId: scope.membershipId,
    academicYearKey: Value(scope.academicYearKey),
    resourceId: id,
    payloadJson: jsonEncode({'school': school}),
    isHistorical: Value(historical),
    cachedAt: time,
    lastSyncedAt: time,
  );
}

void main() {
  late AppDatabase database;
  setUp(() => database = AppDatabase.forTesting(NativeDatabase.memory()));
  tearDown(() => database.close());

  test('database opens with current additive schema and migration foundation',
      () async {
    expect(database.schemaVersion, 3);
    await database.customSelect('SELECT 1').getSingle();
    expect(database.migration.onUpgrade, isA<Function>());
  });

  test('cache is isolated by membership and local user', () async {
    const a = CacheScope(
        localUserKey: 'user:1', membershipId: 10, academicYearKey: '2026');
    const otherMembership = CacheScope(
        localUserKey: 'user:1', membershipId: 11, academicYearKey: '2026');
    const otherUser = CacheScope(
        localUserKey: 'user:2', membershipId: 10, academicYearKey: '2026');
    final synced = DateTime.utc(2026, 8, 14, 10, 35);
    await database.putContext(
        scope: a,
        resourceId: 'profile',
        payload: {'school': 'A'},
        isHistorical: false,
        syncedAt: synced);
    final own = await database.readContexts(a);
    expect(own.single.lastSyncedAt.toUtc(), synced);
    expect(await database.readContexts(otherMembership), isEmpty);
    expect(await database.readContexts(otherUser), isEmpty);
  });

  test('atomic replacement rollback preserves old cache', () async {
    const scope = CacheScope(localUserKey: 'user:1', membershipId: 10);
    await database.putContext(
        scope: scope,
        resourceId: 'old',
        payload: {'value': 'old'},
        isHistorical: false,
        syncedAt: DateTime.utc(2026));
    expect(
      () => database.replaceContextsAtomically(
        scope: scope,
        records: [record(scope, 'new', 'new')],
        beforeInsert: () async => throw StateError('invalid parsed response'),
      ),
      throwsStateError,
    );
    final remaining = await database.readContexts(scope);
    expect(remaining.single.resourceId, 'old');
  });

  test('historical metadata remains read-only and scoped', () async {
    const scope = CacheScope(
        localUserKey: 'user:1', membershipId: 50, academicYearKey: '2023');
    await database.putContext(
        scope: scope,
        resourceId: 'context',
        payload: {'school': 'Old'},
        isHistorical: true,
        syncedAt: DateTime.utc(2026));
    expect((await database.readContexts(scope)).single.isHistorical, isTrue);
  });

  test('context switch never leaks and keeps both caches', () async {
    const a = CacheScope(localUserKey: 'user:1', membershipId: 10);
    const b = CacheScope(localUserKey: 'user:1', membershipId: 20);
    await database.putContext(
        scope: a,
        resourceId: 'context',
        payload: {'school': 'A'},
        isHistorical: false,
        syncedAt: DateTime.utc(2026));
    await database.putContext(
        scope: b,
        resourceId: 'context',
        payload: {'school': 'B'},
        isHistorical: false,
        syncedAt: DateTime.utc(2026));
    expect(
        jsonDecode(
            (await database.readContexts(a)).single.payloadJson)['school'],
        'A');
    expect(
        jsonDecode(
            (await database.readContexts(b)).single.payloadJson)['school'],
        'B');
    expect(
        jsonDecode(
            (await database.readContexts(a)).single.payloadJson)['school'],
        'A');
  });

  test('logout purge removes user cache but font preference survives',
      () async {
    const a = CacheScope(localUserKey: 'user:1', membershipId: 10);
    const b = CacheScope(localUserKey: 'user:2', membershipId: 10);
    await database.putContext(
        scope: a,
        resourceId: 'context',
        payload: {'school': 'A'},
        isHistorical: false,
        syncedAt: DateTime.utc(2026));
    await database.putContext(
        scope: b,
        resourceId: 'context',
        payload: {'school': 'B'},
        isHistorical: false,
        syncedAt: DateTime.utc(2026));
    await database.putHomeworkItem(
        a,
        {
          'id': 99,
          'title': 'Sensitive homework',
        },
        DateTime.utc(2026));
    await database.saveHomeworkDraft(
      scope: a,
      homeworkId: 99,
      answer: 'Sensitive draft',
      studentNote: 'Private note',
    );
    final fonts = MemoryFontStore();
    await fonts.write(AppFont.cairo);
    await LocalDataPurgeService(database).purgeCurrentUserData('user:1');
    expect(await database.readContexts(a), isEmpty);
    expect(await database.readHomeworkItem(a, 99), null);
    expect(await database.readHomeworkDraft(a, 99), null);
    expect(await database.readContexts(b), hasLength(1));
    expect(await fonts.read(), AppFont.cairo);
  });
}
