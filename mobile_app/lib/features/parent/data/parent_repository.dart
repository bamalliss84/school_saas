import 'dart:convert';

import 'package:dio/dio.dart';

import '../../../../core/local_database/app_database.dart';
import '../../../../core/offline/offline_error_policy.dart';
import '../domain/parent_models.dart';

abstract interface class ParentFoundationDataSource {
  Future<ParentFoundationData> load(CacheScope scope);
  Future<ParentFoundationData> refresh(CacheScope scope);
  Future<ParentFoundationData> selectChild(CacheScope scope, int childId);
}

class ParentRepository implements ParentFoundationDataSource {
  ParentRepository(this.dio, this.database);
  final Dio dio;
  final AppDatabase database;

  static const resourceId = 'parent_foundation_v1';

  Future<ParentFoundationData?> read(CacheScope scope) async {
    final rows = await database.readContexts(scope);
    for (final row in rows) {
      if (row.resourceId == resourceId) {
        return ParentFoundationData.fromJson(
          Map<String, dynamic>.from(jsonDecode(row.payloadJson) as Map),
          row.lastSyncedAt,
          offline: true,
        );
      }
    }
    return null;
  }

  @override
  Future<ParentFoundationData> load(CacheScope scope) async {
    final cached = await read(scope);
    try {
      return await refresh(scope);
    } catch (error) {
      if (cached != null && isOfflineEligibleError(error)) return cached;
      rethrow;
    }
  }

  @override
  Future<ParentFoundationData> refresh(CacheScope scope) async {
    final cached = await read(scope);
    final response = await dio.get<dynamic>('parents/me/children/');
    final children =
        _rows(response.data).map(ParentChild.fromJson).toList(growable: false);
    final ids = children.map((item) => item.id).toSet();
    final selected = ids.contains(cached?.selectedChildId)
        ? cached!.selectedChildId
        : (children.isEmpty ? null : children.first.id);
    final histories = <int, List<ParentEnrollment>>{
      for (final entry in (cached?.histories ?? const {}).entries)
        if (ids.contains(entry.key)) entry.key: entry.value,
    };
    if (selected != null) {
      histories[selected] = await _history(scope, selected);
    }
    return _persist(
      scope,
      ParentFoundationData(
        children: children,
        selectedChildId: selected,
        histories: histories,
        lastUpdated: DateTime.now().toUtc(),
      ),
    );
  }

  @override
  Future<ParentFoundationData> selectChild(
    CacheScope scope,
    int childId,
  ) async {
    final cached = await read(scope);
    if (cached == null || !cached.children.any((item) => item.id == childId)) {
      throw StateError('Child is not available in the active parent context.');
    }
    try {
      final history = await _history(scope, childId);
      return _persist(
        scope,
        cached.copyWith(
          selectedChildId: childId,
          histories: {...cached.histories, childId: history},
          lastUpdated: DateTime.now().toUtc(),
          offline: false,
        ),
      );
    } catch (error) {
      if (isOfflineEligibleError(error) &&
          cached.histories.containsKey(childId)) {
        return _persist(
          scope,
          cached.copyWith(selectedChildId: childId, offline: true),
        );
      }
      rethrow;
    }
  }

  Future<List<ParentEnrollment>> _history(
    CacheScope scope,
    int childId,
  ) async {
    final academicYearId = int.tryParse(scope.academicYearKey);
    final response = await dio.get<dynamic>(
      'parents/me/children/$childId/academic-history/',
      queryParameters: {
        'school_membership_id': scope.membershipId,
        if (academicYearId != null) 'academic_year_id': academicYearId,
      },
    );
    return _rows(response.data)
        .map(ParentEnrollment.fromJson)
        .toList(growable: false);
  }

  Future<ParentFoundationData> _persist(
    CacheScope scope,
    ParentFoundationData data,
  ) async {
    await database.putContext(
      scope: scope,
      resourceId: resourceId,
      payload: data.toJson(),
      isHistorical: false,
      syncedAt: data.lastUpdated,
    );
    return data;
  }
}

List<Map<String, dynamic>> _rows(Object? payload) {
  final raw = payload is Map ? payload['results'] : payload;
  return (raw as List? ?? const [])
      .whereType<Map>()
      .map((item) => Map<String, dynamic>.from(item))
      .toList(growable: false);
}
