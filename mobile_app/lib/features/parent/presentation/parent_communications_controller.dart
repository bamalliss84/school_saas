import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../../app/app.dart';
import '../../../../core/local_database/app_database.dart';
import '../../../../core/offline/offline_error_policy.dart';
import '../data/parent_communications_repository.dart';
import '../domain/parent_communication_models.dart';

sealed class ParentNotificationsState {
  const ParentNotificationsState();
}

class ParentNotificationsLoading extends ParentNotificationsState {
  const ParentNotificationsLoading();
}

class ParentNotificationsReady extends ParentNotificationsState {
  const ParentNotificationsReady(this.data, {this.refreshing = false});
  final ParentNotificationData data;
  final bool refreshing;
}

class ParentNotificationsFailure extends ParentNotificationsState {
  const ParentNotificationsFailure(this.message);
  final String message;
}

sealed class ParentAnnouncementsState {
  const ParentAnnouncementsState();
}

class ParentAnnouncementsLoading extends ParentAnnouncementsState {
  const ParentAnnouncementsLoading();
}

class ParentAnnouncementsReady extends ParentAnnouncementsState {
  const ParentAnnouncementsReady(this.data, {this.refreshing = false});
  final ParentAnnouncementData data;
  final bool refreshing;
}

class ParentAnnouncementsFailure extends ParentAnnouncementsState {
  const ParentAnnouncementsFailure(this.message);
  final String message;
}

sealed class ParentConversationsState {
  const ParentConversationsState();
}

class ParentConversationsLoading extends ParentConversationsState {
  const ParentConversationsLoading();
}

class ParentConversationsReady extends ParentConversationsState {
  const ParentConversationsReady(
    this.data, {
    this.selected,
    this.messages = const [],
    this.detailLoading = false,
    this.busy = false,
    this.detailError,
    this.draft = '',
  });
  final ParentConversationData data;
  final ParentConversation? selected;
  final List<ParentMessage> messages;
  final bool detailLoading;
  final bool busy;
  final String? detailError;
  final String draft;

  ParentConversationsReady copyWith({
    ParentConversationData? data,
    ParentConversation? selected,
    List<ParentMessage>? messages,
    bool? detailLoading,
    bool? busy,
    String? detailError,
    bool clearError = false,
    String? draft,
  }) =>
      ParentConversationsReady(
        data ?? this.data,
        selected: selected ?? this.selected,
        messages: messages ?? this.messages,
        detailLoading: detailLoading ?? this.detailLoading,
        busy: busy ?? this.busy,
        detailError: clearError ? null : detailError ?? this.detailError,
        draft: draft ?? this.draft,
      );
}

class ParentConversationsFailure extends ParentConversationsState {
  const ParentConversationsFailure(this.message);
  final String message;
}

typedef ParentCommunicationsQuery = ({CacheScope scope, bool historical});

final parentCommunicationsRepositoryProvider = Provider(
  (ref) => ParentCommunicationsRepository(
    ref.read(apiProvider).dio,
    ref.read(databaseProvider),
  ),
);

final parentNotificationsProvider = StateNotifierProvider.autoDispose.family<
    ParentNotificationsController, ParentNotificationsState, CacheScope>(
  (ref, scope) {
    final controller = ParentNotificationsController(
      ref.read(parentCommunicationsRepositoryProvider),
      scope,
    );
    Future<void>.microtask(controller.load);
    return controller;
  },
);

final parentAnnouncementsProvider = StateNotifierProvider.autoDispose.family<
    ParentAnnouncementsController, ParentAnnouncementsState, CacheScope>(
  (ref, scope) {
    final controller = ParentAnnouncementsController(
      ref.read(parentCommunicationsRepositoryProvider),
      scope,
    );
    Future<void>.microtask(controller.load);
    return controller;
  },
);

final parentConversationsProvider = StateNotifierProvider.autoDispose.family<
    ParentConversationsController,
    ParentConversationsState,
    ParentCommunicationsQuery>(
  (ref, query) {
    final controller = ParentConversationsController(
      ref.read(parentCommunicationsRepositoryProvider),
      query.scope,
      historical: query.historical,
    );
    Future<void>.microtask(controller.load);
    return controller;
  },
);

class ParentNotificationsController
    extends StateNotifier<ParentNotificationsState> {
  ParentNotificationsController(this.repository, this.scope)
      : super(const ParentNotificationsLoading());
  final ParentCommunicationsRepository repository;
  final CacheScope scope;

  Future<void> load() async {
    final cached = await repository.readNotifications(scope);
    if (cached != null)
      state = ParentNotificationsReady(cached, refreshing: true);
    try {
      state =
          ParentNotificationsReady(await repository.loadNotifications(scope));
    } catch (error) {
      state = cached != null && isOfflineEligibleError(error)
          ? ParentNotificationsReady(cached)
          : ParentNotificationsFailure(failureMessage(
              error, 'تعذر تحميل الإشعارات. تحقق من الاتصال وحاول مجددًا.'));
    }
  }

  Future<void> refresh() async {
    try {
      state = ParentNotificationsReady(
          await repository.refreshNotifications(scope));
    } catch (error) {
      state = ParentNotificationsFailure(
          failureMessage(error, 'تعذر تحديث الإشعارات.'));
    }
  }

  Future<void> read(ParentNotification item) async {
    if (item.isRead) return;
    try {
      state = ParentNotificationsReady(
          await repository.markNotificationRead(scope, item));
    } catch (error) {
      state = ParentNotificationsFailure(
          failureMessage(error, 'تعذر تحديث حالة الإشعار.'));
    }
  }

  Future<void> readAll() async {
    try {
      state = ParentNotificationsReady(
          await repository.markAllNotificationsRead(scope));
    } catch (error) {
      state = ParentNotificationsFailure(
          failureMessage(error, 'تعذر تعليم الإشعارات كمقروءة.'));
    }
  }
}

class ParentAnnouncementsController
    extends StateNotifier<ParentAnnouncementsState> {
  ParentAnnouncementsController(this.repository, this.scope)
      : super(const ParentAnnouncementsLoading());
  final ParentCommunicationsRepository repository;
  final CacheScope scope;

  Future<void> load() async {
    final cached = await repository.readAnnouncements(scope);
    if (cached != null)
      state = ParentAnnouncementsReady(cached, refreshing: true);
    try {
      state =
          ParentAnnouncementsReady(await repository.loadAnnouncements(scope));
    } catch (error) {
      state = cached != null && isOfflineEligibleError(error)
          ? ParentAnnouncementsReady(cached)
          : ParentAnnouncementsFailure(failureMessage(
              error, 'تعذر تحميل الإعلانات. تحقق من الاتصال وحاول مجددًا.'));
    }
  }

  Future<void> refresh() async {
    try {
      state = ParentAnnouncementsReady(
          await repository.refreshAnnouncements(scope));
    } catch (error) {
      state = ParentAnnouncementsFailure(
          failureMessage(error, 'تعذر تحديث الإعلانات.'));
    }
  }

  Future<void> read(ParentAnnouncement item) async {
    if (item.isRead) return;
    try {
      state = ParentAnnouncementsReady(
          await repository.markAnnouncementRead(scope, item));
    } catch (error) {
      state = ParentAnnouncementsFailure(
          failureMessage(error, 'تعذر تحديث حالة الإعلان.'));
    }
  }

  Future<ParentConversation?> inquire(
      ParentAnnouncement item, int childId, bool historical) async {
    if (historical || !item.canInquire) return null;
    try {
      return await repository.inquireAnnouncement(item.id, childId);
    } catch (error) {
      state = ParentAnnouncementsFailure(
          failureMessage(error, 'تعذر فتح محادثة الاستفسار.'));
      return null;
    }
  }
}

class ParentConversationsController
    extends StateNotifier<ParentConversationsState> {
  ParentConversationsController(this.repository, this.scope,
      {this.historical = false})
      : super(const ParentConversationsLoading());
  final ParentCommunicationsRepository repository;
  final CacheScope scope;
  final bool historical;

  Future<void> load() async {
    final cached = await repository.readConversations(scope);
    if (cached != null) state = ParentConversationsReady(cached);
    try {
      state =
          ParentConversationsReady(await repository.loadConversations(scope));
    } catch (error) {
      state = cached != null && isOfflineEligibleError(error)
          ? ParentConversationsReady(cached)
          : ParentConversationsFailure(failureMessage(
              error, 'تعذر تحميل الرسائل. تحقق من الاتصال وحاول مجددًا.'));
    }
  }

  Future<void> refresh() async {
    try {
      state = ParentConversationsReady(
          await repository.refreshConversations(scope));
    } catch (error) {
      state = ParentConversationsFailure(
          failureMessage(error, 'تعذر تحديث الرسائل.'));
    }
  }

  Future<void> open(ParentConversation conversation) async {
    final current = state;
    if (current is! ParentConversationsReady) return;
    state = current.copyWith(
        selected: conversation,
        detailLoading: true,
        clearError: true,
        draft: '');
    try {
      final messages = await repository.loadMessages(scope, conversation.id);
      final data = conversation.unread > 0
          ? await repository.markConversationRead(scope, conversation)
          : current.data;
      state = ParentConversationsReady(
        data,
        selected: conversation.copyWith(unread: 0),
        messages: messages,
      );
    } catch (error) {
      state = current.copyWith(
        selected: conversation,
        detailLoading: false,
        detailError: failureMessage(error, 'تعذر تحميل المحادثة.'),
      );
    }
  }

  void setDraft(String value) {
    final current = state;
    if (current is ParentConversationsReady) {
      state = current.copyWith(draft: value, clearError: true);
    }
  }

  Future<void> send([String? value]) async {
    final current = state;
    if (current is! ParentConversationsReady ||
        current.busy ||
        current.selected == null ||
        historical ||
        !current.selected!.canReply) {
      return;
    }
    final body = (value ?? current.draft).trim();
    if (body.isEmpty) return;
    state = current.copyWith(busy: true, draft: body, clearError: true);
    try {
      final messages =
          await repository.sendMessage(scope, current.selected!.id, body);
      state = current.copyWith(
        messages: messages,
        busy: false,
        draft: '',
        clearError: true,
      );
    } catch (error) {
      state = current.copyWith(
        busy: false,
        draft: body,
        detailError: failureMessage(error, 'تعذر إرسال الرسالة.'),
      );
    }
  }

  Future<void> createSupport(String subject, String category) async {
    if (historical || subject.trim().isEmpty) return;
    final current = state;
    if (current is! ParentConversationsReady || current.busy) return;
    state = current.copyWith(busy: true, clearError: true);
    try {
      state = ParentConversationsReady(
          await repository.createSupport(scope, subject.trim(), category));
    } catch (error) {
      state = current.copyWith(
        busy: false,
        detailError: failureMessage(error, 'تعذر إنشاء طلب الدعم.'),
      );
    }
  }
}
