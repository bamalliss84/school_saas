import 'dart:convert';

import 'package:dio/dio.dart';

import '../../../../core/local_database/app_database.dart';
import '../../../../core/offline/offline_error_policy.dart';
import '../domain/parent_communication_models.dart';

class ParentNotificationData {
  const ParentNotificationData(this.items, this.lastUpdated,
      {this.offline = false});
  final List<ParentNotification> items;
  final DateTime lastUpdated;
  final bool offline;
  int get unreadCount => items.where((item) => !item.isRead).length;
}

class ParentAnnouncementData {
  const ParentAnnouncementData(this.items, this.lastUpdated,
      {this.offline = false});
  final List<ParentAnnouncement> items;
  final DateTime lastUpdated;
  final bool offline;
}

class ParentConversationData {
  const ParentConversationData(this.items, this.lastUpdated,
      {this.offline = false});
  final List<ParentConversation> items;
  final DateTime lastUpdated;
  final bool offline;
}

class ParentCommunicationsRepository {
  ParentCommunicationsRepository(this.dio, this.database);
  final Dio dio;
  final AppDatabase database;

  static const _notificationsKey = 'parent_notifications_v1';
  static const _announcementsKey = 'parent_announcements_v1';
  static const _conversationsKey = 'parent_conversations_v1';
  String _messagesKey(int id) => 'parent_conversation_messages_v1_$id';

  Future<ParentNotificationData?> readNotifications(CacheScope scope) async {
    final row = await _read(scope, _notificationsKey);
    if (row == null) return null;
    return ParentNotificationData(
      _cachedRows(row).map(ParentNotification.fromJson).toList(),
      row.lastSyncedAt,
      offline: true,
    );
  }

  Future<ParentNotificationData> refreshNotifications(CacheScope scope) async {
    final response = await dio.get<dynamic>('notifications/');
    final items = _rows(response.data);
    return _saveNotifications(
        scope, items.map(ParentNotification.fromJson).toList());
  }

  Future<ParentNotificationData> loadNotifications(CacheScope scope) async {
    final cached = await readNotifications(scope);
    try {
      return await refreshNotifications(scope);
    } catch (error) {
      if (cached != null && isOfflineEligibleError(error)) return cached;
      rethrow;
    }
  }

  Future<ParentNotificationData> markNotificationRead(
      CacheScope scope, ParentNotification item) async {
    final response = await dio.post<dynamic>('notifications/${item.id}/read/');
    final canonical = ParentNotification.fromJson(
        Map<String, dynamic>.from(response.data as Map));
    final current = await readNotifications(scope);
    final rows = [...?current?.items];
    final index = rows.indexWhere((row) => row.id == canonical.id);
    if (index >= 0) rows[index] = canonical;
    return _saveNotifications(scope, rows);
  }

  Future<ParentNotificationData> markAllNotificationsRead(
      CacheScope scope) async {
    await dio.post<dynamic>('notifications/read-all/');
    final current = await readNotifications(scope);
    final now = DateTime.now().toUtc();
    return _saveNotifications(
      scope,
      [...?current?.items]
          .map((item) => item.copyWith(isRead: true, readAt: now))
          .toList(),
    );
  }

  Future<ParentNotificationData> _saveNotifications(
      CacheScope scope, List<ParentNotification> items) async {
    final now = DateTime.now().toUtc();
    await _write(scope, _notificationsKey,
        items.map((item) => item.toJson()).toList(), now);
    return ParentNotificationData(items, now);
  }

  Future<ParentAnnouncementData?> readAnnouncements(CacheScope scope) async {
    final row = await _read(scope, _announcementsKey);
    if (row == null) return null;
    return ParentAnnouncementData(
      _cachedRows(row).map(ParentAnnouncement.fromJson).toList(),
      row.lastSyncedAt,
      offline: true,
    );
  }

  Future<ParentAnnouncementData> refreshAnnouncements(CacheScope scope) async {
    final response = await dio.get<dynamic>('announcements/');
    return _saveAnnouncements(
        scope, _rows(response.data).map(ParentAnnouncement.fromJson).toList());
  }

  Future<ParentAnnouncementData> loadAnnouncements(CacheScope scope) async {
    final cached = await readAnnouncements(scope);
    try {
      return await refreshAnnouncements(scope);
    } catch (error) {
      if (cached != null && isOfflineEligibleError(error)) return cached;
      rethrow;
    }
  }

  Future<ParentAnnouncementData> markAnnouncementRead(
      CacheScope scope, ParentAnnouncement item) async {
    final response = await dio.post<dynamic>('announcements/${item.id}/read/');
    final canonical = Map<String, dynamic>.from(response.data as Map);
    final current = await readAnnouncements(scope);
    final rows = [...?current?.items];
    final index = rows.indexWhere((row) => row.id == item.id);
    if (index >= 0) {
      rows[index] = item.copyWith(isRead: canonical['is_read'] == true);
    }
    return _saveAnnouncements(scope, rows);
  }

  Future<ParentConversation> inquireAnnouncement(int id, int childId) async {
    final response = await dio.post<dynamic>('announcements/$id/inquiry/',
        data: {'student_id': childId});
    return ParentConversation.fromJson(
        Map<String, dynamic>.from(response.data as Map));
  }

  Future<ParentAnnouncementData> _saveAnnouncements(
      CacheScope scope, List<ParentAnnouncement> items) async {
    final now = DateTime.now().toUtc();
    await _write(scope, _announcementsKey,
        items.map((item) => item.toJson()).toList(), now);
    return ParentAnnouncementData(items, now);
  }

  Future<ParentConversationData?> readConversations(CacheScope scope) async {
    final row = await _read(scope, _conversationsKey);
    if (row == null) return null;
    return ParentConversationData(
      _cachedRows(row).map(ParentConversation.fromJson).toList(),
      row.lastSyncedAt,
      offline: true,
    );
  }

  Future<ParentConversationData> refreshConversations(CacheScope scope) async {
    final response = await dio.get<dynamic>('conversations/');
    return _saveConversations(
        scope, _rows(response.data).map(ParentConversation.fromJson).toList());
  }

  Future<ParentConversationData> loadConversations(CacheScope scope) async {
    final cached = await readConversations(scope);
    try {
      return await refreshConversations(scope);
    } catch (error) {
      if (cached != null && isOfflineEligibleError(error)) return cached;
      rethrow;
    }
  }

  Future<ParentConversationData> markConversationRead(
      CacheScope scope, ParentConversation item) async {
    await dio.post<dynamic>('conversations/${item.id}/read/');
    final current = await readConversations(scope);
    final rows = [...?current?.items];
    final index = rows.indexWhere((row) => row.id == item.id);
    if (index >= 0) rows[index] = item.copyWith(unread: 0);
    return _saveConversations(scope, rows);
  }

  Future<ParentConversationData> createSupport(
      CacheScope scope, String subject, String category) async {
    final response = await dio.post<dynamic>('conversations/start/', data: {
      'conversation_type': 'school_support',
      'subject': subject,
      'category': category,
      'priority': 'normal',
    });
    final canonical = ParentConversation.fromJson(
        Map<String, dynamic>.from(response.data as Map));
    final current = await readConversations(scope);
    final rows = [
      canonical,
      ...?current?.items.where((e) => e.id != canonical.id)
    ];
    return _saveConversations(scope, rows);
  }

  Future<ParentConversationData> _saveConversations(
      CacheScope scope, List<ParentConversation> items) async {
    final now = DateTime.now().toUtc();
    await _write(scope, _conversationsKey,
        items.map((item) => item.toJson()).toList(), now);
    return ParentConversationData(items, now);
  }

  Future<List<ParentMessage>?> readMessages(CacheScope scope, int id) async {
    final row = await _read(scope, _messagesKey(id));
    if (row == null) return null;
    return _cachedRows(row).map(ParentMessage.fromJson).toList();
  }

  Future<List<ParentMessage>> loadMessages(CacheScope scope, int id) async {
    final cached = await readMessages(scope, id);
    try {
      final response = await dio.get<dynamic>('conversations/$id/messages/');
      final messages =
          _rows(response.data).map(ParentMessage.fromJson).toList();
      await _saveMessages(scope, id, messages);
      return messages;
    } catch (error) {
      if (cached != null && isOfflineEligibleError(error)) return cached;
      rethrow;
    }
  }

  Future<List<ParentMessage>> sendMessage(
      CacheScope scope, int id, String body) async {
    final response = await dio
        .post<dynamic>('conversations/$id/messages/', data: {'body': body});
    final canonical =
        ParentMessage.fromJson(Map<String, dynamic>.from(response.data as Map));
    final messages = [...?await readMessages(scope, id), canonical];
    await _saveMessages(scope, id, messages);
    return messages;
  }

  Future<void> _saveMessages(
      CacheScope scope, int id, List<ParentMessage> items) async {
    await _write(scope, _messagesKey(id),
        items.map((item) => item.toJson()).toList(), DateTime.now().toUtc());
  }

  Future<CachedContext?> _read(CacheScope scope, String resource) async {
    for (final row in await database.readContexts(scope)) {
      if (row.resourceId == resource) return row;
    }
    return null;
  }

  List<Map<String, dynamic>> _cachedRows(CachedContext row) {
    final payload =
        Map<String, dynamic>.from(jsonDecode(row.payloadJson) as Map);
    return (payload['items'] as List? ?? const [])
        .whereType<Map>()
        .map((item) => Map<String, dynamic>.from(item))
        .toList();
  }

  Future<void> _write(CacheScope scope, String resource,
          List<Map<String, Object?>> items, DateTime at) =>
      database.putContext(
        scope: scope,
        resourceId: resource,
        payload: {'items': items},
        isHistorical: false,
        syncedAt: at,
      );

  List<Map<String, dynamic>> _rows(Object? payload) {
    final raw = payload is Map ? payload['results'] : payload;
    return (raw as List? ?? const [])
        .whereType<Map>()
        .map((item) => Map<String, dynamic>.from(item))
        .toList();
  }
}
