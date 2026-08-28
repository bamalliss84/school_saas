import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../core/local_database/app_database.dart';
import '../../core/offline/offline_error_policy.dart';
import 'student_profile_repository.dart';

sealed class StudentProfileState {
  const StudentProfileState();
}

class StudentProfileLoading extends StudentProfileState {
  const StudentProfileLoading();
}

class StudentProfileReady extends StudentProfileState {
  const StudentProfileReady(this.data, {this.refreshing = false});
  final StudentMoreData data;
  final bool refreshing;
}

class StudentProfileFailure extends StudentProfileState {
  const StudentProfileFailure(this.message);
  final String message;
}

class StudentProfileController extends StateNotifier<StudentProfileState> {
  StudentProfileController(this.repository, this.scope)
      : super(const StudentProfileLoading());
  final StudentProfileRepository repository;
  final CacheScope scope;
  Future<void> load() async {
    try {
      state = StudentProfileReady(await repository.load(scope));
    } catch (error) {
      state = StudentProfileFailure(
          failureMessage(error, 'تعذر تحميل بيانات الحساب'));
    }
  }

  Future<void> refresh() async {
    final current = state;
    if (current is StudentProfileReady) {
      state = StudentProfileReady(current.data, refreshing: true);
    }
    try {
      state = StudentProfileReady(await repository.refresh(scope));
    } catch (error) {
      state = current is StudentProfileReady
          ? current
          : StudentProfileFailure(
              failureMessage(error, 'تعذر تحديث بيانات الحساب'));
    }
  }
}
