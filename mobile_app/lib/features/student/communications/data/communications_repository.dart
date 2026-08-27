import 'dart:convert';
import 'package:dio/dio.dart';
import 'package:file_selector/file_selector.dart';
import '../../../../core/local_database/app_database.dart';
import '../../../../core/offline/offline_error_policy.dart';
import '../domain/communication_models.dart';

class CommunicationsSnapshot {
  const CommunicationsSnapshot(
      {required this.notifications,
      required this.announcements,
      required this.conversations,
      required this.badges,
      required this.lastUpdated,
      this.offline = false});
  final List<CommunicationNotification> notifications;
  final List<SchoolAnnouncement> announcements;
  final List<ConversationSummary> conversations;
  final CommunicationBadges badges;
  final DateTime lastUpdated;
  final bool offline;
}

class StudentCommunicationsRepository {
  StudentCommunicationsRepository(this.dio, this.db);
  final Dio dio;
  final AppDatabase db;
  static const _key = 'student_communications_v1';
  List<Map<String, dynamic>> _rows(dynamic raw) {
    final value = raw is Map ? raw['results'] : raw;
    return (value as List? ?? const [])
        .whereType<Map>()
        .map((e) => Map<String, dynamic>.from(e))
        .toList();
  }

  Future<CommunicationsSnapshot?> read(CacheScope s) async {
    final rows = await db.readContexts(s);
    CachedContext? row;
    for (final item in rows) {
      if (item.resourceId == _key) {
        row = item;
        break;
      }
    }
    if (row == null) return null;
    final j = Map<String, dynamic>.from(jsonDecode(row.payloadJson) as Map);
    return _decode(j, row.lastSyncedAt, offline: true);
  }

  CommunicationsSnapshot _decode(Map<String, dynamic> j, DateTime at,
          {bool offline = false}) =>
      CommunicationsSnapshot(
          notifications: (j['notifications'] as List? ?? const [])
              .whereType<Map>()
              .map((e) => CommunicationNotification.fromJson(
                  Map<String, dynamic>.from(e)))
              .toList(),
          announcements: (j['announcements'] as List? ?? const [])
              .whereType<Map>()
              .map((e) =>
                  SchoolAnnouncement.fromJson(Map<String, dynamic>.from(e)))
              .toList(),
          conversations: (j['conversations'] as List? ?? const [])
              .whereType<Map>()
              .map((e) =>
                  ConversationSummary.fromJson(Map<String, dynamic>.from(e)))
              .toList(),
          badges: CommunicationBadges.fromJson(
              Map<String, dynamic>.from((j['badges'] as Map?) ?? const {})),
          lastUpdated: at,
          offline: offline);
  Future<CommunicationsSnapshot> refresh(CacheScope s) async {
    final rs = await Future.wait([
      dio.get('notifications/'),
      dio.get('announcements/'),
      dio.get('conversations/'),
      dio.get('communication/badges/')
    ]);
    final payload = <String, Object?>{
      'notifications': _rows(rs[0].data),
      'announcements': _rows(rs[1].data),
      'conversations': _rows(rs[2].data),
      'badges': Map<String, dynamic>.from(rs[3].data as Map)
    };
    final now = DateTime.now().toUtc();
    await db.putContext(
        scope: s,
        resourceId: _key,
        payload: payload,
        isHistorical: false,
        syncedAt: now);
    return _decode(Map<String, dynamic>.from(payload), now);
  }

  Future<CommunicationsSnapshot> load(CacheScope s) async {
    final c = await read(s);
    try {
      return await refresh(s);
    } catch (e) {
      if (c != null && isOfflineEligibleError(e)) return c;
      rethrow;
    }
  }

  Future<void> markNotificationRead(int id) =>
      dio.post('notifications/$id/read/');
  Future<void> markAllNotificationsRead() =>
      dio.post('notifications/read-all/');
  Future<void> markAnnouncementRead(int id) =>
      dio.post('announcements/$id/read/');
  Future<int?> inquireAnnouncement(int id) async {
    final r = await dio.post('announcements/$id/inquiry/');
    final d = r.data;
    return d is Map ? (d['id'] as num?)?.toInt() : null;
  }

  Future<List<ConversationMessage>> messages(CacheScope scope, int id) async {
    final key = 'comm_messages:$id';
    List<ConversationMessage>? cached;
    final rows = await db.readContexts(scope);
    for (final row in rows) {
      if (row.resourceId == key) {
        final raw = jsonDecode(row.payloadJson);
        if (raw is Map && raw['messages'] is List) {
          cached = (raw['messages'] as List)
              .whereType<Map>()
              .map((e) =>
                  ConversationMessage.fromJson(Map<String, dynamic>.from(e)))
              .toList();
        }
        break;
      }
    }
    try {
      final r = await dio.get('conversations/$id/messages/');
      final rawRows = _rows(r.data);
      final now = DateTime.now().toUtc();
      await db.putContext(
          scope: scope,
          resourceId: key,
          payload: {'messages': rawRows},
          isHistorical: false,
          syncedAt: now);
      return rawRows.map(ConversationMessage.fromJson).toList();
    } catch (e) {
      if (cached != null && isOfflineEligibleError(e)) return cached;
      rethrow;
    }
  }

  Future<void> markConversationRead(int id) =>
      dio.post('conversations/$id/read/');
  Future<int> sendMessage(int id, String body) async {
    final response =
        await dio.post('conversations/$id/messages/', data: {'body': body});
    return ((response.data as Map)['id'] as num).toInt();
  }

  Future<int> replySupport(int id, String body) async {
    final response =
        await dio.post('school-inbox/$id/reply/', data: {'body': body});
    return ((response.data as Map)['id'] as num).toInt();
  }

  Future<ConversationSummary> createSupport(
      {required String category,
      required String subject,
      required String message}) async {
    final response = await dio.post('school-inbox/', data: {
      'category': category,
      'subject': subject,
      'message': message,
      'priority': 'normal'
    });
    return ConversationSummary.fromJson(
        Map<String, dynamic>.from(response.data as Map));
  }

  Future<void> uploadAttachments(int messageId, List<XFile> files) async {
    if (files.isEmpty) return;
    final parts = <MultipartFile>[];
    for (final file in files) {
      parts.add(await MultipartFile.fromFile(file.path, filename: file.name));
    }
    await dio.post(
      'messages/$messageId/attachments/',
      data: FormData.fromMap({'files': parts}),
    );
  }
}
