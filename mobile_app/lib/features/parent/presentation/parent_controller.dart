import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../../app/app.dart';
import '../../../../core/local_database/app_database.dart';
import '../../../../core/offline/offline_error_policy.dart';
import '../data/parent_repository.dart';
import '../domain/parent_models.dart';

sealed class ParentState {
  const ParentState();
}

class ParentLoading extends ParentState {
  const ParentLoading();
}

class ParentReady extends ParentState {
  const ParentReady(this.data, {this.refreshing = false});
  final ParentFoundationData data;
  final bool refreshing;
}

class ParentFailure extends ParentState {
  const ParentFailure(this.message);
  final String message;
}

final parentRepositoryProvider = Provider<ParentFoundationDataSource>((ref) {
  return ParentRepository(
    ref.read(apiProvider).dio,
    ref.read(databaseProvider),
  );
});

final parentFoundationProvider = StateNotifierProvider.autoDispose
    .family<ParentController, ParentState, CacheScope>((ref, scope) {
  final controller =
      ParentController(ref.read(parentRepositoryProvider), scope);
  Future<void>.microtask(controller.load);
  return controller;
});

class ParentController extends StateNotifier<ParentState> {
  ParentController(this.repository, this.scope) : super(const ParentLoading());
  final ParentFoundationDataSource repository;
  final CacheScope scope;

  Future<void> load() async {
    try {
      state = ParentReady(await repository.load(scope));
    } catch (error) {
      state = ParentFailure(failureMessage(error, 'تعذر تحميل بيانات الأبناء'));
    }
  }

  Future<void> refresh() async {
    final current = state;
    if (current is ParentReady) {
      state = ParentReady(current.data, refreshing: true);
    }
    try {
      state = ParentReady(await repository.refresh(scope));
    } catch (error) {
      state = current is ParentReady
          ? current
          : ParentFailure(failureMessage(error, 'تعذر تحديث بيانات الأبناء'));
    }
  }

  Future<void> selectChild(int childId) async {
    final current = state;
    if (current is! ParentReady || current.data.selectedChildId == childId) {
      return;
    }
    state = ParentReady(current.data, refreshing: true);
    try {
      state = ParentReady(await repository.selectChild(scope, childId));
    } catch (error) {
      state = current;
      rethrow;
    }
  }
}
