class UnreadCounts {
  const UnreadCounts(
      {this.notifications = 0, this.conversations = 0, this.announcements = 0});
  final int notifications;
  final int conversations;
  final int announcements;

  factory UnreadCounts.fromJson(Map<String, dynamic>? json) => UnreadCounts(
        notifications: json?['notifications'] as int? ?? 0,
        conversations: json?['conversations'] as int? ?? 0,
        announcements: json?['announcements'] as int? ?? 0,
      );
}

class SchoolContext {
  const SchoolContext(
      {required this.membershipId,
      required this.schoolName,
      required this.role,
      required this.status,
      required this.accessMode,
      required this.canWrite,
      this.academicYearName,
      this.isDefault = false,
      this.unread = const UnreadCounts()});
  final int membershipId;
  final String schoolName;
  final String role;
  final String status;
  final String accessMode;
  final bool canWrite;
  final String? academicYearName;
  final bool isDefault;
  final UnreadCounts unread;
  bool get isHistorical => accessMode == 'historical' || !canWrite;
  bool get isActive => status == 'active' && !isHistorical;

  factory SchoolContext.fromJson(Map<String, dynamic> json) => SchoolContext(
        membershipId: json['membership_id'] as int,
        schoolName: (json['school'] as Map?)?['name']?.toString() ?? '',
        role: json['role']?.toString() ?? '',
        status: json['status']?.toString() ?? '',
        accessMode: json['access_mode']?.toString() ?? 'active',
        canWrite: json['can_write'] as bool? ?? false,
        academicYearName: (json['academic_year'] as Map?)?['name']?.toString(),
        isDefault: json['is_default'] as bool? ?? false,
        unread: UnreadCounts.fromJson(json['unread_counts'] is Map
            ? Map<String, dynamic>.from(json['unread_counts'] as Map)
            : null),
      );
}

class ContextListResult {
  const ContextListResult({required this.contexts, this.current});
  final List<SchoolContext> contexts;
  final SchoolContext? current;
  factory ContextListResult.fromJson(Map<String, dynamic> json) {
    final contexts = (json['contexts'] as List? ?? const [])
        .map((item) =>
            SchoolContext.fromJson(Map<String, dynamic>.from(item as Map)))
        .toList();
    final current = json['current_context'];
    return ContextListResult(
        contexts: contexts,
        current: current is Map
            ? SchoolContext.fromJson(Map<String, dynamic>.from(current))
            : null);
  }
}
