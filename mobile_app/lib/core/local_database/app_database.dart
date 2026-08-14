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

@DriftDatabase(tables: [CachedContexts, CacheMetadata, CachedTimetableDatasets])
class AppDatabase extends _$AppDatabase {
  AppDatabase() : super(_openConnection());
  AppDatabase.forTesting(super.executor);

  @override
  int get schemaVersion => 2;

  @override
  MigrationStrategy get migration => MigrationStrategy(
        onCreate: (migrator) => migrator.createAll(),
        onUpgrade: (migrator, from, to) async {
          if (from < 2) await migrator.createTable(cachedTimetableDatasets);
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
      });
}
