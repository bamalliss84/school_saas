import 'package:flutter/material.dart';

/// One school in the child's study record, as returned by
/// `parents/me/children/<id>/schools/` (only schools where this parent has a membership).
class ChildSchoolRecord {
  const ChildSchoolRecord({
    required this.schoolName,
    required this.membershipId,
    required this.isCurrent,
    required this.readOnly,
    required this.years,
  });

  final String schoolName;
  final int? membershipId;
  final bool isCurrent;
  final bool readOnly;
  final List<String> years;

  factory ChildSchoolRecord.fromJson(Map<String, dynamic> json) {
    final school = Map<String, dynamic>.from(json['school'] as Map? ?? const {});
    return ChildSchoolRecord(
      schoolName: '${school['name'] ?? ''}',
      membershipId: (json['membership_id'] as num?)?.toInt(),
      isCurrent: json['is_current'] == true,
      readOnly: json['access_mode'] == 'read_only',
      years: [
        for (final year in json['academic_years'] as List? ?? const [])
          if (year is Map) '${year['name'] ?? ''}',
      ],
    );
  }
}

List<ChildSchoolRecord> parseChildSchools(Object? data) => [
      for (final row in data is List ? data : const [])
        if (row is Map) ChildSchoolRecord.fromJson(Map<String, dynamic>.from(row)),
    ];

class ParentChildHistoryScreen extends StatefulWidget {
  const ParentChildHistoryScreen({
    super.key,
    required this.childName,
    required this.currentMembershipId,
    required this.load,
    required this.onOpenSchool,
  });

  final String childName;
  final int currentMembershipId;
  final Future<List<ChildSchoolRecord>> Function() load;

  /// Switches the app to the school's (possibly historical, read-only) context.
  final Future<void> Function(int membershipId) onOpenSchool;

  @override
  State<ParentChildHistoryScreen> createState() =>
      _ParentChildHistoryScreenState();
}

class _ParentChildHistoryScreenState extends State<ParentChildHistoryScreen> {
  late Future<List<ChildSchoolRecord>> future = widget.load();
  int? opening;

  Future<void> _open(int membershipId) async {
    setState(() => opening = membershipId);
    try {
      await widget.onOpenSchool(membershipId);
      if (mounted) Navigator.of(context).popUntil((route) => route.isFirst);
    } catch (_) {
      if (mounted) {
        ScaffoldMessenger.maybeOf(context)?.showSnackBar(const SnackBar(
            content: Text('تعذر فتح سجل هذه المدرسة. حاول مجددًا.')));
      }
    } finally {
      if (mounted) setState(() => opening = null);
    }
  }

  @override
  Widget build(BuildContext context) => Scaffold(
        appBar: AppBar(title: const Text('السجل الدراسي')),
        body: SafeArea(
          child: FutureBuilder<List<ChildSchoolRecord>>(
            future: future,
            builder: (context, snapshot) {
              if (snapshot.connectionState != ConnectionState.done) {
                return const Center(child: CircularProgressIndicator());
              }
              if (snapshot.hasError) {
                return Center(
                  child: Column(mainAxisSize: MainAxisSize.min, children: [
                    const Text('تعذر تحميل السجل الدراسي.'),
                    TextButton(
                      onPressed: () => setState(() => future = widget.load()),
                      child: const Text('إعادة المحاولة'),
                    ),
                  ]),
                );
              }
              final schools = snapshot.data ?? const [];
              return ListView(
                padding: const EdgeInsets.all(16),
                children: [
                  Text(widget.childName,
                      style: Theme.of(context)
                          .textTheme
                          .titleLarge
                          ?.copyWith(fontWeight: FontWeight.w800)),
                  const SizedBox(height: 4),
                  const Text(
                      'المدارس التي درس فيها ابنك. سجل المدرسة السابقة متاح للعرض فقط.'),
                  const SizedBox(height: 12),
                  if (schools.isEmpty)
                    const Padding(
                      padding: EdgeInsets.all(24),
                      child: Text('لا يوجد سجل دراسي متاح.',
                          textAlign: TextAlign.center),
                    ),
                  for (final school in schools)
                    Card(
                      child: Padding(
                        padding: const EdgeInsets.all(14),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Row(children: [
                              Icon(
                                  school.isCurrent
                                      ? Icons.school
                                      : Icons.history_edu_outlined,
                                  color: school.isCurrent
                                      ? Theme.of(context).colorScheme.primary
                                      : Colors.grey),
                              const SizedBox(width: 8),
                              Expanded(
                                child: Text(school.schoolName,
                                    style: const TextStyle(
                                        fontWeight: FontWeight.w700)),
                              ),
                              Chip(
                                label: Text(school.isCurrent
                                    ? 'المدرسة الحالية'
                                    : 'مدرسة سابقة'),
                                visualDensity: VisualDensity.compact,
                              ),
                            ]),
                            const SizedBox(height: 6),
                            Text('الأعوام: ${school.years.join('، ')}'),
                            if (school.membershipId != null &&
                                school.membershipId !=
                                    widget.currentMembershipId) ...[
                              const SizedBox(height: 8),
                              Align(
                                alignment: AlignmentDirectional.centerEnd,
                                child: OutlinedButton.icon(
                                  onPressed: opening == null
                                      ? () => _open(school.membershipId!)
                                      : null,
                                  icon: opening == school.membershipId
                                      ? const SizedBox.square(
                                          dimension: 16,
                                          child: CircularProgressIndicator(
                                              strokeWidth: 2))
                                      : const Icon(Icons.open_in_new),
                                  label: Text(school.readOnly
                                      ? 'عرض سجل هذه المدرسة (للقراءة فقط)'
                                      : 'فتح هذه المدرسة'),
                                ),
                              ),
                            ],
                          ],
                        ),
                      ),
                    ),
                ],
              );
            },
          ),
        ),
      );
}
