import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../../app/app.dart';
import '../../../../core/offline/offline_error_policy.dart';
import '../data/parent_fees_repository.dart';
import '../domain/parent_fee_models.dart';
import 'parent_m2_controller.dart';

sealed class ParentFeesState {
  const ParentFeesState();
}

class ParentFeesLoading extends ParentFeesState {
  const ParentFeesLoading();
}

class ParentFeesReady extends ParentFeesState {
  const ParentFeesReady(this.data, {this.refreshing = false});
  final ParentFeesData data;
  final bool refreshing;
}

/// The guardian is not authorized for this child's financial information.
class ParentFeesNotAllowed extends ParentFeesState {
  const ParentFeesNotAllowed();
}

class ParentFeesFailure extends ParentFeesState {
  const ParentFeesFailure(this.message);
  final String message;
}

final parentFeesRepositoryProvider = Provider((ref) =>
    ParentFeesRepository(ref.read(apiProvider).dio, ref.read(databaseProvider)));

final parentFeesProvider = StateNotifierProvider.autoDispose
    .family<ParentFeesController, ParentFeesState, ParentChildQuery>(
  (ref, query) {
    final controller =
        ParentFeesController(ref.read(parentFeesRepositoryProvider), query);
    Future<void>.microtask(controller.load);
    return controller;
  },
);

class ParentFeesController extends StateNotifier<ParentFeesState> {
  ParentFeesController(this.repository, this.query)
      : super(const ParentFeesLoading());
  final ParentFeesRepository repository;
  final ParentChildQuery query;

  Future<void> load() async {
    final cached = await repository.read(query.scope, query.childId);
    if (!mounted) return;
    if (cached != null) state = ParentFeesReady(cached, refreshing: true);
    try {
      final data = await repository.load(query.scope, query.childId);
      if (mounted) state = ParentFeesReady(data);
    } on ParentFeesUnavailable {
      if (mounted) state = const ParentFeesNotAllowed();
    } catch (error) {
      if (!mounted) return;
      state = cached != null && isOfflineEligibleError(error)
          ? ParentFeesReady(cached)
          : ParentFeesFailure(failureMessage(
              error, 'تعذر تحميل الرسوم. تحقق من الاتصال وحاول مجددًا.'));
    }
  }

  Future<void> refresh() async {
    final current = state;
    if (current is ParentFeesReady) {
      state = ParentFeesReady(current.data, refreshing: true);
    }
    try {
      final data = await repository.refresh(query.scope, query.childId);
      if (mounted) state = ParentFeesReady(data);
    } on ParentFeesUnavailable {
      if (mounted) state = const ParentFeesNotAllowed();
    } catch (error) {
      if (!mounted) return;
      state = current is ParentFeesReady
          ? ParentFeesReady(current.data)
          : ParentFeesFailure(failureMessage(error, 'تعذر تحديث الرسوم.'));
    }
  }
}
