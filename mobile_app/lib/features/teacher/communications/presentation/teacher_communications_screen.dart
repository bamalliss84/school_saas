import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../../core/errors/app_failure.dart';
import '../../../../core/local_database/app_database.dart';
import '../../students/domain/teacher_students_models.dart';
import '../../students/presentation/teacher_students_controller.dart';
import '../domain/teacher_communication_models.dart';
import 'teacher_communications_controller.dart';

class TeacherCommunicationsScreen extends ConsumerStatefulWidget {
  const TeacherCommunicationsScreen({
    super.key,
    required this.scope,
    required this.historical,
    required this.initialTab,
    required this.onBack,
  });

  final CacheScope scope;
  final bool historical;
  final int initialTab;
  final VoidCallback onBack;

  @override
  ConsumerState<TeacherCommunicationsScreen> createState() =>
      _TeacherCommunicationsScreenState();
}

class _TeacherCommunicationsScreenState
    extends ConsumerState<TeacherCommunicationsScreen> {
  late int tab;

  @override
  void initState() {
    super.initState();
    tab = widget.initialTab.clamp(0, 2);
  }

  @override
  Widget build(BuildContext context) => Column(
        children: [
          Padding(
            padding: const EdgeInsets.fromLTRB(8, 10, 16, 8),
            child: Row(
              children: [
                IconButton(
                  onPressed: widget.onBack,
                  icon: const Icon(Icons.arrow_back),
                ),
                const Expanded(
                  child: Text(
                    'التواصل',
                    style: TextStyle(fontSize: 22, fontWeight: FontWeight.w800),
                  ),
                ),
              ],
            ),
          ),
          if (widget.historical)
            const Padding(
              padding: EdgeInsets.symmetric(horizontal: 16, vertical: 4),
              child: _Notice(
                text: 'السجل الدراسي السابق للعرض فقط. تتاح علامات القراءة الشخصية.',
              ),
            ),
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 12),
            child: SegmentedButton<int>(
              segments: const [
                ButtonSegment(value: 0, label: Text('الإشعارات')),
                ButtonSegment(value: 1, label: Text('الإعلانات')),
                ButtonSegment(value: 2, label: Text('الرسائل')),
              ],
              selected: {tab},
              showSelectedIcon: false,
              onSelectionChanged: (value) => setState(() => tab = value.first),
            ),
          ),
          const SizedBox(height: 4),
          Expanded(
            child: IndexedStack(
              index: tab,
              children: [
                _NotificationsTab(scope: widget.scope),
                _AnnouncementsTab(
                  scope: widget.scope,
                  historical: widget.historical,
                ),
                _ConversationsTab(
                  scope: widget.scope,
                  historical: widget.historical,
                ),
              ],
            ),
          ),
        ],
      );
}

class _NotificationsTab extends ConsumerWidget {
  const _NotificationsTab({required this.scope});
  final CacheScope scope;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final state = ref.watch(teacherNotificationsProvider(scope));
    final controller = ref.read(teacherNotificationsProvider(scope).notifier);
    return state.when(
      loading: () => const Center(child: CircularProgressIndicator()),
      error: (error, _) => _ErrorState(
        message: _message(error),
        retry: controller.load,
      ),
      data: (items) {
        if (items.isEmpty) {
          return _RefreshableEmpty(
            message: 'لا توجد إشعارات',
            onRefresh: controller.load,
          );
        }
        return RefreshIndicator(
          onRefresh: controller.load,
          child: ListView(
            padding: const EdgeInsets.all(16),
            children: [
              if (items.any((item) => !item.isRead))
                Align(
                  alignment: AlignmentDirectional.centerEnd,
                  child: TextButton.icon(
                    onPressed: () => _markAllNotifications(context, controller),
                    icon: const Icon(Icons.done_all),
                    label: const Text('تحديد الكل كمقروء'),
                  ),
                ),
              for (final item in items) ...[
                Card(
                  child: ListTile(
                    leading: Badge(
                      isLabelVisible: !item.isRead,
                      child: const Icon(Icons.notifications_outlined),
                    ),
                    title: Text(
                      item.title,
                      style: TextStyle(
                        fontWeight:
                            item.isRead ? FontWeight.w500 : FontWeight.w800,
                      ),
                    ),
                    subtitle: Text(
                      item.body,
                      maxLines: 2,
                      overflow: TextOverflow.ellipsis,
                    ),
                    trailing: const Icon(Icons.chevron_left),
                    onTap: () => _openNotification(context, ref, scope, item),
                  ),
                ),
                const SizedBox(height: 8),
              ],
            ],
          ),
        );
      },
    );
  }

  Future<void> _markAllNotifications(
    BuildContext context,
    TeacherNotificationsController controller,
  ) async {
    try {
      final count = await controller.markAllRead();
      if (context.mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('تم تحديث $count إشعارًا.')),
        );
      }
    } catch (error) {
      if (context.mounted) _showError(context, error);
    }
  }
}

class _AnnouncementsTab extends ConsumerWidget {
  const _AnnouncementsTab({required this.scope, required this.historical});
  final CacheScope scope;
  final bool historical;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final state = ref.watch(teacherAnnouncementsProvider(scope));
    final controller = ref.read(teacherAnnouncementsProvider(scope).notifier);
    return Stack(
      children: [
        state.when(
          loading: () => const Center(child: CircularProgressIndicator()),
          error: (error, _) => _ErrorState(
            message: _message(error),
            retry: controller.load,
          ),
          data: (items) {
            if (items.isEmpty) {
              return _RefreshableEmpty(
                message: 'لا توجد إعلانات',
                onRefresh: controller.load,
              );
            }
            return RefreshIndicator(
              onRefresh: controller.load,
              child: ListView.separated(
                padding: EdgeInsets.fromLTRB(16, 16, 16, historical ? 16 : 88),
                itemCount: items.length,
                separatorBuilder: (_, __) => const SizedBox(height: 8),
                itemBuilder: (context, index) {
                  final item = items[index];
                  return Card(
                    child: ListTile(
                      leading: Badge(
                        isLabelVisible: item.hasReceipt && !item.isRead,
                        child: const Icon(Icons.campaign_outlined),
                      ),
                      title: Text(
                        item.title,
                        style: TextStyle(
                          fontWeight: item.hasReceipt && !item.isRead
                              ? FontWeight.w800
                              : FontWeight.w600,
                        ),
                      ),
                      subtitle: Text(
                        '${_announcementStatus(item.status)} · ${item.body}',
                        maxLines: 2,
                        overflow: TextOverflow.ellipsis,
                      ),
                      trailing: const Icon(Icons.chevron_left),
                      onTap: () => _openAnnouncement(context, ref, item),
                    ),
                  );
                },
              ),
            );
          },
        ),
        if (!historical)
          PositionedDirectional(
            start: 16,
            bottom: 16,
            child: FloatingActionButton.extended(
              heroTag: 'teacher-announcement-create',
              onPressed: () => _editAnnouncement(context, ref),
              icon: const Icon(Icons.add),
              label: const Text('إعلان جديد'),
            ),
          ),
      ],
    );
  }

  Future<void> _openAnnouncement(
    BuildContext context,
    WidgetRef ref,
    TeacherAnnouncement item,
  ) async {
    var canonical = item;
    if (item.hasReceipt && !item.isRead) {
      try {
        canonical = await ref
            .read(teacherAnnouncementsProvider(scope).notifier)
            .markRead(item.id);
      } catch (error) {
        if (context.mounted) _showError(context, error);
      }
    }
    if (!context.mounted) return;
    await Navigator.of(context).push<void>(
      MaterialPageRoute(
        builder: (_) => _AnnouncementDetailScreen(
          scope: scope,
          historical: historical,
          initial: canonical,
        ),
      ),
    );
  }

  Future<void> _editAnnouncement(
    BuildContext context,
    WidgetRef ref, [
    TeacherAnnouncement? item,
  ]) async {
    await Navigator.of(context).push<TeacherAnnouncement>(
      MaterialPageRoute(
        builder: (_) => _AnnouncementEditor(scope: scope, initial: item),
      ),
    );
  }
}

class _ConversationsTab extends ConsumerWidget {
  const _ConversationsTab({required this.scope, required this.historical});
  final CacheScope scope;
  final bool historical;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final state = ref.watch(teacherConversationsProvider(scope));
    final controller = ref.read(teacherConversationsProvider(scope).notifier);
    return Stack(
      children: [
        state.when(
          loading: () => const Center(child: CircularProgressIndicator()),
          error: (error, _) => _ErrorState(
            message: _message(error),
            retry: controller.load,
          ),
          data: (items) {
            if (items.isEmpty) {
              return _RefreshableEmpty(
                message: 'لا توجد محادثات متاحة',
                onRefresh: controller.load,
              );
            }
            return RefreshIndicator(
              onRefresh: controller.load,
              child: ListView.separated(
                padding: EdgeInsets.fromLTRB(16, 16, 16, historical ? 16 : 88),
                itemCount: items.length,
                separatorBuilder: (_, __) => const SizedBox(height: 8),
                itemBuilder: (context, index) {
                  final item = items[index];
                  return Card(
                    child: ListTile(
                      leading: Badge(
                        isLabelVisible: item.unreadCount > 0,
                        label: Text('${item.unreadCount}'),
                        child: const Icon(Icons.chat_bubble_outline),
                      ),
                      title: Text(item.subject),
                      subtitle: Text(
                        item.preview,
                        maxLines: 2,
                        overflow: TextOverflow.ellipsis,
                      ),
                      trailing: const Icon(Icons.chevron_left),
                      onTap: () => _openConversation(context, ref, item),
                    ),
                  );
                },
              ),
            );
          },
        ),
        if (!historical)
          PositionedDirectional(
            start: 16,
            bottom: 16,
            child: FloatingActionButton.extended(
              heroTag: 'teacher-conversation-create',
              onPressed: () => _startConversation(context, ref),
              icon: const Icon(Icons.chat_outlined),
              label: const Text('محادثة طالب'),
            ),
          ),
      ],
    );
  }

  Future<void> _openConversation(
    BuildContext context,
    WidgetRef ref,
    TeacherConversation item,
  ) async {
    await Navigator.of(context).push<void>(
      MaterialPageRoute(
        builder: (_) => _ConversationScreen(
          scope: scope,
          item: item,
          historical: historical,
        ),
      ),
    );
    ref.invalidate(teacherConversationsProvider(scope));
  }

  Future<void> _startConversation(BuildContext context, WidgetRef ref) async {
    final item = await Navigator.of(context).push<TeacherConversation>(
      MaterialPageRoute(builder: (_) => _NewStudentConversation(scope: scope)),
    );
    if (item == null || !context.mounted) return;
    await _openConversation(context, ref, item);
  }
}

class _AnnouncementDetailScreen extends ConsumerStatefulWidget {
  const _AnnouncementDetailScreen({
    required this.scope,
    required this.historical,
    required this.initial,
  });
  final CacheScope scope;
  final bool historical;
  final TeacherAnnouncement initial;

  @override
  ConsumerState<_AnnouncementDetailScreen> createState() =>
      _AnnouncementDetailScreenState();
}

class _AnnouncementDetailScreenState
    extends ConsumerState<_AnnouncementDetailScreen> {
  late TeacherAnnouncement item = widget.initial;
  bool busy = false;

  @override
  Widget build(BuildContext context) {
    final permissions = item.permissions;
    return Scaffold(
      appBar: AppBar(title: const Text('تفاصيل الإعلان')),
      body: SafeArea(
        child: ListView(
          padding: const EdgeInsets.all(16),
          children: [
            Text(item.title, style: Theme.of(context).textTheme.headlineSmall),
            const SizedBox(height: 8),
            Text(_announcementStatus(item.status)),
            if (item.assignmentSubject.isNotEmpty)
              Text('المادة: ${item.assignmentSubject}'),
            const Divider(height: 32),
            SelectableText(item.body),
            const SizedBox(height: 24),
            if (!widget.historical)
              Wrap(
                spacing: 8,
                runSpacing: 8,
                children: [
                  if (permissions.canEdit)
                    OutlinedButton.icon(
                      onPressed: busy ? null : _edit,
                      icon: const Icon(Icons.edit_outlined),
                      label: const Text('تعديل'),
                    ),
                  if (permissions.canPublish)
                    FilledButton(
                      onPressed: busy ? null : () => _action('publish'),
                      child: const Text('نشر'),
                    ),
                  if (permissions.canClose)
                    OutlinedButton(
                      onPressed: busy ? null : () => _action('close'),
                      child: const Text('إغلاق'),
                    ),
                  if (permissions.canArchive)
                    OutlinedButton(
                      onPressed: busy ? null : () => _action('archive'),
                      child: const Text('أرشفة'),
                    ),
                ],
              ),
          ],
        ),
      ),
    );
  }

  Future<void> _edit() async {
    final updated = await Navigator.of(context).push<TeacherAnnouncement>(
      MaterialPageRoute(
        builder: (_) => _AnnouncementEditor(
          scope: widget.scope,
          initial: item,
        ),
      ),
    );
    if (updated != null && mounted) setState(() => item = updated);
  }

  Future<void> _action(String action) async {
    setState(() => busy = true);
    try {
      final updated = await ref
          .read(teacherAnnouncementsProvider(widget.scope).notifier)
          .action(item.id, action);
      if (mounted) setState(() => item = updated);
    } catch (error) {
      if (mounted) _showError(context, error);
    } finally {
      if (mounted) setState(() => busy = false);
    }
  }
}

class _AnnouncementEditor extends ConsumerStatefulWidget {
  const _AnnouncementEditor({required this.scope, this.initial});
  final CacheScope scope;
  final TeacherAnnouncement? initial;

  @override
  ConsumerState<_AnnouncementEditor> createState() =>
      _AnnouncementEditorState();
}

class _AnnouncementEditorState extends ConsumerState<_AnnouncementEditor> {
  final formKey = GlobalKey<FormState>();
  late final TextEditingController title;
  late final TextEditingController body;
  int? assignmentId;
  late String priority;
  late bool includeParents;
  late bool allowInquiry;
  bool saving = false;

  @override
  void initState() {
    super.initState();
    final initial = widget.initial;
    title = TextEditingController(text: initial?.title ?? '');
    body = TextEditingController(text: initial?.body ?? '');
    assignmentId = initial?.assignmentId;
    priority = initial?.priority ?? 'normal';
    includeParents = initial?.includeParents ?? false;
    allowInquiry = initial?.allowInquiry ?? false;
  }

  @override
  void dispose() {
    title.dispose();
    body.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final assignments = ref.watch(teacherAssignmentsProvider(widget.scope));
    return Scaffold(
      appBar: AppBar(
        title: Text(widget.initial == null ? 'إنشاء إعلان' : 'تعديل الإعلان'),
      ),
      body: SafeArea(
        child: Form(
          key: formKey,
          child: ListView(
            padding: const EdgeInsets.all(16),
            children: [
              assignments.when(
                loading: () => const LinearProgressIndicator(),
                error: (error, _) => _InlineError(
                  message: _message(error),
                  retry: () => ref.invalidate(
                    teacherAssignmentsProvider(widget.scope),
                  ),
                ),
                data: (items) => DropdownButtonFormField<int>(
                  isExpanded: true,
                  value: assignmentId,
                  decoration: const InputDecoration(labelText: 'التكليف'),
                  items: [
                    for (final item in items)
                      DropdownMenuItem(
                        value: item.id,
                        child: Text(
                          _assignmentLabel(item),
                          maxLines: 1,
                          overflow: TextOverflow.ellipsis,
                        ),
                      ),
                  ],
                  onChanged: saving
                      ? null
                      : (value) => setState(() => assignmentId = value),
                  validator: (value) => value == null ? 'اختر التكليف' : null,
                ),
              ),
              const SizedBox(height: 12),
              TextFormField(
                controller: title,
                decoration: const InputDecoration(labelText: 'العنوان'),
                validator: (value) => value == null || value.trim().isEmpty
                    ? 'العنوان مطلوب'
                    : null,
              ),
              const SizedBox(height: 12),
              TextFormField(
                controller: body,
                minLines: 5,
                maxLines: 10,
                decoration: const InputDecoration(labelText: 'نص الإعلان'),
                validator: (value) => value == null || value.trim().isEmpty
                    ? 'نص الإعلان مطلوب'
                    : null,
              ),
              const SizedBox(height: 12),
              DropdownButtonFormField<String>(
                value: priority,
                decoration: const InputDecoration(labelText: 'الأولوية'),
                items: const [
                  DropdownMenuItem(value: 'normal', child: Text('عادية')),
                  DropdownMenuItem(value: 'important', child: Text('مهمة')),
                  DropdownMenuItem(value: 'urgent', child: Text('عاجلة')),
                ],
                onChanged: saving
                    ? null
                    : (value) => setState(() => priority = value ?? 'normal'),
              ),
              SwitchListTile(
                value: includeParents,
                onChanged: saving
                    ? null
                    : (value) => setState(() => includeParents = value),
                title: const Text('إشراك أولياء الأمور'),
              ),
              SwitchListTile(
                value: allowInquiry,
                onChanged: saving
                    ? null
                    : (value) => setState(() => allowInquiry = value),
                title: const Text('السماح بالاستفسار'),
              ),
              const SizedBox(height: 20),
              FilledButton.icon(
                onPressed: saving ? null : _save,
                icon: saving
                    ? const SizedBox.square(
                        dimension: 18,
                        child: CircularProgressIndicator(strokeWidth: 2),
                      )
                    : const Icon(Icons.save_outlined),
                label: const Text('حفظ كمسودة'),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Future<void> _save() async {
    if (formKey.currentState?.validate() != true) return;
    setState(() => saving = true);
    final draft = TeacherAnnouncementDraft(
      title: title.text.trim(),
      body: body.text.trim(),
      assignmentId: assignmentId!,
      priority: priority,
      includeParents: includeParents,
      allowInquiry: allowInquiry,
    );
    try {
      final controller =
          ref.read(teacherAnnouncementsProvider(widget.scope).notifier);
      final saved = widget.initial == null
          ? await controller.create(draft)
          : await controller.update(widget.initial!.id, draft);
      if (mounted) Navigator.pop(context, saved);
    } catch (error) {
      if (mounted) _showError(context, error);
    } finally {
      if (mounted) setState(() => saving = false);
    }
  }
}

class _ConversationScreen extends ConsumerStatefulWidget {
  const _ConversationScreen({
    required this.scope,
    required this.item,
    required this.historical,
  });
  final CacheScope scope;
  final TeacherConversation item;
  final bool historical;

  @override
  ConsumerState<_ConversationScreen> createState() =>
      _ConversationScreenState();
}

class _ConversationScreenState extends ConsumerState<_ConversationScreen> {
  final input = TextEditingController();

  TeacherMessagesQuery get query => (
        scope: widget.scope,
        conversationId: widget.item.id,
      );

  @override
  void dispose() {
    input.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final state = ref.watch(teacherMessagesProvider(query));
    final controller = ref.read(teacherMessagesProvider(query).notifier);
    final writable = !widget.historical && widget.item.canReply;
    return Scaffold(
      appBar: AppBar(title: Text(widget.item.subject)),
      body: SafeArea(
        child: Column(
          children: [
            if (state.failure != null && state.items.isNotEmpty)
              _Notice(text: _message(state.failure!)),
            Expanded(
              child: state.loading && state.items.isEmpty
                  ? const Center(child: CircularProgressIndicator())
                  : state.failure != null && state.items.isEmpty
                      ? _ErrorState(
                          message: _message(state.failure!),
                          retry: controller.load,
                        )
                      : state.items.isEmpty
                          ? const Center(child: Text('لا توجد رسائل'))
                          : RefreshIndicator(
                              onRefresh: controller.load,
                              child: ListView.builder(
                                padding: const EdgeInsets.all(16),
                                itemCount: state.items.length,
                                itemBuilder: (context, index) {
                                  final message = state.items[index];
                                  final mine = message.senderRole == 'teacher';
                                  return Align(
                                    alignment: mine
                                        ? AlignmentDirectional.centerEnd
                                        : AlignmentDirectional.centerStart,
                                    child: Card(
                                      color: mine
                                          ? const Color(0xffeaf0ff)
                                          : null,
                                      child: Padding(
                                        padding: const EdgeInsets.all(12),
                                        child: Column(
                                          crossAxisAlignment:
                                              CrossAxisAlignment.start,
                                          children: [
                                            Text(
                                              message.senderName,
                                              style: Theme.of(context)
                                                  .textTheme
                                                  .labelSmall,
                                            ),
                                            Text(message.body),
                                          ],
                                        ),
                                      ),
                                    ),
                                  );
                                },
                              ),
                            ),
            ),
            if (writable)
              Padding(
                padding: EdgeInsets.fromLTRB(
                  12,
                  8,
                  12,
                  8 + MediaQuery.viewInsetsOf(context).bottom,
                ),
                child: Row(
                  children: [
                    Expanded(
                      child: TextField(
                        controller: input,
                        minLines: 1,
                        maxLines: 4,
                        decoration:
                            const InputDecoration(hintText: 'اكتب رسالة...'),
                      ),
                    ),
                    IconButton(
                      onPressed: state.sending ? null : _send,
                      icon: state.sending
                          ? const SizedBox.square(
                              dimension: 20,
                              child: CircularProgressIndicator(strokeWidth: 2),
                            )
                          : const Icon(Icons.send),
                    ),
                  ],
                ),
              ),
          ],
        ),
      ),
    );
  }

  Future<void> _send() async {
    final controller = ref.read(teacherMessagesProvider(query).notifier);
    final sent = await controller.send(input.text);
    if (!mounted) return;
    if (sent) {
      input.clear();
      ref.invalidate(teacherConversationsProvider(widget.scope));
    }
  }
}

class _NewStudentConversation extends ConsumerStatefulWidget {
  const _NewStudentConversation({required this.scope});
  final CacheScope scope;

  @override
  ConsumerState<_NewStudentConversation> createState() =>
      _NewStudentConversationState();
}

class _NewStudentConversationState
    extends ConsumerState<_NewStudentConversation> {
  final formKey = GlobalKey<FormState>();
  final subject = TextEditingController();
  int? assignmentId;
  int? studentId;
  bool saving = false;

  @override
  void dispose() {
    subject.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final assignments = ref.watch(teacherAssignmentsProvider(widget.scope));
    final roster = assignmentId == null
        ? null
        : ref.watch(teacherRosterProvider((
            scope: widget.scope,
            assignmentId: assignmentId!,
            date: _today(),
          )));
    return Scaffold(
      appBar: AppBar(title: const Text('محادثة جديدة مع طالب')),
      body: SafeArea(
        child: Form(
          key: formKey,
          child: ListView(
            padding: const EdgeInsets.all(16),
            children: [
              const _Notice(
                text: 'يُختار الطالب من قائمة تكليفاتك وطلاب الشعبة فقط.',
              ),
              const SizedBox(height: 12),
              assignments.when(
                loading: () => const LinearProgressIndicator(),
                error: (error, _) => _InlineError(
                  message: _message(error),
                  retry: () => ref.invalidate(
                    teacherAssignmentsProvider(widget.scope),
                  ),
                ),
                data: (items) => DropdownButtonFormField<int>(
                  isExpanded: true,
                  value: assignmentId,
                  decoration: const InputDecoration(labelText: 'التكليف'),
                  items: [
                    for (final item in items)
                      DropdownMenuItem(
                        value: item.id,
                        child: Text(
                          _assignmentLabel(item),
                          maxLines: 1,
                          overflow: TextOverflow.ellipsis,
                        ),
                      ),
                  ],
                  onChanged: saving
                      ? null
                      : (value) => setState(() {
                            assignmentId = value;
                            studentId = null;
                          }),
                  validator: (value) => value == null ? 'اختر التكليف' : null,
                ),
              ),
              const SizedBox(height: 12),
              if (roster == null)
                const Text('اختر التكليف لعرض طلاب الشعبة.')
              else
                roster.when(
                  loading: () => const LinearProgressIndicator(),
                  error: (error, _) => _InlineError(
                    message: _message(error),
                    retry: () => ref.invalidate(teacherRosterProvider((
                      scope: widget.scope,
                      assignmentId: assignmentId!,
                      date: _today(),
                    ))),
                  ),
                  data: (data) => DropdownButtonFormField<int>(
                    value: studentId,
                    decoration: const InputDecoration(labelText: 'الطالب'),
                    items: [
                      for (final student in data.students)
                        DropdownMenuItem(
                          value: student.id,
                          child: Text(student.fullName),
                        ),
                    ],
                    onChanged: saving
                        ? null
                        : (value) => setState(() => studentId = value),
                    validator: (value) => value == null ? 'اختر الطالب' : null,
                  ),
                ),
              const SizedBox(height: 12),
              TextFormField(
                controller: subject,
                decoration: const InputDecoration(labelText: 'موضوع المحادثة'),
                validator: (value) => value == null || value.trim().isEmpty
                    ? 'موضوع المحادثة مطلوب'
                    : null,
              ),
              const SizedBox(height: 20),
              FilledButton.icon(
                onPressed: saving ? null : _save,
                icon: saving
                    ? const SizedBox.square(
                        dimension: 18,
                        child: CircularProgressIndicator(strokeWidth: 2),
                      )
                    : const Icon(Icons.chat_outlined),
                label: const Text('بدء المحادثة'),
              ),
              const SizedBox(height: 12),
              const Text(
                'بدء محادثة جديدة مع ولي أمر غير متاح في هذه الدفعة.',
                textAlign: TextAlign.center,
              ),
            ],
          ),
        ),
      ),
    );
  }

  Future<void> _save() async {
    if (formKey.currentState?.validate() != true) return;
    setState(() => saving = true);
    try {
      final item = await ref
          .read(teacherConversationsProvider(widget.scope).notifier)
          .start(TeacherStudentConversationDraft(
            assignmentId: assignmentId!,
            studentId: studentId!,
            subject: subject.text.trim(),
          ));
      if (mounted) Navigator.pop(context, item);
    } catch (error) {
      if (mounted) _showError(context, error);
    } finally {
      if (mounted) setState(() => saving = false);
    }
  }
}

class _RefreshableEmpty extends StatelessWidget {
  const _RefreshableEmpty({required this.message, required this.onRefresh});
  final String message;
  final Future<void> Function() onRefresh;

  @override
  Widget build(BuildContext context) => RefreshIndicator(
        onRefresh: onRefresh,
        child: ListView(
          physics: const AlwaysScrollableScrollPhysics(),
          children: [
            SizedBox(height: MediaQuery.sizeOf(context).height * .25),
            Center(child: Text(message)),
          ],
        ),
      );
}

class _ErrorState extends StatelessWidget {
  const _ErrorState({required this.message, required this.retry});
  final String message;
  final Future<void> Function() retry;

  @override
  Widget build(BuildContext context) => Center(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Padding(
              padding: const EdgeInsets.all(16),
              child: Text(message, textAlign: TextAlign.center),
            ),
            TextButton(
              onPressed: retry,
              child: const Text('إعادة المحاولة'),
            ),
          ],
        ),
      );
}

class _InlineError extends StatelessWidget {
  const _InlineError({required this.message, required this.retry});
  final String message;
  final VoidCallback retry;

  @override
  Widget build(BuildContext context) => Row(
        children: [
          Expanded(child: Text(message)),
          TextButton(onPressed: retry, child: const Text('إعادة المحاولة')),
        ],
      );
}

class _Notice extends StatelessWidget {
  const _Notice({required this.text});
  final String text;

  @override
  Widget build(BuildContext context) => DecoratedBox(
        decoration: BoxDecoration(
          color: Theme.of(context).colorScheme.primaryContainer,
          borderRadius: BorderRadius.circular(12),
        ),
        child: Padding(
          padding: const EdgeInsets.all(12),
          child: Text(text),
        ),
      );
}

Future<void> _openNotification(
  BuildContext context,
  WidgetRef ref,
  CacheScope scope,
  TeacherNotification original,
) async {
  var item = original;
  if (!item.isRead) {
    try {
      await ref
          .read(teacherNotificationsProvider(scope).notifier)
          .markRead(item.id);
      item = ref
              .read(teacherNotificationsProvider(scope))
              .asData
              ?.value
              .where((row) => row.id == item.id)
              .firstOrNull ??
          item;
    } catch (error) {
      if (context.mounted) _showError(context, error);
    }
  }
  if (!context.mounted) return;
  await showDialog<void>(
    context: context,
    builder: (context) => AlertDialog(
      title: Text(item.title),
      content: SingleChildScrollView(
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(item.body),
            if (_supportedActionLabel(item.action) case final label?) ...[
              const SizedBox(height: 12),
              Text(label, style: Theme.of(context).textTheme.labelMedium),
            ],
          ],
        ),
      ),
      actions: [
        TextButton(
          onPressed: () => Navigator.pop(context),
          child: const Text('إغلاق'),
        ),
      ],
    ),
  );
}

String? _supportedActionLabel(TeacherNotificationAction? action) {
  if (action == null) return null;
  return switch (action.route) {
    'conversation_detail' => 'مرتبط بمحادثة',
    'announcement_detail' => 'مرتبط بإعلان',
    'homework_detail' => 'مرتبط بواجب',
    _ => null,
  };
}

String _assignmentLabel(TeacherAssignmentSummary item) =>
    '${item.subject.name} · ${item.classroom.name} / ${item.section.name}';

String _announcementStatus(String status) => switch (status) {
      'draft' => 'مسودة',
      'published' => 'منشور',
      'closed' => 'مغلق',
      'archived' => 'مؤرشف',
      _ => status,
    };

String _today() {
  final value = DateTime.now();
  String two(int number) => number.toString().padLeft(2, '0');
  return '${value.year}-${two(value.month)}-${two(value.day)}';
}

void _showError(BuildContext context, Object error) {
  ScaffoldMessenger.of(context).showSnackBar(
    SnackBar(content: Text(_message(error))),
  );
}

String _message(Object error) {
  if (error is AppFailure) return error.message;
  if (error is DioException) {
    return AppFailure.fromResponse(
      error.response?.statusCode,
      error.response?.data,
    ).message;
  }
  return 'تعذر إكمال العملية. حاول مرة أخرى.';
}
