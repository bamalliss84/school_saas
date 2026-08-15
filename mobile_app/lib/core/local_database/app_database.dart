import 'dart:convert';

import 'package:drift/drift.dart';
import 'package:drift_flutter/drift_flutter.dart';

part 'app_database.g.dart';

class CachedContexts extends Table {
  TextColumn get localUserKey => text()();
  IntColumn get membershipId => integer()();
  TextColumn get academicYearKey => text().withDefault(const Constant(''))();
  TextColumn get resourceId => text()();
  TextColumn get payloadJson => text()();
  BoolColumn get isHistorical => boolean().withDefault(const Constant(false))();
  DateTimeColumn get cachedAt => dateTime()();
  DateTimeColumn get lastSyncedAt => dateTime()();

  @override
  Set<Column<Object>> get primaryKey =>
      {localUserKey, membershipId, academicYearKey, resourceId};
}

class CacheMetadata extends Table {
  TextColumn get localUserKey => text()();
  IntColumn get membershipId => integer()();
  TextColumn get academicYearKey => text().withDefault(const Constant(''))();
  TextColumn get resourceType => text()();
  DateTimeColumn get cachedAt => dateTime()();
  DateTimeColumn get lastSyncedAt => dateTime()();

  @override
  Set<Column<Object>> get primaryKey =>
      {localUserKey, membershipId, academicYearKey, resourceType};
}

class CachedTimetableDatasets extends Table {
  TextColumn get localUserKey => text()();
  IntColumn get membershipId => integer()();
  TextColumn get academicYearKey => text()();
  TextColumn get datasetKey => text()();
  TextColumn get payloadJson => text()();
  DateTimeColumn get lastSyncedAt => dateTime()();

  @override
  Set<Column<Object>> get primaryKey =>
      {localUserKey, membershipId, academicYearKey, datasetKey};
}

class CachedHomeworkItems extends Table {
  TextColumn get localUserKey => text()();
  IntColumn get membershipId => integer()();
  TextColumn get academicYearKey => text()();
  IntColumn get homeworkId => integer()();
  TextColumn get payloadJson => text()();
  DateTimeColumn get lastSyncedAt => dateTime()();

  @override
  Set<Column<Object>> get primaryKey =>
      {localUserKey, membershipId, academicYearKey, homeworkId};
}

class LocalHomeworkDrafts extends Table {
  TextColumn get localUserKey => text()();
  IntColumn get membershipId => integer()();
  TextColumn get academicYearKey => text()();
  IntColumn get homeworkId => integer()();
  TextColumn get answer => text().withDefault(const Constant(''))();
  TextColumn get studentNote => text().withDefault(const Constant(''))();
  TextColumn get localFilesJson => text().withDefault(const Constant('[]'))();
  DateTimeColumn get updatedAt => dateTime()();

  @override
  Set<Column<Object>> get primaryKey =>
      {localUserKey, membershipId, academicYearKey, homeworkId};
}

class CacheScope {
  const CacheScope({
    required this.localUserKey,
    required this.membershipId,
    this.academicYearKey = '',
  });

  final String localUserKey;
  final int membershipId;
  final String academicYearKey;

  @override
  bool operator ==(Object other) =>
      other is CacheScope &&
      other.localUserKey == localUserKey &&
      other.membershipId == membershipId &&
      other.academicYearKey == academicYearKey;
  @override
  int get hashCode => Object.hash(localUserKey, membershipId, academicYearKey);
}

@DriftDatabase(tables: [
  CachedContexts,
  CacheMetadata,
  CachedTimetableDatasets,
  CachedHomeworkItems,
  LocalHomeworkDrafts,
])
class AppDatabase extends _$AppDatabase {
  AppDatabase() : super(_openConnection());
  AppDatabase.forTesting(super.executor);

  @override
  int get schemaVersion => 3;

  @override
  MigrationStrategy get migration => MigrationStrategy(
        onCreate: (migrator) => migrator.createAll(),
        onUpgrade: (migrator, from, to) async {
          if (from < 2) await migrator.createTable(cachedTimetableDatasets);
          if (from < 3) {
            await migrator.createTable(cachedHomeworkItems);
            await migrator.createTable(localHomeworkDrafts);
          }
        },
      );

  static QueryExecutor _openConnection() =>
      driftDatabase(name: 'school_saas_mobile_cache');

  Future<void> putContext({
    required CacheScope scope,
    required String resourceId,
    required Map<String, Object?> payload,
    required bool isHistorical,
    required DateTime syncedAt,
  }) =>
      into(cachedContexts)
          .insertOnConflictUpdate(CachedContextsCompanion.insert(
        localUserKey: scope.localUserKey,
        membershipId: scope.membershipId,
        academicYearKey: Value(scope.academicYearKey),
        resourceId: resourceId,
        payloadJson: jsonEncode(payload),
        isHistorical: Value(isHistorical),
        cachedAt: syncedAt,
        lastSyncedAt: syncedAt,
      ));

  Future<List<CachedContext>> readContexts(CacheScope scope) =>
      (select(cachedContexts)
            ..where((row) =>
                row.localUserKey.equals(scope.localUserKey) &
                row.membershipId.equals(scope.membershipId) &
                row.academicYearKey.equals(scope.academicYearKey)))
          .get();

  Stream<List<CachedContext>> watchContexts(CacheScope scope) =>
      (select(cachedContexts)
            ..where((row) =>
                row.localUserKey.equals(scope.localUserKey) &
                row.membershipId.equals(scope.membershipId) &
                row.academicYearKey.equals(scope.academicYearKey)))
          .watch();

  Future<void> replaceContextsAtomically({
    required CacheScope scope,
    required List<CachedContextsCompanion> records,
    Future<void> Function()? beforeInsert,
  }) =>
      transaction(() async {
        await (delete(cachedContexts)
              ..where((row) =>
                  row.localUserKey.equals(scope.localUserKey) &
                  row.membershipId.equals(scope.membershipId) &
                  row.academicYearKey.equals(scope.academicYearKey)))
            .go();
        if (beforeInsert != null) await beforeInsert();
        await batch((batch) => batch.insertAll(cachedContexts, records));
      });

  Future<void> invalidateMembership(CacheScope scope) => (delete(cachedContexts)
        ..where((row) =>
            row.localUserKey.equals(scope.localUserKey) &
            row.membershipId.equals(scope.membershipId)))
      .go();

  Future<CachedTimetableDataset?> readTimetableDataset(
          CacheScope scope, String datasetKey) =>
      (select(cachedTimetableDatasets)
            ..where((row) =>
                row.localUserKey.equals(scope.localUserKey) &
                row.membershipId.equals(scope.membershipId) &
                row.academicYearKey.equals(scope.academicYearKey) &
                row.datasetKey.equals(datasetKey)))
          .getSingleOrNull();

  Future<void> replaceTimetableDatasets(CacheScope scope,
          Map<String, Map<String, Object?>> payloads, DateTime syncedAt) =>
      transaction(() async {
        for (final item in payloads.entries) {
          await into(cachedTimetableDatasets).insertOnConflictUpdate(
            CachedTimetableDatasetsCompanion.insert(
              localUserKey: scope.localUserKey,
              membershipId: scope.membershipId,
              academicYearKey: scope.academicYearKey,
              datasetKey: item.key,
              payloadJson: jsonEncode(item.value),
              lastSyncedAt: syncedAt,
            ),
          );
        }
      });

  Future<List<CachedHomeworkItem>> readHomeworkItems(CacheScope scope) =>
      (select(cachedHomeworkItems)
            ..where((row) =>
                row.localUserKey.equals(scope.localUserKey) &
                row.membershipId.equals(scope.membershipId) &
                row.academicYearKey.equals(scope.academicYearKey))
            ..orderBy([(row) => OrderingTerm.desc(row.lastSyncedAt)]))
          .get();

  Future<CachedHomeworkItem?> readHomeworkItem(
          CacheScope scope, int homeworkId) =>
      (select(cachedHomeworkItems)
            ..where((row) =>
                row.localUserKey.equals(scope.localUserKey) &
                row.membershipId.equals(scope.membershipId) &
                row.academicYearKey.equals(scope.academicYearKey) &
                row.homeworkId.equals(homeworkId)))
          .getSingleOrNull();

  Future<void> replaceHomeworkItems(CacheScope scope,
          List<Map<String, Object?>> payloads, DateTime syncedAt) =>
      transaction(() async {
        await (delete(cachedHomeworkItems)
              ..where((row) =>
                  row.localUserKey.equals(scope.localUserKey) &
                  row.membershipId.equals(scope.membershipId) &
                  row.academicYearKey.equals(scope.academicYearKey)))
            .go();
        await batch((batch) => batch.insertAll(
              cachedHomeworkItems,
              payloads
                  .map((payload) => CachedHomeworkItemsCompanion.insert(
                        localUserKey: scope.localUserKey,
                        membershipId: scope.membershipId,
                        academicYearKey: scope.academicYearKey,
                        homeworkId: payload['id']! as int,
                        payloadJson: jsonEncode(payload),
                        lastSyncedAt: syncedAt,
                      ))
                  .toList(),
            ));
      });

  Future<void> putHomeworkItem(
          CacheScope scope, Map<String, Object?> payload, DateTime syncedAt) =>
      into(cachedHomeworkItems).insertOnConflictUpdate(
        CachedHomeworkItemsCompanion.insert(
          localUserKey: scope.localUserKey,
          membershipId: scope.membershipId,
          academicYearKey: scope.academicYearKey,
          homeworkId: payload['id']! as int,
          payloadJson: jsonEncode(payload),
          lastSyncedAt: syncedAt,
        ),
      );

  Future<LocalHomeworkDraft?> readHomeworkDraft(
          CacheScope scope, int homeworkId) =>
      (select(localHomeworkDrafts)
            ..where((row) =>
                row.localUserKey.equals(scope.localUserKey) &
                row.membershipId.equals(scope.membershipId) &
                row.academicYearKey.equals(scope.academicYearKey) &
                row.homeworkId.equals(homeworkId)))
          .getSingleOrNull();

  Future<void> saveHomeworkDraft({
    required CacheScope scope,
    required int homeworkId,
    required String answer,
    required String studentNote,
    List<String> localFiles = const [],
  }) =>
      into(localHomeworkDrafts).insertOnConflictUpdate(
        LocalHomeworkDraftsCompanion.insert(
          localUserKey: scope.localUserKey,
          membershipId: scope.membershipId,
          academicYearKey: scope.academicYearKey,
          homeworkId: homeworkId,
          answer: Value(answer),
          studentNote: Value(studentNote),
          localFilesJson: Value(jsonEncode(localFiles)),
          updatedAt: DateTime.now().toUtc(),
        ),
      );

  Future<void> deleteHomeworkDraft(CacheScope scope, int homeworkId) =>
      (delete(localHomeworkDrafts)
            ..where((row) =>
                row.localUserKey.equals(scope.localUserKey) &
                row.membershipId.equals(scope.membershipId) &
                row.academicYearKey.equals(scope.academicYearKey) &
                row.homeworkId.equals(homeworkId)))
          .go();

  Future<void> purgeUser(String localUserKey) => transaction(() async {
        await (delete(cachedContexts)
              ..where((row) => row.localUserKey.equals(localUserKey)))
            .go();
        await (delete(cacheMetadata)
              ..where((row) => row.localUserKey.equals(localUserKey)))
            .go();
        await (delete(cachedTimetableDatasets)
              ..where((row) => row.localUserKey.equals(localUserKey)))
            .go();
        await (delete(cachedHomeworkItems)
              ..where((row) => row.localUserKey.equals(localUserKey)))
            .go();
        await (delete(localHomeworkDrafts)
              ..where((row) => row.localUserKey.equals(localUserKey)))
            .go();
      });
}
