import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../../app/app.dart';
import '../../../../core/local_database/app_database.dart';
import '../../../../core/offline/offline_error_policy.dart';
import '../data/parent_homework_repository.dart';
import '../domain/parent_homework_models.dart';

typedef ParentHomeworkQuery = ({CacheScope scope, int childId});
typedef ParentHomeworkDetailQuery = ({
  CacheScope scope,
  int childId,
  ParentHomework homework,
});

sealed class ParentHomeworkState {
  const ParentHomeworkState();
}

class ParentHomeworkLoading extends ParentHomeworkState {
  const ParentHomeworkLoading();
}

class ParentHomeworkReady extends ParentHomeworkState {
  const ParentHomeworkReady(this.data, {this.refreshing = false});
  final ParentHomeworkListData data;
  final bool refreshing;
}

class ParentHomeworkFailure extends ParentHomeworkState {
  const ParentHomeworkFailure(this.message);
  final String message;
}

sealed class ParentHomeworkDetailState {
  const ParentHomeworkDetailState();
}

class ParentHomeworkDetailLoading extends ParentHomeworkDetailState {
  const ParentHomeworkDetailLoading();
}

class ParentHomeworkDetailReady extends ParentHomeworkDetailState {
  const ParentHomeworkDetailReady(this.data, {this.refreshing = false});
  final ParentHomeworkDetailData data;
  final bool refreshing;
}

class ParentHomeworkDetailFailure extends ParentHomeworkDetailState {
  const ParentHomeworkDetailFailure(this.message);
  final String message;
}

final parentHomeworkRepositoryProvider = Provider((ref) =>
    ParentHomeworkRepository(
        ref.read(apiProvider).dio, ref.read(databaseProvider)));

final parentHomeworkProvider = StateNotifierProvider.autoDispose
    .family<ParentHomeworkController, ParentHomeworkState, ParentHomeworkQuery>(
  (ref, query) {
    final controller = ParentHomeworkController(
      ref.read(parentHomeworkRepositoryProvider),
      query,
    );
    Future<void>.microtask(controller.load);
    return controller;
  },
);

final parentHomeworkDetailProvider = StateNotifierProvider.autoDispose.family<
    ParentHomeworkDetailController,
    ParentHomeworkDetailState,
    ParentHomeworkDetailQuery>(
  (ref, query) {
    final controller = ParentHomeworkDetailController(
      ref.read(parentHomeworkRepositoryProvider),
      query,
    );
    Future<void>.microtask(controller.load);
    return controller;
  },
);

class ParentHomeworkController extends StateNotifier<ParentHomeworkState> {
  ParentHomeworkController(this.repository, this.query)
      : super(const ParentHomeworkLoading());
  final ParentHomeworkRepository repository;
  final ParentHomeworkQuery query;

  Future<void> load() async {
    final cached = await repository.readList(query.scope, query.childId);
    if (cached != null) state = ParentHomeworkReady(cached, refreshing: true);
    try {
      state = ParentHomeworkReady(
          await repository.loadList(query.scope, query.childId));
    } catch (error) {
      state = cached != null && isOfflineEligibleError(error)
          ? ParentHomeworkReady(cached)
          : ParentHomeworkFailure(failureMessage(
              error, 'تعذر تحميل الواجبات. تحقق من الاتصال وحاول مجددًا.'));
    }
  }

  Future<void> refresh() async {
    final current = state;
    if (current is ParentHomeworkReady) {
      state = ParentHomeworkReady(current.data, refreshing: true);
    }
    try {
      state = ParentHomeworkReady(
          await repository.refreshList(query.scope, query.childId));
    } catch (error) {
      state = current is ParentHomeworkReady
          ? current
          : ParentHomeworkFailure(
              failureMessage(error, 'تعذر تحديث الواجبات.'));
    }
  }
}

class ParentHomeworkDetailController
    extends StateNotifier<ParentHomeworkDetailState> {
  ParentHomeworkDetailController(this.repository, this.query)
      : super(const ParentHomeworkDetailLoading());
  final ParentHomeworkRepository repository;
  final ParentHomeworkDetailQuery query;

  Future<void> load() async {
    final cached = await repository.readDetail(
        query.scope, query.childId, query.homework.id);
    if (cached != null) {
      state = ParentHomeworkDetailReady(cached, refreshing: true);
    }
    try {
      state = ParentHomeworkDetailReady(await repository.loadDetail(
          query.scope, query.childId, query.homework));
    } catch (error) {
      state = cached != null && isOfflineEligibleError(error)
          ? ParentHomeworkDetailReady(cached)
          : ParentHomeworkDetailFailure(
              failureMessage(error, 'تعذر تحميل تفاصيل الواجب.'));
    }
  }

  Future<void> refresh() async {
    final current = state;
    if (current is ParentHomeworkDetailReady) {
      state = ParentHomeworkDetailReady(current.data, refreshing: true);
    }
    try {
      state = ParentHomeworkDetailReady(await repository.refreshDetail(
          query.scope, query.childId, query.homework));
    } catch (error) {
      state = current is ParentHomeworkDetailReady
          ? current
          : ParentHomeworkDetailFailure(
              failureMessage(error, 'تعذر تحديث تفاصيل الواجب.'));
    }
  }
}
