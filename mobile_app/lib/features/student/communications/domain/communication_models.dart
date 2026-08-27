class CommunicationNotification {
  const CommunicationNotification(
      {required this.id,
      required this.type,
      required this.title,
      required this.body,
      required this.isRead,
      required this.createdAt,
      this.action});
  final int id;
  final String type;
  final String title;
  final String body;
  final bool isRead;
  final DateTime createdAt;
  final Map<String, dynamic>? action;
  factory CommunicationNotification.fromJson(Map<String, dynamic> j) =>
      CommunicationNotification(
          id: j['id'] as int,
          type: (j['notification_type'] ?? 'system').toString(),
          title: (j['title'] ?? '').toString(),
          body: (j['body'] ?? '').toString(),
          isRead: j['is_read'] == true,
          createdAt: DateTime.tryParse((j['created_at'] ?? '').toString()) ??
              DateTime.fromMillisecondsSinceEpoch(0),
          action: j['action'] is Map
              ? Map<String, dynamic>.from(j['action'] as Map)
              : null);
}

class SchoolAnnouncement {
  const SchoolAnnouncement(
      {required this.id,
      required this.title,
      required this.body,
      required this.priority,
      required this.publishedAt,
      required this.isRead,
      required this.canInquire,
      required this.attachments});
  final int id;
  final String title, body, priority;
  final DateTime? publishedAt;
  final bool isRead, canInquire;
  final List<Map<String, dynamic>> attachments;
  factory SchoolAnnouncement.fromJson(Map<String, dynamic> j) {
    final r = j['receipt'] is Map ? j['receipt'] as Map : null;
    final p = j['permissions'] is Map ? j['permissions'] as Map : null;
    return SchoolAnnouncement(
        id: j['id'] as int,
        title: (j['title'] ?? '').toString(),
        body: (j['body'] ?? '').toString(),
        priority: (j['priority'] ?? 'normal').toString(),
        publishedAt: DateTime.tryParse((j['published_at'] ?? '').toString()),
        isRead: r?['is_read'] == true,
        canInquire: p?['can_inquire'] == true,
        attachments: (j['attachments'] as List? ?? const [])
            .whereType<Map>()
            .map((e) => Map<String, dynamic>.from(e))
            .toList());
  }
}

class ConversationSummary {
  const ConversationSummary(
      {required this.id,
      required this.type,
      required this.subject,
      required this.status,
      required this.category,
      required this.unread,
      required this.canReply,
      required this.participants,
      required this.preview,
      required this.updatedAt});
  final int id, unread;
  final String type, subject, status, category, preview;
  final bool canReply;
  final List<String> participants;
  final DateTime updatedAt;
  bool get isSchoolSupport => type == 'school_support';
  factory ConversationSummary.fromJson(Map<String, dynamic> j) =>
      ConversationSummary(
          id: j['id'] as int,
          type: (j['conversation_type'] ?? '').toString(),
          subject: (j['subject'] ?? '').toString(),
          status: (j['status'] ?? 'open').toString(),
          category: (j['category'] ?? '').toString(),
          unread: (j['unread_messages_count'] as num?)?.toInt() ?? 0,
          canReply: j['can_reply'] == true,
          participants: (j['participants_summary'] as List? ?? const [])
              .whereType<Map>()
              .map((e) => (e['display_name'] ?? '').toString())
              .where((e) => e.isNotEmpty)
              .toList(),
          preview: (j['last_message_preview'] ?? '').toString(),
          updatedAt: DateTime.tryParse(
                  (j['last_message_at'] ?? j['updated_at'] ?? '').toString()) ??
              DateTime.fromMillisecondsSinceEpoch(0));
}

class ConversationMessage {
  const ConversationMessage(
      {required this.id,
      required this.body,
      required this.sender,
      required this.senderRole,
      required this.createdAt,
      required this.attachmentsCount});
  final int id, attachmentsCount;
  final String body, sender, senderRole;
  final DateTime createdAt;
  factory ConversationMessage.fromJson(Map<String, dynamic> j) {
    final s = j['sender'] is Map ? j['sender'] as Map : const {};
    return ConversationMessage(
        id: j['id'] as int,
        body: (j['body'] ?? '').toString(),
        sender: (s['display_name'] ?? '').toString(),
        senderRole: (s['role'] ?? '').toString(),
        createdAt: DateTime.tryParse((j['created_at'] ?? '').toString()) ??
            DateTime.fromMillisecondsSinceEpoch(0),
        attachmentsCount: (j['attachments_count'] as num?)?.toInt() ?? 0);
  }
}

class CommunicationBadges {
  const CommunicationBadges(this.notifications, this.conversations);
  final int notifications, conversations;
  int get total => notifications + conversations;
  factory CommunicationBadges.fromJson(Map<String, dynamic> j) =>
      CommunicationBadges((j['notification_unread'] as num?)?.toInt() ?? 0,
          (j['conversation_unread'] as num?)?.toInt() ?? 0);
}
