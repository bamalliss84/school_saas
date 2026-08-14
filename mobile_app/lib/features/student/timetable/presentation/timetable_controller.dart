import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../../core/local_database/app_database.dart';
import '../data/timetable_repository.dart';

sealed class TimetableState {
  const TimetableState();
}

class TimetableLoading extends TimetableState {
  const TimetableLoading();
}

class TimetableReady extends TimetableState {
  const TimetableReady(this.data,
      {this.offline = false, this.refreshing = false});
  final StudentTimetableData data;
  final bool offline;
  final bool refreshing;
}

class TimetableFailure extends TimetableState {
  const TimetableFailure(this.message);
  final String message;
}

class TimetableController extends StateNotifier<TimetableState> {
  TimetableController(this.repository, this.scope)
      : super(const TimetableLoading());
  final StudentTimetableRepository repository;
  final CacheScope scope;
  Future<void> load() async {
    final cached = await repository.readCache(scope);
    if (cached != null) {
      state = TimetableReady(cached, refreshing: true);
    }
    try {
      state = TimetableReady(await repository.refresh(scope));
    } catch (_) {
      if (cached != null) {
        state = TimetableReady(cached, offline: true);
      } else {
        state = const TimetableFailure(
            'تعذر تحميل الجدول. تحقق من الاتصال وحاول مجددًا.');
      }
    }
  }

  Future<void> refresh() => load();
}
