class ParentBrief {
  const ParentBrief({required this.id, required this.name});
  final int id;
  final String name;
  factory ParentBrief.fromJson(Map<String, dynamic> json) => ParentBrief(
      id: (json['id'] as num?)?.toInt() ?? 0,
      name: json['name']?.toString() ?? '');
  Map<String, Object?> toJson() => {'id': id, 'name': name};
}

class ParentChild {
  const ParentChild(
      {required this.id,
      required this.studentCode,
      required this.fullName,
      required this.relationship,
      required this.isPrimary,
      required this.school});
  final int id;
  final String studentCode, fullName, relationship;
  final bool isPrimary;
  final ParentBrief school;
  factory ParentChild.fromJson(Map<String, dynamic> json) {
    final student = _map(json['student']);
    return ParentChild(
        id: (student['id'] as num).toInt(),
        studentCode: student['student_code']?.toString() ?? '',
        fullName: student['full_name']?.toString() ?? '',
        relationship: json['relationship_type']?.toString() ?? '',
        isPrimary: json['is_primary'] == true,
        school: ParentBrief.fromJson(_map(student['school'])));
  }
  Map<String, Object?> toJson() => {
        'student': {
          'id': id,
          'student_code': studentCode,
          'full_name': fullName,
          'school': school.toJson()
        },
        'relationship_type': relationship,
        'is_primary': isPrimary
      };
}

class ParentEnrollment {
  const ParentEnrollment(
      {required this.id,
      required this.school,
      required this.academicYear,
      required this.classroom,
      required this.section,
      required this.status,
      required this.isCurrent});
  final int id;
  final ParentBrief school, academicYear, classroom, section;
  final String status;
  final bool isCurrent;
  String get classroomName => classroom.name;
  String get sectionName => section.name;
  factory ParentEnrollment.fromJson(Map<String, dynamic> json) =>
      ParentEnrollment(
          id: (json['id'] as num).toInt(),
          school: ParentBrief.fromJson(_map(json['school'])),
          academicYear: ParentBrief.fromJson(_map(json['academic_year'])),
          classroom: ParentBrief.fromJson(_map(json['classroom'])),
          section: ParentBrief.fromJson(_map(json['section'])),
          status: json['status']?.toString() ?? '',
          isCurrent: json['is_current'] == true);
  Map<String, Object?> toJson() => {
        'id': id,
        'school': school.toJson(),
        'academic_year': academicYear.toJson(),
        'classroom': classroom.toJson(),
        'section': section.toJson(),
        'status': status,
        'is_current': isCurrent
      };
}

class ParentFoundationData {
  const ParentFoundationData(
      {required this.children,
      required this.selectedChildId,
      required this.histories,
      required this.lastUpdated,
      this.offline = false});
  final List<ParentChild> children;
  final int? selectedChildId;
  final Map<int, List<ParentEnrollment>> histories;
  final DateTime lastUpdated;
  final bool offline;
  ParentChild? get selectedChild {
    for (final item in children) {
      if (item.id == selectedChildId) return item;
    }
    return null;
  }

  List<ParentEnrollment> get selectedHistory =>
      histories[selectedChildId] ?? const [];
  ParentEnrollment? get selectedEnrollment {
    if (selectedHistory.isEmpty) return null;
    for (final item in selectedHistory) {
      if (item.isCurrent) return item;
    }
    return selectedHistory.first;
  }

  ParentFoundationData copyWith(
          {List<ParentChild>? children,
          int? selectedChildId,
          Map<int, List<ParentEnrollment>>? histories,
          DateTime? lastUpdated,
          bool? offline}) =>
      ParentFoundationData(
          children: children ?? this.children,
          selectedChildId: selectedChildId ?? this.selectedChildId,
          histories: histories ?? this.histories,
          lastUpdated: lastUpdated ?? this.lastUpdated,
          offline: offline ?? this.offline);
  Map<String, Object?> toJson() => {
        'children': children.map((item) => item.toJson()).toList(),
        'selected_child_id': selectedChildId,
        'histories': {
          for (final entry in histories.entries)
            '${entry.key}': entry.value.map((item) => item.toJson()).toList()
        }
      };
  factory ParentFoundationData.fromJson(
          Map<String, dynamic> json, DateTime lastUpdated,
          {bool offline = false}) =>
      ParentFoundationData(
        children: (json['children'] as List? ?? const [])
            .whereType<Map>()
            .map(
                (item) => ParentChild.fromJson(Map<String, dynamic>.from(item)))
            .toList(growable: false),
        selectedChildId: (json['selected_child_id'] as num?)?.toInt(),
        histories: {
          for (final entry in _map(json['histories']).entries)
            if (int.tryParse(entry.key) case final id?)
              id: (entry.value as List? ?? const [])
                  .whereType<Map>()
                  .map((item) => ParentEnrollment.fromJson(
                      Map<String, dynamic>.from(item)))
                  .toList(growable: false)
        },
        lastUpdated: lastUpdated,
        offline: offline,
      );
}

Map<String, dynamic> _map(Object? value) =>
    value is Map ? Map<String, dynamic>.from(value) : <String, dynamic>{};
