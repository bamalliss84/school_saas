class ParentNotification {
  const ParentNotification({
    required this.id,
    required this.type,
    required this.title,
    required this.body,
    required this.isRead,
    required this.createdAt,
    this.readAt,
    this.action,
  });
  final int id;
  final String type, title, body;
  final bool isRead;
  final DateTime createdAt;
  final DateTime? readAt;
  final Map<String, dynamic>? action;

  factory ParentNotification.fromJson(Map<String, dynamic> json) =>
      ParentNotification(
        id: (json['id'] as num).toInt(),
        type: json['notification_type']?.toString() ?? 'system',
        title: json['title']?.toString() ?? '',
        body: json['body']?.toString() ?? '',
        isRead: json['is_read'] == true,
        readAt: _date(json['read_at']),
        createdAt:
            _date(json['created_at']) ?? DateTime.fromMillisecondsSinceEpoch(0),
        action: json['action'] is Map
            ? Map<String, dynamic>.from(json['action'] as Map)
            : null,
      );
  Map<String, Object?> toJson() => {
        'id': id,
        'notification_type': type,
        'title': title,
        'body': body,
        'is_read': isRead,
        'read_at': readAt?.toIso8601String(),
        'created_at': createdAt.toIso8601String(),
        'action': action,
      };
  ParentNotification copyWith({bool? isRead, DateTime? readAt}) =>
      ParentNotification(
        id: id,
        type: type,
        title: title,
        body: body,
        isRead: isRead ?? this.isRead,
        readAt: readAt ?? this.readAt,
        createdAt: createdAt,
        action: action,
      );
}

class ParentAnnouncement {
  const ParentAnnouncement({
    required this.id,
    required this.title,
    required this.body,
    required this.status,
    required this.priority,
    required this.isRead,
    required this.canInquire,
    required this.attachments,
    this.publishedAt,
  });
  final int id;
  final String title, body, status, priority;
  final bool isRead, canInquire;
  final DateTime? publishedAt;
  final List<Map<String, dynamic>> attachments;

  factory ParentAnnouncement.fromJson(Map<String, dynamic> json) {
    final receipt = json['receipt'] is Map ? json['receipt'] as Map : const {};
    final permissions =
        json['permissions'] is Map ? json['permissions'] as Map : const {};
    return ParentAnnouncement(
      id: (json['id'] as num).toInt(),
      title: json['title']?.toString() ?? '',
      body: json['body']?.toString() ?? '',
      status: json['status']?.toString() ?? '',
      priority: json['priority']?.toString() ?? 'normal',
      isRead: receipt['is_read'] == true,
      canInquire: permissions['can_inquire'] == true,
      publishedAt: _date(json['published_at']),
      attachments: (json['attachments'] as List? ?? const [])
          .whereType<Map>()
          .map((item) => Map<String, dynamic>.from(item))
          .toList(growable: false),
    );
  }
  Map<String, Object?> toJson() => {
        'id': id,
        'title': title,
        'body': body,
        'status': status,
        'priority': priority,
        'published_at': publishedAt?.toIso8601String(),
        'attachments': attachments,
        'receipt': {'is_read': isRead},
        'permissions': {'can_inquire': canInquire},
      };
  ParentAnnouncement copyWith({bool? isRead}) => ParentAnnouncement(
        id: id,
        title: title,
        body: body,
        status: status,
        priority: priority,
        isRead: isRead ?? this.isRead,
        canInquire: canInquire,
        publishedAt: publishedAt,
        attachments: attachments,
      );
}

class ParentConversation {
  const ParentConversation({
    required this.id,
    required this.type,
    required this.subject,
    required this.status,
    required this.category,
    required this.unread,
    required this.canReply,
    required this.participants,
    required this.preview,
    required this.updatedAt,
  });
  final int id, unread;
  final String type, subject, status, category, preview;
  final bool canReply;
  final List<String> participants;
  final DateTime updatedAt;

  factory ParentConversation.fromJson(Map<String, dynamic> json) =>
      ParentConversation(
        id: (json['id'] as num).toInt(),
        type: json['conversation_type']?.toString() ?? '',
        subject: json['subject']?.toString() ?? '',
        status: json['status']?.toString() ?? 'open',
        category: json['category']?.toString() ?? '',
        unread: (json['unread_messages_count'] as num?)?.toInt() ?? 0,
        canReply: json['can_reply'] == true,
        participants: (json['participants_summary'] as List? ?? const [])
            .whereType<Map>()
            .map((item) => item['display_name']?.toString() ?? '')
            .where((name) => name.isNotEmpty)
            .toList(growable: false),
        preview: json['last_message_preview']?.toString() ?? '',
        updatedAt: _date(json['last_message_at'] ?? json['updated_at']) ??
            DateTime.fromMillisecondsSinceEpoch(0),
      );
  Map<String, Object?> toJson() => {
        'id': id,
        'conversation_type': type,
        'subject': subject,
        'status': status,
        'category': category,
        'unread_messages_count': unread,
        'can_reply': canReply,
        'participants_summary': participants
            .map((name) => {'display_name': name})
            .toList(growable: false),
        'last_message_preview': preview,
        'updated_at': updatedAt.toIso8601String(),
      };
  ParentConversation copyWith({int? unread}) => ParentConversation(
        id: id,
        type: type,
        subject: subject,
        status: status,
        category: category,
        unread: unread ?? this.unread,
        canReply: canReply,
        participants: participants,
        preview: preview,
        updatedAt: updatedAt,
      );
}

class ParentMessage {
  const ParentMessage({
    required this.id,
    required this.body,
    required this.sender,
    required this.senderRole,
    required this.createdAt,
    required this.attachmentsCount,
  });
  final int id, attachmentsCount;
  final String body, sender, senderRole;
  final DateTime createdAt;
  factory ParentMessage.fromJson(Map<String, dynamic> json) {
    final sender = json['sender'] is Map ? json['sender'] as Map : const {};
    return ParentMessage(
      id: (json['id'] as num).toInt(),
      body: json['body']?.toString() ?? '',
      sender: sender['display_name']?.toString() ?? '',
      senderRole: sender['role']?.toString() ?? '',
      createdAt:
          _date(json['created_at']) ?? DateTime.fromMillisecondsSinceEpoch(0),
      attachmentsCount: (json['attachments_count'] as num?)?.toInt() ?? 0,
    );
  }
  Map<String, Object?> toJson() => {
        'id': id,
        'body': body,
        'sender': {'display_name': sender, 'role': senderRole},
        'created_at': createdAt.toIso8601String(),
        'attachments_count': attachmentsCount,
      };
}

DateTime? _date(Object? value) =>
    value == null ? null : DateTime.tryParse(value.toString());
