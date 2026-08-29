class TeacherTimetablePeriod {
  const TeacherTimetablePeriod({
    required this.id,
    required this.name,
    required this.sequence,
    required this.startTime,
    required this.endTime,
    required this.kind,
    required this.isActive,
  });

  final int id;
  final String name;
  final int sequence;
  final String startTime;
  final String endTime;
  final String kind;
  final bool isActive;
  bool get isBreak => kind == 'break';

  factory TeacherTimetablePeriod.fromJson(Map<String, dynamic> json) =>
      TeacherTimetablePeriod(
        id: (json['id'] as num).toInt(),
        name: json['name']?.toString() ?? '',
        sequence: (json['sequence'] as num?)?.toInt() ?? 0,
        startTime: json['start_time']?.toString() ?? '',
        endTime: json['end_time']?.toString() ?? '',
        kind: json['kind']?.toString() ?? 'lesson',
        isActive: json['is_active'] as bool? ?? true,
      );
}

class TeacherLesson {
  const TeacherLesson({
    required this.id,
    required this.weekday,
    required this.period,
    required this.subject,
    required this.classroom,
    required this.section,
    required this.status,
    required this.roomOrLocation,
  });

  final int id;
  final int weekday;
  final TeacherTimetablePeriod period;
  final String subject;
  final String classroom;
  final String section;
  final String status;
  final String roomOrLocation;

  factory TeacherLesson.fromJson(Map<String, dynamic> json) => TeacherLesson(
        id: (json['id'] as num).toInt(),
        weekday: (json['weekday'] as num).toInt(),
        period: TeacherTimetablePeriod.fromJson(
          Map<String, dynamic>.from(json['period_detail'] as Map),
        ),
        subject: json['subject']?.toString() ?? '',
        classroom: json['classroom']?.toString() ?? '',
        section: json['section']?.toString() ?? '',
        status: json['status']?.toString() ?? 'upcoming',
        roomOrLocation: json['room_or_location']?.toString() ?? '',
      );
}

class TeacherTodayTimetable {
  const TeacherTodayTimetable({
    required this.date,
    required this.weekday,
    required this.entries,
    required this.periods,
    this.current,
    this.next,
  });

  final DateTime date;
  final int weekday;
  final List<TeacherLesson> entries;
  final List<TeacherTimetablePeriod> periods;
  final TeacherLesson? current;
  final TeacherLesson? next;

  factory TeacherTodayTimetable.fromJson(Map<String, dynamic> json) =>
      TeacherTodayTimetable(
        date: DateTime.parse(json['date'].toString()),
        weekday: (json['weekday'] as num?)?.toInt() ?? 0,
        entries: teacherLessons(json['entries']),
        periods: teacherPeriods(json['periods']),
        current: nullableTeacherLesson(json, 'current_entry'),
        next: nullableTeacherLesson(json, 'next_entry'),
      );
}

class TeacherTimetableDay {
  const TeacherTimetableDay({
    required this.date,
    required this.weekday,
    required this.entries,
  });

  final DateTime date;
  final int weekday;
  final List<TeacherLesson> entries;

  factory TeacherTimetableDay.fromJson(Map<String, dynamic> json) =>
      TeacherTimetableDay(
        date: DateTime.parse(json['date'].toString()),
        weekday: (json['weekday'] as num).toInt(),
        entries: teacherLessons(json['entries']),
      );
}

class TeacherWeekTimetable {
  const TeacherWeekTimetable({required this.weekStart, required this.days});

  final DateTime weekStart;
  final List<TeacherTimetableDay> days;

  factory TeacherWeekTimetable.fromJson(Map<String, dynamic> json) {
    final days = (json['days'] as List? ?? const [])
        .map((item) => TeacherTimetableDay.fromJson(
            Map<String, dynamic>.from(item as Map)))
        .toList()
      ..sort((a, b) => a.date.compareTo(b.date));
    return TeacherWeekTimetable(
      weekStart: DateTime.parse(json['week_start'].toString()),
      days: days,
    );
  }
}

class DatedTeacherLesson {
  const DatedTeacherLesson({required this.date, required this.lesson});
  final DateTime date;
  final TeacherLesson lesson;
}

class TeacherTimetableData {
  const TeacherTimetableData({
    required this.today,
    required this.week,
    required this.lastUpdated,
    required this.fromCache,
    this.current,
    this.next,
  });

  final TeacherTodayTimetable today;
  final TeacherWeekTimetable week;
  final DatedTeacherLesson? current;
  final DatedTeacherLesson? next;
  final DateTime lastUpdated;
  final bool fromCache;
}

List<TeacherLesson> teacherLessons(Object? value) {
  final rows = (value as List? ?? const [])
      .map((item) =>
          TeacherLesson.fromJson(Map<String, dynamic>.from(item as Map)))
      .toList()
    ..sort((a, b) {
      final sequence = a.period.sequence.compareTo(b.period.sequence);
      return sequence != 0 ? sequence : a.id.compareTo(b.id);
    });
  return rows;
}

List<TeacherTimetablePeriod> teacherPeriods(Object? value) {
  final rows = (value as List? ?? const [])
      .map((item) => TeacherTimetablePeriod.fromJson(
          Map<String, dynamic>.from(item as Map)))
      .where((item) => item.isActive)
      .toList()
    ..sort((a, b) {
      final sequence = a.sequence.compareTo(b.sequence);
      return sequence != 0 ? sequence : a.id.compareTo(b.id);
    });
  return rows;
}

TeacherLesson? nullableTeacherLesson(
    Map<String, dynamic> json, String key) {
  final value = json[key];
  return value is Map
      ? TeacherLesson.fromJson(Map<String, dynamic>.from(value))
      : null;
}

DatedTeacherLesson? datedTeacherLesson(
    Map<String, dynamic> json, String key) {
  final lesson = nullableTeacherLesson(json, key);
  final rawDate = json['date'];
  return lesson == null || rawDate == null
      ? null
      : DatedTeacherLesson(
          date: DateTime.parse(rawDate.toString()),
          lesson: lesson,
        );
}
