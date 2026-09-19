Map<String, dynamic> _map(Object? value) =>
    value is Map ? Map<String, dynamic>.from(value) : const {};

DateTime? _date(Object? value) =>
    value == null ? null : DateTime.tryParse(value.toString());

class TeacherNotificationAction {
  const TeacherNotificationAction({required this.route, required this.params});
  final String route;
  final Map<String, dynamic> params;

  factory TeacherNotificationAction.fromJson(Map<String, dynamic> json) =>
      TeacherNotificationAction(
        route: json['route']?.toString() ?? '',
        params: _map(json['params']),
      );
}

class TeacherNotification {
  const TeacherNotification({
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
  final String type;
  final String title;
  final String body;
  final bool isRead;
  final DateTime createdAt;
  final DateTime? readAt;
  final TeacherNotificationAction? action;

  factory TeacherNotification.fromJson(Map<String, dynamic> json) {
    final action = _map(json['action']);
    return TeacherNotification(
      id: (json['id'] as num).toInt(),
      type: json['notification_type']?.toString() ?? '',
      title: json['title']?.toString() ?? '',
      body: json['body']?.toString() ?? '',
      isRead: json['is_read'] == true,
      readAt: _date(json['read_at']),
      createdAt:
          _date(json['created_at']) ?? DateTime.fromMillisecondsSinceEpoch(0),
      action: action.isEmpty ? null : TeacherNotificationAction.fromJson(action),
    );
  }
}

class TeacherAnnouncementPermissions {
  const TeacherAnnouncementPermissions({
    required this.canEdit,
    required this.canPublish,
    required this.canClose,
    required this.canArchive,
    required this.canInquire,
  });

  final bool canEdit;
  final bool canPublish;
  final bool canClose;
  final bool canArchive;
  final bool canInquire;

  factory TeacherAnnouncementPermissions.fromJson(Map<String, dynamic> json) =>
      TeacherAnnouncementPermissions(
        canEdit: json['can_edit'] == true,
        canPublish: json['can_publish'] == true,
        canClose: json['can_close'] == true,
        canArchive: json['can_archive'] == true,
        canInquire: json['can_inquire'] == true,
      );
}

class TeacherAnnouncement {
  const TeacherAnnouncement({
    required this.id,
    required this.title,
    required this.body,
    required this.status,
    required this.priority,
    required this.hasReceipt,
    required this.isRead,
    required this.permissions,
    required this.createdAt,
    this.assignmentId,
    this.assignmentSubject = '',
    this.includeParents = false,
    this.allowInquiry = false,
    this.publishedAt,
    this.readAt,
  });

  final int id;
  final String title;
  final String body;
  final String status;
  final String priority;
  final int? assignmentId;
  final String assignmentSubject;
  final bool includeParents;
  final bool allowInquiry;
  final bool hasReceipt;
  final bool isRead;
  final DateTime createdAt;
  final DateTime? publishedAt;
  final DateTime? readAt;
  final TeacherAnnouncementPermissions permissions;

  factory TeacherAnnouncement.fromJson(Map<String, dynamic> json) {
    final assignment = _map(json['teacher_assignment']);
    final receipt = _map(json['receipt']);
    return TeacherAnnouncement(
      id: (json['id'] as num).toInt(),
      title: json['title']?.toString() ?? '',
      body: json['body']?.toString() ?? '',
      status: json['status']?.toString() ?? 'draft',
      priority: json['priority']?.toString() ?? 'normal',
      assignmentId: (assignment['id'] as num?)?.toInt(),
      assignmentSubject:
          _map(assignment['subject'])['name']?.toString() ?? '',
      includeParents: json['include_parents'] == true,
      allowInquiry: json['allow_inquiry'] == true,
      hasReceipt: receipt.isNotEmpty,
      isRead: receipt['is_read'] == true,
      readAt: _date(receipt['read_at']),
      createdAt:
          _date(json['created_at']) ?? DateTime.fromMillisecondsSinceEpoch(0),
      publishedAt: _date(json['published_at']),
      permissions:
          TeacherAnnouncementPermissions.fromJson(_map(json['permissions'])),
    );
  }
}

class TeacherAnnouncementDraft {
  const TeacherAnnouncementDraft({
    required this.title,
    required this.body,
    required this.assignmentId,
    this.priority = 'normal',
    this.includeParents = false,
    this.allowInquiry = false,
  });

  final String title;
  final String body;
  final int assignmentId;
  final String priority;
  final bool includeParents;
  final bool allowInquiry;

  Map<String, dynamic> toJson() => {
        'title': title,
        'body': body,
        'priority': priority,
        'audience_type': 'teacher_assignment',
        'teacher_assignment': assignmentId,
        'include_parents': includeParents,
        'allow_inquiry': allowInquiry,
      };
}

class TeacherConversationParticipant {
  const TeacherConversationParticipant({required this.role, required this.name});
  final String role;
  final String name;

  factory TeacherConversationParticipant.fromJson(Map<String, dynamic> json) =>
      TeacherConversationParticipant(
        role: json['role']?.toString() ?? '',
        name: json['display_name']?.toString() ?? '',
      );
}

class TeacherConversation {
  const TeacherConversation({
    required this.id,
    required this.type,
    required this.subject,
    required this.status,
    required this.preview,
    required this.unreadCount,
    required this.canReply,
    required this.participants,
  });

  final int id;
  final String type;
  final String subject;
  final String status;
  final String preview;
  final int unreadCount;
  final bool canReply;
  final List<TeacherConversationParticipant> participants;

  factory TeacherConversation.fromJson(Map<String, dynamic> json) =>
      TeacherConversation(
        id: (json['id'] as num).toInt(),
        type: json['conversation_type']?.toString() ?? '',
        subject: json['subject']?.toString() ?? '',
        status: json['status']?.toString() ?? '',
        preview: json['last_message_preview']?.toString() ?? '',
        unreadCount: (json['unread_messages_count'] as num?)?.toInt() ?? 0,
        canReply: json['can_reply'] == true,
        participants: (json['participants_summary'] as List? ?? const [])
            .whereType<Map>()
            .map((row) => TeacherConversationParticipant.fromJson(
                  Map<String, dynamic>.from(row),
                ))
            .toList(growable: false),
      );
}

class TeacherMessage {
  const TeacherMessage({
    required this.id,
    required this.conversationId,
    required this.body,
    required this.senderName,
    required this.senderRole,
    required this.createdAt,
  });

  final int id;
  final int conversationId;
  final String body;
  final String senderName;
  final String senderRole;
  final DateTime createdAt;

  factory TeacherMessage.fromJson(Map<String, dynamic> json) {
    final sender = _map(json['sender']);
    return TeacherMessage(
      id: (json['id'] as num).toInt(),
      conversationId: (json['conversation'] as num).toInt(),
      body: json['body']?.toString() ?? '',
      senderName: sender['display_name']?.toString() ?? '',
      senderRole: sender['role']?.toString() ?? '',
      createdAt:
          _date(json['created_at']) ?? DateTime.fromMillisecondsSinceEpoch(0),
    );
  }
}

class TeacherStudentConversationDraft {
  const TeacherStudentConversationDraft({
    required this.assignmentId,
    required this.studentId,
    required this.subject,
  });

  final int assignmentId;
  final int studentId;
  final String subject;

  Map<String, dynamic> toJson() => {
        'conversation_type': 'teacher_student',
        'teacher_assignment_id': assignmentId,
        'student_id': studentId,
        'subject': subject,
      };
}
