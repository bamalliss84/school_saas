import 'package:flutter/material.dart';
import '../../core/design_system/components.dart';
import '../../core/design_system/tokens.dart';
import '../../core/models/school_context.dart';
import 'student_profile_controller.dart';
import 'student_profile_models.dart';

class StudentMoreScreen extends StatelessWidget {
  const StudentMoreScreen(
      {super.key,
      required this.studentName,
      required this.schoolName,
      required this.canChangeContext,
      required this.onProfile,
      required this.onContext,
      required this.onHistory,
      required this.onAppearance,
      required this.onHelp,
      required this.onAbout,
      required this.onLogout});
  final String studentName, schoolName;
  final bool canChangeContext;
  final VoidCallback onProfile,
      onContext,
      onHistory,
      onAppearance,
      onHelp,
      onAbout,
      onLogout;
  @override
  Widget build(BuildContext context) =>
      ListView(padding: const EdgeInsets.all(AppSpacing.x4), children: [
        Text('المزيد', style: Theme.of(context).textTheme.headlineMedium),
        const SizedBox(height: AppSpacing.x4),
        AppCard(
            child: ListTile(
          leading: const CircleAvatar(child: Icon(Icons.person_outline)),
          title: Text(studentName.isEmpty ? '—' : studentName,
              maxLines: 2, overflow: TextOverflow.ellipsis),
          subtitle: Text(schoolName.isEmpty ? '—' : schoolName,
              maxLines: 2, overflow: TextOverflow.ellipsis),
          trailing: const Icon(Icons.chevron_left),
          onTap: onProfile,
        )),
        const SizedBox(height: AppSpacing.x3),
        _MoreGroup(children: [
          _MoreTile(
              icon: Icons.person_outline, label: 'ملفي', onTap: onProfile),
          if (canChangeContext)
            _MoreTile(
                icon: Icons.school_outlined,
                label: 'المدرسة والسياق',
                onTap: onContext),
          _MoreTile(
              icon: Icons.history_edu_outlined,
              label: 'السجل الدراسي',
              onTap: onHistory),
        ]),
        const SizedBox(height: AppSpacing.x3),
        _MoreGroup(children: [
          _MoreTile(
              icon: Icons.palette_outlined,
              label: 'المظهر',
              onTap: onAppearance),
          _MoreTile(icon: Icons.help_outline, label: 'المساعدة', onTap: onHelp),
          _MoreTile(
              icon: Icons.info_outline, label: 'حول التطبيق', onTap: onAbout),
        ]),
        const SizedBox(height: AppSpacing.x4),
        OutlinedButton.icon(
            onPressed: onLogout,
            icon: const Icon(Icons.logout),
            label: const Text('تسجيل الخروج')),
      ]);
}

class _MoreGroup extends StatelessWidget {
  const _MoreGroup({required this.children});
  final List<Widget> children;
  @override
  Widget build(BuildContext context) =>
      AppCard(child: Column(children: children));
}

class _MoreTile extends StatelessWidget {
  const _MoreTile(
      {required this.icon, required this.label, required this.onTap});
  final IconData icon;
  final String label;
  final VoidCallback onTap;
  @override
  Widget build(BuildContext context) => ListTile(
        leading: Container(
            padding: const EdgeInsets.all(AppSpacing.x2),
            decoration: BoxDecoration(
                color: AppColors.primary.withOpacity(.08),
                borderRadius: BorderRadius.circular(AppRadius.chip)),
            child: Icon(icon, color: AppColors.primary)),
        title: Text(label),
        trailing: const Icon(Icons.chevron_left),
        onTap: onTap,
      );
}

class StudentProfileScreen extends StatelessWidget {
  const StudentProfileScreen(
      {super.key,
      required this.state,
      required this.contextInfo,
      required this.onBack,
      required this.onRetry});
  final StudentProfileState state;
  final SchoolContext contextInfo;
  final VoidCallback onBack;
  final Future<void> Function() onRetry;
  @override
  Widget build(BuildContext context) => _NestedPage(
      title: 'ملفي',
      onBack: onBack,
      child: _stateBody(state, onRetry, (data) {
        final p = data.profile;
        final historical = contextInfo.isHistorical;
        return ListView(children: [
          if (data.offline) const OfflineCacheBanner(),
          if (historical) const StatusChip(label: 'أرشيف / للقراءة فقط'),
          AppCard(
              child: Column(children: [
            const CircleAvatar(
                radius: 30, child: Icon(Icons.person_outline, size: 32)),
            const SizedBox(height: AppSpacing.x2),
            Text(_safe(p.fullName),
                style: Theme.of(context).textTheme.titleLarge,
                textAlign: TextAlign.center),
            const Text('طالب'),
          ])),
          const SizedBox(height: AppSpacing.x3),
          AppCard(
              child: Column(children: [
            _InfoRow('رقم الطالب', p.studentCode),
            _InfoRow('المدرسة', contextInfo.schoolName),
            _InfoRow('العام الدراسي', contextInfo.academicYearName),
            if (!historical && p.schoolName == contextInfo.schoolName) ...[
              _InfoRow('الصف', p.classroomName),
              _InfoRow('الشعبة', p.sectionName),
            ],
            _InfoRow('الحالة', historical ? 'أرشيف / للقراءة فقط' : 'حالي'),
          ])),
        ]);
      }));
}

class StudentContextScreen extends StatefulWidget {
  const StudentContextScreen(
      {super.key,
      required this.current,
      required this.contexts,
      required this.offline,
      required this.onBack,
      required this.onSelect});
  final SchoolContext current;
  final List<SchoolContext> contexts;
  final bool offline;
  final VoidCallback onBack;
  final Future<void> Function(SchoolContext) onSelect;
  @override
  State<StudentContextScreen> createState() => _StudentContextScreenState();
}

class _StudentContextScreenState extends State<StudentContextScreen> {
  int? busyId;
  String? error;
  Future<void> _select(SchoolContext item) async {
    if (widget.offline || item.membershipId == widget.current.membershipId) {
      return;
    }
    setState(() {
      busyId = item.membershipId;
      error = null;
    });
    try {
      await widget.onSelect(item);
    } catch (_) {
      if (mounted) {
        setState(() => error = 'تعذر تغيير السياق. ما زلت في السياق السابق.');
      }
    } finally {
      if (mounted) setState(() => busyId = null);
    }
  }

  @override
  Widget build(BuildContext context) => _NestedPage(
      title: 'المدرسة والسياق',
      onBack: widget.onBack,
      child: ListView(children: [
        if (widget.offline) const OfflineCacheBanner(),
        if (error != null)
          Text(error!, style: const TextStyle(color: AppColors.error)),
        ...widget.contexts.map((item) => Padding(
            padding: const EdgeInsets.only(bottom: AppSpacing.x2),
            child: AppCard(
                child: ListTile(
              title: Text(item.schoolName,
                  maxLines: 2, overflow: TextOverflow.ellipsis),
              subtitle: Text([
                item.academicYearName ?? '—',
                item.isHistorical ? 'أرشيف / للقراءة فقط' : 'طالب'
              ].join(' • ')),
              leading: item.membershipId == widget.current.membershipId
                  ? const Icon(Icons.check_circle, color: AppColors.success)
                  : const Icon(Icons.school_outlined),
              trailing: busyId == item.membershipId
                  ? const SizedBox.square(
                      dimension: 20,
                      child: CircularProgressIndicator(strokeWidth: 2))
                  : null,
              enabled: !widget.offline && busyId == null,
              onTap: item.membershipId == widget.current.membershipId
                  ? null
                  : () => _select(item),
            )))),
      ]));
}

class StudentAcademicHistoryScreen extends StatelessWidget {
  const StudentAcademicHistoryScreen(
      {super.key,
      required this.state,
      required this.onBack,
      required this.onRetry});
  final StudentProfileState state;
  final VoidCallback onBack;
  final Future<void> Function() onRetry;
  @override
  Widget build(BuildContext context) => _NestedPage(
      title: 'السجل الدراسي',
      onBack: onBack,
      child: _stateBody(
          state,
          onRetry,
          (data) => data.history.isEmpty
              ? const AppEmptyState(message: 'لا يوجد سجل دراسي سابق')
              : ListView(children: [
                  if (data.offline) const OfflineCacheBanner(),
                  ...data.history.map((item) => _HistoryCard(item))
                ])));
}

class _HistoryCard extends StatelessWidget {
  const _HistoryCard(this.item);
  final StudentAcademicHistoryItem item;
  @override
  Widget build(BuildContext context) => Padding(
      padding: const EdgeInsets.only(bottom: AppSpacing.x2),
      child: AppCard(
          child:
              Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        Row(children: [
          Expanded(
              child: Text(_safe(item.schoolName),
                  style: Theme.of(context).textTheme.titleMedium)),
          StatusChip(label: item.isCurrent ? 'حالي' : 'للعرض فقط')
        ]),
        const SizedBox(height: AppSpacing.x2),
        Text(_safe(item.academicYearName)),
        Text([
          'الصف: ${_safe(item.classroomName)}',
          'الشعبة: ${_safe(item.sectionName)}'
        ].join(' • ')),
      ])));
}

class StudentHelpScreen extends StatelessWidget {
  const StudentHelpScreen(
      {super.key, required this.onBack, required this.onSupport});
  final VoidCallback onBack, onSupport;
  @override
  Widget build(BuildContext context) => _NestedPage(
      title: 'المساعدة',
      onBack: onBack,
      child: ListView(children: [
        const AppCard(
            child: Text(
                'يمكنك مراجعة بياناتك والسياق الدراسي، أو التواصل مع مدرستك من مركز الرسائل.')),
        const SizedBox(height: AppSpacing.x3),
        FilledButton.icon(
            onPressed: onSupport,
            icon: const Icon(Icons.support_agent_outlined),
            label: const Text('التواصل مع المدرسة')),
      ]));
}

class StudentAboutScreen extends StatelessWidget {
  const StudentAboutScreen({super.key, required this.onBack});
  final VoidCallback onBack;
  @override
  Widget build(BuildContext context) => _NestedPage(
      title: 'حول التطبيق',
      onBack: onBack,
      child: const AppCard(
          child: Column(children: [
        Icon(Icons.school, size: 52, color: AppColors.primary),
        SizedBox(height: AppSpacing.x3),
        Text('تطبيق المدرسة', style: TextStyle(fontWeight: FontWeight.bold)),
        SizedBox(height: AppSpacing.x2),
        Text('يساعد الطالب على متابعة يومه الدراسي والتواصل مع مدرسته.',
            textAlign: TextAlign.center),
      ])));
}

class _NestedPage extends StatelessWidget {
  const _NestedPage(
      {required this.title, required this.onBack, required this.child});
  final String title;
  final VoidCallback onBack;
  final Widget child;
  @override
  Widget build(BuildContext context) => Padding(
      padding: const EdgeInsets.all(AppSpacing.x4),
      child: Column(children: [
        Row(children: [
          IconButton(onPressed: onBack, icon: const Icon(Icons.arrow_forward)),
          Expanded(
              child:
                  Text(title, style: Theme.of(context).textTheme.headlineSmall))
        ]),
        const SizedBox(height: AppSpacing.x2),
        Expanded(child: child),
      ]));
}

class _InfoRow extends StatelessWidget {
  const _InfoRow(this.label, this.value);
  final String label;
  final String? value;
  @override
  Widget build(BuildContext context) => Padding(
      padding: const EdgeInsets.symmetric(vertical: AppSpacing.x2),
      child: Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
        Expanded(
            child: Text(label,
                style: const TextStyle(color: AppColors.textSecondary))),
        const SizedBox(width: AppSpacing.x2),
        Flexible(child: Text(_safe(value), textAlign: TextAlign.end)),
      ]));
}

Widget _stateBody(StudentProfileState state, Future<void> Function() onRetry,
    Widget Function(dynamic data) ready) {
  if (state is StudentProfileLoading) return const AppSkeletonCard();
  if (state is StudentProfileFailure) {
    return Column(children: [
      Expanded(child: AppErrorState(message: state.message)),
      FilledButton(onPressed: onRetry, child: const Text('إعادة المحاولة')),
    ]);
  }
  return ready((state as StudentProfileReady).data);
}

String _safe(String? value) =>
    value == null || value.trim().isEmpty ? '—' : value;
