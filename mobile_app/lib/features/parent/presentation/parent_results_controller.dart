import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../../app/app.dart';
import '../../../../core/local_database/app_database.dart';
import '../../../../core/offline/offline_error_policy.dart';
import '../data/parent_results_repository.dart';

typedef ParentResultsQuery = ({CacheScope scope, int childId, int enrollmentId});

sealed class ParentResultsState {
  const ParentResultsState();
}

class ParentResultsLoading extends ParentResultsState {
  const ParentResultsLoading();
}

class ParentResultsReady extends ParentResultsState {
  const ParentResultsReady(this.data, {this.refreshing = false});
  final ParentResultsData data;
  final bool refreshing;
}

class ParentResultsFailure extends ParentResultsState {
  const ParentResultsFailure(this.message);
  final String message;
}

final parentResultsRepositoryProvider = Provider((ref) =>
    ParentResultsRepository(ref.read(apiProvider).dio, ref.read(databaseProvider)));

final parentResultsProvider = StateNotifierProvider.autoDispose
    .family<ParentResultsController, ParentResultsState, ParentResultsQuery>(
  (ref, query) {
    final controller = ParentResultsController(
      ref.read(parentResultsRepositoryProvider),
      query,
    );
    Future<void>.microtask(controller.load);
    return controller;
  },
);

class ParentResultsController extends StateNotifier<ParentResultsState> {
  ParentResultsController(this.repository, this.query)
      : super(const ParentResultsLoading());
  final ParentResultsRepository repository;
  final ParentResultsQuery query;

  Future<void> load() async {
    final cached = await repository.read(query.scope,
        childId: query.childId, enrollmentId: query.enrollmentId);
    if (cached != null) state = ParentResultsReady(cached, refreshing: true);
    try {
      state = ParentResultsReady(await repository.load(query.scope,
          childId: query.childId, enrollmentId: query.enrollmentId));
    } catch (error) {
      state = cached != null && isOfflineEligibleError(error)
          ? ParentResultsReady(cached)
          : ParentResultsFailure(failureMessage(
              error, 'تعذر تحميل النتائج. تحقق من الاتصال وحاول مجددًا.'));
    }
  }

  Future<void> refresh() async {
    final current = state;
    if (current is ParentResultsReady) {
      state = ParentResultsReady(current.data, refreshing: true);
    }
    try {
      state = ParentResultsReady(await repository.refresh(query.scope,
          childId: query.childId, enrollmentId: query.enrollmentId));
    } catch (error) {
      state = current is ParentResultsReady
          ? current
          : ParentResultsFailure(
              failureMessage(error, 'تعذر تحديث النتائج.'));
    }
  }
}
