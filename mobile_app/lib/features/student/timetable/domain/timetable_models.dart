class TimetablePeriod {
  const TimetablePeriod(
      {required this.id,
      required this.name,
      required this.sequence,
      required this.startTime,
      required this.endTime,
      required this.kind});
  final int id;
  final String name;
  final int sequence;
  final String startTime;
  final String endTime;
  final String kind;
  bool get isBreak => kind == 'break';

  factory TimetablePeriod.fromJson(Map<String, dynamic> json) =>
      TimetablePeriod(
          id: json['id'] as int,
          name: json['name']?.toString() ?? '',
          sequence: json['sequence'] as int? ?? 0,
          startTime: json['start_time']?.toString() ?? '',
          endTime: json['end_time']?.toString() ?? '',
          kind: json['kind']?.toString() ?? 'lesson');
}

class TimetableEntryModel {
  const TimetableEntryModel(
      {required this.id,
      required this.weekday,
      required this.period,
      required this.teacher,
      required this.subject,
      required this.classroom,
      required this.section,
      required this.status});
  final int id;
  final int weekday;
  final TimetablePeriod period;
  final String teacher;
  final String subject;
  final String classroom;
  final String section;
  final String status;

  factory TimetableEntryModel.fromJson(Map<String, dynamic> json) =>
      TimetableEntryModel(
          id: json['id'] as int,
          weekday: json['weekday'] as int,
          period: TimetablePeriod.fromJson(
              Map<String, dynamic>.from(json['period_detail'] as Map)),
          teacher: json['teacher']?.toString() ?? '',
          subject: json['subject']?.toString() ?? '',
          classroom: json['classroom']?.toString() ?? '',
          section: json['section']?.toString() ?? '',
          status: json['status']?.toString() ?? 'upcoming');
}

class TodayTimetable {
  const TodayTimetable(
      {required this.date, required this.entries, required this.periods});
  final DateTime date;
  final List<TimetableEntryModel> entries;
  final List<TimetablePeriod> periods;
  factory TodayTimetable.fromJson(Map<String, dynamic> json) => TodayTimetable(
      date: DateTime.parse(json['date'].toString()),
      entries: _entries(json['entries']),
      periods: _periods(json['periods']));
}

class TimetableDay {
  const TimetableDay(
      {required this.date, required this.weekday, required this.entries});
  final DateTime date;
  final int weekday;
  final List<TimetableEntryModel> entries;
  factory TimetableDay.fromJson(Map<String, dynamic> json) => TimetableDay(
      date: DateTime.parse(json['date'].toString()),
      weekday: json['weekday'] as int,
      entries: _entries(json['entries']));
}

class WeekTimetable {
  const WeekTimetable({required this.weekStart, required this.days});
  final DateTime weekStart;
  final List<TimetableDay> days;
  factory WeekTimetable.fromJson(Map<String, dynamic> json) {
    final days = (json['days'] as List? ?? const [])
        .map((e) => TimetableDay.fromJson(Map<String, dynamic>.from(e as Map)))
        .toList()
      ..sort((a, b) => a.date.compareTo(b.date));
    return WeekTimetable(
      weekStart: DateTime.parse(json['week_start'].toString()),
      days: days,
    );
  }
}

List<TimetableEntryModel> _entries(Object? value) {
  final entries = (value as List? ?? const [])
      .map((e) =>
          TimetableEntryModel.fromJson(Map<String, dynamic>.from(e as Map)))
      .toList()
    ..sort((a, b) {
      final sequence = a.period.sequence.compareTo(b.period.sequence);
      return sequence != 0 ? sequence : a.id.compareTo(b.id);
    });
  return entries;
}

List<TimetablePeriod> _periods(Object? value) {
  final periods = (value as List? ?? const [])
      .map((e) => TimetablePeriod.fromJson(Map<String, dynamic>.from(e as Map)))
      .toList()
    ..sort((a, b) {
      final sequence = a.sequence.compareTo(b.sequence);
      return sequence != 0 ? sequence : a.id.compareTo(b.id);
    });
  return periods;
}

TimetableEntryModel? nullableEntry(Map<String, dynamic> json, String key) {
  final value = json[key];
  return value is Map
      ? TimetableEntryModel.fromJson(Map<String, dynamic>.from(value))
      : null;
}
