import 'package:dio/dio.dart';

import '../domain/teacher_communication_models.dart';

abstract interface class TeacherCommunicationsDataSource {
  Future<List<TeacherNotification>> notifications();
  Future<TeacherNotification> markNotificationRead(int id);
  Future<int> markAllNotificationsRead();
  Future<List<TeacherAnnouncement>> announcements();
  Future<TeacherAnnouncement> announcement(int id);
  Future<TeacherAnnouncement> createAnnouncement(TeacherAnnouncementDraft draft);
  Future<TeacherAnnouncement> updateAnnouncement(
    int id,
    TeacherAnnouncementDraft draft,
  );
  Future<TeacherAnnouncement> announcementAction(int id, String action);
  Future<TeacherAnnouncement> markAnnouncementRead(int id);
  Future<List<TeacherConversation>> conversations();
  Future<List<TeacherMessage>> messages(int conversationId);
  Future<void> markConversationRead(int conversationId);
  Future<TeacherMessage> sendMessage(int conversationId, String body);
  Future<TeacherConversation> startStudentConversation(
    TeacherStudentConversationDraft draft,
  );
}

class TeacherCommunicationsRepository
    implements TeacherCommunicationsDataSource {
  const TeacherCommunicationsRepository(this.dio);
  final Dio dio;

  @override
  Future<List<TeacherNotification>> notifications() async {
    final response = await dio.get<dynamic>('notifications/');
    return _rows(response.data)
        .map(TeacherNotification.fromJson)
        .toList(growable: false);
  }

  @override
  Future<TeacherNotification> markNotificationRead(int id) async {
    final response = await dio.post<Map<String, dynamic>>(
      'notifications/$id/read/',
    );
    return TeacherNotification.fromJson(response.data!);
  }

  @override
  Future<int> markAllNotificationsRead() async {
    final response = await dio.post<Map<String, dynamic>>(
      'notifications/read-all/',
    );
    return (response.data?['updated_count'] as num?)?.toInt() ?? 0;
  }

  @override
  Future<List<TeacherAnnouncement>> announcements() async {
    final response = await dio.get<dynamic>('announcements/');
    return _rows(response.data)
        .map(TeacherAnnouncement.fromJson)
        .toList(growable: false);
  }

  @override
  Future<TeacherAnnouncement> announcement(int id) async {
    final response =
        await dio.get<Map<String, dynamic>>('announcements/$id/');
    return TeacherAnnouncement.fromJson(response.data!);
  }

  @override
  Future<TeacherAnnouncement> createAnnouncement(
    TeacherAnnouncementDraft draft,
  ) async {
    final response = await dio.post<Map<String, dynamic>>(
      'announcements/',
      data: draft.toJson(),
    );
    return TeacherAnnouncement.fromJson(response.data!);
  }

  @override
  Future<TeacherAnnouncement> updateAnnouncement(
    int id,
    TeacherAnnouncementDraft draft,
  ) async {
    final response = await dio.patch<Map<String, dynamic>>(
      'announcements/$id/',
      data: draft.toJson(),
    );
    return TeacherAnnouncement.fromJson(response.data!);
  }

  @override
  Future<TeacherAnnouncement> announcementAction(
    int id,
    String action,
  ) async {
    if (!const {'publish', 'close', 'archive'}.contains(action)) {
      throw ArgumentError.value(action, 'action');
    }
    final response = await dio.post<Map<String, dynamic>>(
      'announcements/$id/$action/',
    );
    return TeacherAnnouncement.fromJson(response.data!);
  }

  @override
  Future<TeacherAnnouncement> markAnnouncementRead(int id) async {
    await dio.post<void>('announcements/$id/read/');
    return announcement(id);
  }

  @override
  Future<List<TeacherConversation>> conversations() async {
    final response = await dio.get<dynamic>('conversations/');
    return _rows(response.data)
        .map(TeacherConversation.fromJson)
        .toList(growable: false);
  }

  @override
  Future<List<TeacherMessage>> messages(int conversationId) async {
    final response =
        await dio.get<dynamic>('conversations/$conversationId/messages/');
    return _rows(response.data)
        .map(TeacherMessage.fromJson)
        .toList(growable: false);
  }

  @override
  Future<void> markConversationRead(int conversationId) async {
    await dio.post<void>('conversations/$conversationId/read/');
  }

  @override
  Future<TeacherMessage> sendMessage(int conversationId, String body) async {
    final response = await dio.post<Map<String, dynamic>>(
      'conversations/$conversationId/messages/',
      data: {'body': body},
    );
    return TeacherMessage.fromJson(response.data!);
  }

  @override
  Future<TeacherConversation> startStudentConversation(
    TeacherStudentConversationDraft draft,
  ) async {
    final response = await dio.post<Map<String, dynamic>>(
      'conversations/start/',
      data: draft.toJson(),
    );
    return TeacherConversation.fromJson(response.data!);
  }
}

List<Map<String, dynamic>> _rows(dynamic payload) {
  final raw = payload is Map ? payload['results'] : payload;
  return (raw as List? ?? const [])
      .whereType<Map>()
      .map((row) => Map<String, dynamic>.from(row))
      .toList(growable: false);
}
