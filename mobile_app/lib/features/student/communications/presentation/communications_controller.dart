import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:file_selector/file_selector.dart';
import '../../../../core/local_database/app_database.dart';
import '../../../../core/offline/offline_error_policy.dart';
import '../data/communications_repository.dart';
import '../domain/communication_models.dart';

sealed class CommunicationsState {
  const CommunicationsState();
}

class CommunicationsLoading extends CommunicationsState {
  const CommunicationsLoading();
}

class CommunicationsFailure extends CommunicationsState {
  const CommunicationsFailure(this.message);
  final String message;
}

class CommunicationsReady extends CommunicationsState {
  const CommunicationsReady(this.data,
      {this.selectedConversation,
      this.messages = const [],
      this.busy = false,
      this.detailError});
  final CommunicationsSnapshot data;
  final ConversationSummary? selectedConversation;
  final List<ConversationMessage> messages;
  final bool busy;
  final String? detailError;
  CommunicationsReady copyWith(
          {CommunicationsSnapshot? data,
          ConversationSummary? selectedConversation,
          List<ConversationMessage>? messages,
          bool? busy,
          bool clearConversation = false,
          String? detailError,
          bool clearError = false}) =>
      CommunicationsReady(data ?? this.data,
          selectedConversation: clearConversation
              ? null
              : (selectedConversation ?? this.selectedConversation),
          messages: messages ?? this.messages,
          busy: busy ?? this.busy,
          detailError: clearError ? null : (detailError ?? this.detailError));
}

class CommunicationsController extends StateNotifier<CommunicationsState> {
  CommunicationsController(this.repo, this.scope)
      : super(const CommunicationsLoading());
  final StudentCommunicationsRepository repo;
  final CacheScope scope;
  Future<void> load() async {
    final cached = await repo.read(scope);
    if (cached != null) {
      state = CommunicationsReady(cached);
    }
    try {
      final fresh = await repo.refresh(scope);
      final current = state;
      state = current is CommunicationsReady
          ? current.copyWith(data: fresh)
          : CommunicationsReady(fresh);
    } catch (e) {
      if (cached == null || !isOfflineEligibleError(e)) {
        state = CommunicationsFailure(
            failureMessage(e, 'تعذر تحميل بيانات التواصل'));
      }
    }
  }

  Future<void> refresh() async {
    try {
      state = CommunicationsReady(await repo.refresh(scope));
    } catch (e) {
      if (state is! CommunicationsReady) {
        state = CommunicationsFailure(
            failureMessage(e, 'تعذر تحديث بيانات التواصل'));
      }
    }
  }

  Future<void> readNotification(int id) async {
    await repo.markNotificationRead(id);
    await refresh();
  }

  Future<void> readAll() async {
    await repo.markAllNotificationsRead();
    await refresh();
  }

  Future<void> readAnnouncement(int id) async {
    await repo.markAnnouncementRead(id);
    await refresh();
  }

  Future<void> openConversation(ConversationSummary c) async {
    final current = state;
    if (current is! CommunicationsReady) {
      return;
    }
    state =
        current.copyWith(selectedConversation: c, busy: true, clearError: true);
    try {
      final rows = await repo.messages(scope, c.id);
      try {
        await repo.markConversationRead(c.id);
      } catch (_) {
        /* Personal read marker must never hide readable cached history. */
      }
      state = current.copyWith(
          selectedConversation: c,
          messages: rows,
          busy: false,
          clearError: true);
    } catch (e) {
      state = current.copyWith(
          selectedConversation: c,
          messages: const [],
          busy: false,
          detailError: failureMessage(e, 'تعذر تحميل الرسائل'));
    }
  }

  void closeConversation() {
    final s = state;
    if (s is CommunicationsReady) {
      state = s.copyWith(clearConversation: true, messages: const []);
    }
  }

  Future<void> send(String body, [List<XFile> attachments = const []]) async {
    final s = state;
    if (s is! CommunicationsReady ||
        s.selectedConversation == null ||
        body.trim().isEmpty) {
      return;
    }
    if (s.selectedConversation!.isSchoolSupport) {
      final messageId =
          await repo.replySupport(s.selectedConversation!.id, body.trim());
      await repo.uploadAttachments(messageId, attachments);
    } else {
      final messageId =
          await repo.sendMessage(s.selectedConversation!.id, body.trim());
      await repo.uploadAttachments(messageId, attachments);
    }
    await openConversation(s.selectedConversation!);
  }

  Future<int> inquire(int announcementId) async {
    final id = await repo.inquireAnnouncement(announcementId);
    if (id == null) throw StateError('لم يُرجع الخادم محادثة الاستفسار');
    await refresh();
    return id;
  }

  Future<bool> createSupport(String category, String subject, String message,
      [List<XFile> attachments = const []]) async {
    final item = await repo.createSupport(
        category: category, subject: subject, message: message);
    var attachmentsUploaded = true;
    if (attachments.isNotEmpty) {
      try {
        final messages = await repo.messages(scope, item.id);
        final initial = messages.where((row) => row.senderRole == 'student');
        if (initial.isEmpty) {
          attachmentsUploaded = false;
        } else {
          await repo.uploadAttachments(initial.last.id, attachments);
        }
      } catch (_) {
        attachmentsUploaded = false;
      }
    }
    await refresh();
    await openConversation(item);
    return attachmentsUploaded;
  }
}
