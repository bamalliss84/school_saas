import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../../app/app.dart';
import '../../../../core/local_database/app_database.dart';
import '../data/teacher_communications_repository.dart';
import '../domain/teacher_communication_models.dart';

final teacherCommunicationsRepositoryProvider =
    Provider<TeacherCommunicationsDataSource>((ref) {
  return TeacherCommunicationsRepository(ref.read(apiProvider).dio);
});

final teacherNotificationsProvider = StateNotifierProvider.autoDispose.family<
    TeacherNotificationsController,
    AsyncValue<List<TeacherNotification>>,
    CacheScope>((ref, scope) {
  final controller = TeacherNotificationsController(
    ref.read(teacherCommunicationsRepositoryProvider),
  );
  Future<void>.microtask(controller.load);
  return controller;
});

class TeacherNotificationsController
    extends StateNotifier<AsyncValue<List<TeacherNotification>>> {
  TeacherNotificationsController(this.repository)
      : super(const AsyncValue.loading());
  final TeacherCommunicationsDataSource repository;

  Future<void> load() async {
    state = const AsyncValue.loading();
    state = await AsyncValue.guard(repository.notifications);
  }

  Future<void> markRead(int id) async {
    final current = state.asData?.value;
    if (current == null) return;
    final canonical = await repository.markNotificationRead(id);
    state = AsyncValue.data([
      for (final item in current) if (item.id == id) canonical else item,
    ]);
  }

  Future<int> markAllRead() async {
    final count = await repository.markAllNotificationsRead();
    final canonical = await repository.notifications();
    state = AsyncValue.data(canonical);
    return count;
  }
}

final teacherAnnouncementsProvider = StateNotifierProvider.autoDispose.family<
    TeacherAnnouncementsController,
    AsyncValue<List<TeacherAnnouncement>>,
    CacheScope>((ref, scope) {
  final controller = TeacherAnnouncementsController(
    ref.read(teacherCommunicationsRepositoryProvider),
  );
  Future<void>.microtask(controller.load);
  return controller;
});

class TeacherAnnouncementsController
    extends StateNotifier<AsyncValue<List<TeacherAnnouncement>>> {
  TeacherAnnouncementsController(this.repository)
      : super(const AsyncValue.loading());
  final TeacherCommunicationsDataSource repository;

  Future<void> load() async {
    state = const AsyncValue.loading();
    state = await AsyncValue.guard(repository.announcements);
  }

  Future<TeacherAnnouncement> markRead(int id) async {
    final item = await repository.markAnnouncementRead(id);
    _replace(item);
    return item;
  }

  Future<TeacherAnnouncement> create(TeacherAnnouncementDraft draft) async {
    final item = await repository.createAnnouncement(draft);
    final current = state.asData?.value ?? const <TeacherAnnouncement>[];
    state = AsyncValue.data([item, ...current]);
    return item;
  }

  Future<TeacherAnnouncement> update(
    int id,
    TeacherAnnouncementDraft draft,
  ) async {
    final item = await repository.updateAnnouncement(id, draft);
    _replace(item);
    return item;
  }

  Future<TeacherAnnouncement> action(int id, String action) async {
    final item = await repository.announcementAction(id, action);
    _replace(item);
    return item;
  }

  void _replace(TeacherAnnouncement item) {
    final current = state.asData?.value;
    if (current == null) return;
    state = AsyncValue.data([
      for (final row in current) if (row.id == item.id) item else row,
    ]);
  }
}

final teacherConversationsProvider = StateNotifierProvider.autoDispose.family<
    TeacherConversationsController,
    AsyncValue<List<TeacherConversation>>,
    CacheScope>((ref, scope) {
  final controller = TeacherConversationsController(
    ref.read(teacherCommunicationsRepositoryProvider),
  );
  Future<void>.microtask(controller.load);
  return controller;
});

class TeacherConversationsController
    extends StateNotifier<AsyncValue<List<TeacherConversation>>> {
  TeacherConversationsController(this.repository)
      : super(const AsyncValue.loading());
  final TeacherCommunicationsDataSource repository;

  Future<void> load() async {
    state = const AsyncValue.loading();
    state = await AsyncValue.guard(repository.conversations);
  }

  Future<TeacherConversation> start(
    TeacherStudentConversationDraft draft,
  ) async {
    final item = await repository.startStudentConversation(draft);
    final current = state.asData?.value ?? const <TeacherConversation>[];
    state = AsyncValue.data([
      item,
      ...current.where((row) => row.id != item.id),
    ]);
    return item;
  }
}

typedef TeacherMessagesQuery = ({CacheScope scope, int conversationId});

class TeacherMessagesState {
  const TeacherMessagesState({
    this.items = const [],
    this.loading = true,
    this.sending = false,
    this.failure,
  });

  final List<TeacherMessage> items;
  final bool loading;
  final bool sending;
  final Object? failure;

  TeacherMessagesState copyWith({
    List<TeacherMessage>? items,
    bool? loading,
    bool? sending,
    Object? failure,
    bool clearFailure = false,
  }) =>
      TeacherMessagesState(
        items: items ?? this.items,
        loading: loading ?? this.loading,
        sending: sending ?? this.sending,
        failure: clearFailure ? null : failure ?? this.failure,
      );
}

final teacherMessagesProvider = StateNotifierProvider.autoDispose.family<
    TeacherMessagesController, TeacherMessagesState, TeacherMessagesQuery>(
  (ref, query) {
    final controller = TeacherMessagesController(
      ref.read(teacherCommunicationsRepositoryProvider),
      query.conversationId,
    );
    Future<void>.microtask(controller.load);
    return controller;
  },
);

class TeacherMessagesController extends StateNotifier<TeacherMessagesState> {
  TeacherMessagesController(this.repository, this.conversationId)
      : super(const TeacherMessagesState());

  final TeacherCommunicationsDataSource repository;
  final int conversationId;

  Future<void> load() async {
    state = state.copyWith(loading: true, clearFailure: true);
    try {
      final items = await repository.messages(conversationId);
      state = state.copyWith(items: items, loading: false, clearFailure: true);
      try {
        await repository.markConversationRead(conversationId);
      } catch (error) {
        state = state.copyWith(failure: error);
      }
    } catch (error) {
      state = state.copyWith(loading: false, failure: error);
    }
  }

  Future<bool> send(String body) async {
    final clean = body.trim();
    if (clean.isEmpty || state.sending) return false;
    state = state.copyWith(sending: true, clearFailure: true);
    try {
      final sent = await repository.sendMessage(conversationId, clean);
      final appended = [
        ...state.items.where((item) => item.id != sent.id),
        sent,
      ]..sort((a, b) {
          final byDate = a.createdAt.compareTo(b.createdAt);
          return byDate != 0 ? byDate : a.id.compareTo(b.id);
        });
      state = state.copyWith(items: appended, sending: false);
      try {
        final canonical = await repository.messages(conversationId);
        state = state.copyWith(items: canonical, clearFailure: true);
      } catch (error) {
        state = state.copyWith(failure: error);
      }
      return true;
    } catch (error) {
      state = state.copyWith(sending: false, failure: error);
      return false;
    }
  }
}
