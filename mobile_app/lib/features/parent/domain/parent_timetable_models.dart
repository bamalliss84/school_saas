import '../../student/timetable/domain/timetable_models.dart';

class ParentTimetableData {
  const ParentTimetableData({
    required this.week,
    required this.lastUpdated,
    this.offline = false,
  });

  final WeekTimetable week;
  final DateTime lastUpdated;
  final bool offline;

  factory ParentTimetableData.fromJson(
    Map<String, dynamic> json,
    DateTime lastUpdated, {
    bool offline = false,
  }) =>
      ParentTimetableData(
        week: WeekTimetable.fromJson(json),
        lastUpdated: lastUpdated,
        offline: offline,
      );

  ParentTimetableData copyWith({bool? offline}) => ParentTimetableData(
        week: week,
        lastUpdated: lastUpdated,
        offline: offline ?? this.offline,
      );
}
