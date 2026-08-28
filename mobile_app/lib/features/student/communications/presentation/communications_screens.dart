import 'package:flutter/material.dart';
import 'package:file_selector/file_selector.dart';

import '../../../../core/design_system/components.dart';
import '../../../../core/design_system/tokens.dart';
import '../data/communications_repository.dart';
import '../domain/communication_models.dart';

class StudentCommunicationsCenter extends StatefulWidget {
  const StudentCommunicationsCenter(
      {super.key,
      required this.data,
      required this.historical,
      required this.onBack,
      required this.onOpenNotification,
      required this.onReadAll,
      required this.onReadAnnouncement,
      required this.onInquireAnnouncement});
  final CommunicationsSnapshot data;
  final bool historical;
  final VoidCallback onBack, onReadAll;
  final ValueChanged<CommunicationNotification> onOpenNotification;
  final ValueChanged<int> onReadAnnouncement;
  final Future<void> Function(SchoolAnnouncement) onInquireAnnouncement;
  @override
  State<StudentCommunicationsCenter> createState() =>
      _StudentCommunicationsCenterState();
}

class _StudentCommunicationsCenterState
    extends State<StudentCommunicationsCenter> {
  int tab = 0;
  bool unreadOnly = false;
  @override
  Widget build(BuildContext context) {
    final notifications = unreadOnly
        ? widget.data.notifications.where((e) => !e.isRead).toList()
        : widget.data.notifications;
    return ListView(padding: const EdgeInsets.all(AppSpacing.x4), children: [
      Row(children: [
        IconButton(
            onPressed: widget.onBack, icon: const Icon(Icons.arrow_back)),
        Expanded(
            child: Text(tab == 0 ? 'الإشعارات' : 'الإعلانات',
                style: Theme.of(context).textTheme.titleLarge)),
      ]),
      SegmentedButton<int>(
        segments: const [
          ButtonSegment(value: 0, label: Text('الإشعارات')),
          ButtonSegment(value: 1, label: Text('الإعلانات'))
        ],
        selected: {tab},
        onSelectionChanged: (value) => setState(() => tab = value.first),
      ),
      if (widget.data.offline) const OfflineCacheBanner(),
      if (widget.historical) const StatusChip(label: 'للعرض فقط'),
      if (tab == 0) ...[
        Row(children: [
          FilterChip(
              label: const Text('غير المقروءة'),
              selected: unreadOnly,
              onSelected: (v) => setState(() => unreadOnly = v)),
          const Spacer(),
          TextButton(
              onPressed: widget.historical ? null : widget.onReadAll,
              child: const Text('تحديد الكل كمقروء')),
        ]),
        if (notifications.isEmpty)
          const SizedBox(
              height: 240, child: AppEmptyState(message: 'لا توجد إشعارات')),
        ...notifications.map((item) => Card(
                child: ListTile(
              leading: Icon(_notificationIcon(item.type)),
              title: Text(item.title),
              subtitle:
                  Text(item.body, maxLines: 3, overflow: TextOverflow.ellipsis),
              trailing: item.isRead ? null : const Icon(Icons.circle, size: 10),
              onTap: () => widget.onOpenNotification(item),
            ))),
      ],
      if (tab == 1) ...[
        if (widget.data.announcements.isEmpty)
          const SizedBox(
              height: 240, child: AppEmptyState(message: 'لا توجد إعلانات')),
        ...widget.data.announcements.map((item) => Card(
                child: ExpansionTile(
              leading: const Icon(Icons.campaign_outlined),
              title: Text(item.title),
              subtitle: Text(item.priority == 'high' ? 'مهم' : 'إعلان مدرسي'),
              onExpansionChanged: (open) {
                if (open && !item.isRead && !widget.historical) {
                  widget.onReadAnnouncement(item.id);
                }
              },
              children: [
                Padding(
                    padding: const EdgeInsets.all(AppSpacing.x4),
                    child: Align(
                        alignment: AlignmentDirectional.centerStart,
                        child: Text(item.body))),
                if (item.attachments.isNotEmpty)
                  ListTile(
                      leading: const Icon(Icons.attach_file),
                      title: Text('المرفقات (${item.attachments.length})')),
                if (item.canInquire &&
                    !widget.historical &&
                    !widget.data.offline)
                  Padding(
                    padding: const EdgeInsets.all(AppSpacing.x3),
                    child: OutlinedButton(
                      onPressed: () => widget.onInquireAnnouncement(item),
                      child: const Text('لدي استفسار'),
                    ),
                  ),
              ],
            ))),
      ],
      const SizedBox(height: 20),
      LastUpdatedLabel(value: widget.data.lastUpdated.toLocal()),
    ]);
  }
}

IconData _notificationIcon(String type) => switch (type) {
      'homework_published' ||
      'homework_graded' ||
      'homework_returned' =>
        Icons.assignment_outlined,
      'result_published' => Icons.bar_chart_outlined,
      'message_received' => Icons.chat_bubble_outline,
      'announcement_published' => Icons.campaign_outlined,
      _ => Icons.notifications_none,
    };

class StudentAnnouncementDetailScreen extends StatelessWidget {
  const StudentAnnouncementDetailScreen({
    super.key,
    required this.item,
    required this.historical,
    required this.onBack,
    this.onInquire,
  });

  final SchoolAnnouncement item;
  final bool historical;
  final VoidCallback onBack;
  final Future<void> Function()? onInquire;

  @override
  Widget build(BuildContext context) => ListView(
        padding: const EdgeInsets.all(AppSpacing.x4),
        children: [
          Row(children: [
            IconButton(onPressed: onBack, icon: const Icon(Icons.arrow_back)),
            Expanded(
              child: Text('الإعلان',
                  style: Theme.of(context).textTheme.titleLarge),
            ),
            if (historical) const StatusChip(label: 'للعرض فقط'),
          ]),
          Card(
            child: Padding(
              padding: const EdgeInsets.all(AppSpacing.x4),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(item.title,
                      style: Theme.of(context).textTheme.titleMedium),
                  const SizedBox(height: AppSpacing.x3),
                  Text(item.body),
                  if (item.publishedAt != null) ...[
                    const SizedBox(height: AppSpacing.x3),
                    Text(
                      'تاريخ النشر: ${item.publishedAt!.toLocal().toString().split('.').first}',
                      style: Theme.of(context).textTheme.bodySmall,
                    ),
                  ],
                  if (item.attachments.isNotEmpty) ...[
                    const Divider(),
                    ListTile(
                      contentPadding: EdgeInsets.zero,
                      leading: const Icon(Icons.attach_file),
                      title: Text('المرفقات (${item.attachments.length})'),
                    ),
                    ...item.attachments.map((attachment) => ListTile(
                          contentPadding: EdgeInsets.zero,
                          leading: const Icon(Icons.insert_drive_file_outlined),
                          title: Text(attachment['original_name']?.toString() ??
                              attachment['name']?.toString() ??
                              'مرفق'),
                          subtitle: Text(
                              attachment['content_type']?.toString() ?? ''),
                        )),
                  ],
                  if (onInquire != null) ...[
                    const SizedBox(height: AppSpacing.x3),
                    SizedBox(
                      width: double.infinity,
                      child: OutlinedButton(
                        onPressed: onInquire,
                        child: const Text('لدي استفسار'),
                      ),
                    ),
                  ],
                ],
              ),
            ),
          ),
        ],
      );
}

class StudentConversationsScreen extends StatelessWidget {
  const StudentConversationsScreen(
      {super.key,
      required this.items,
      required this.offline,
      required this.historical,
      required this.onOpen,
      this.onCreateSupport});
  final List<ConversationSummary> items;
  final bool offline, historical;
  final ValueChanged<ConversationSummary> onOpen;
  final Future<bool> Function(String, String, String, List<XFile>)?
      onCreateSupport;

  Future<void> _openSupportSheet(BuildContext context) async {
    if (offline) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('يتطلب إرسال طلب دعم اتصالاً بالإنترنت.'),
        ),
      );
      return;
    }
    if (historical || onCreateSupport == null) return;
    await showModalBottomSheet<void>(
      context: context,
      isScrollControlled: true,
      useSafeArea: true,
      showDragHandle: true,
      builder: (_) => SchoolSupportSheet(onSubmit: onCreateSupport!),
    );
  }

  @override
  Widget build(BuildContext context) =>
      ListView(padding: const EdgeInsets.all(AppSpacing.x4), children: [
        Padding(
          padding: const EdgeInsets.only(bottom: AppSpacing.x3),
          child: LayoutBuilder(builder: (context, constraints) {
            final action = onCreateSupport == null
                ? null
                : OutlinedButton.icon(
                    onPressed:
                        historical ? null : () => _openSupportSheet(context),
                    icon: const Icon(Icons.support_agent_outlined, size: 18),
                    label: const Text('طلب دعم جديد'),
                    style: OutlinedButton.styleFrom(
                      visualDensity: VisualDensity.compact,
                      tapTargetSize: MaterialTapTargetSize.shrinkWrap,
                    ),
                  );
            final stackHeader = constraints.maxWidth < 360 ||
                MediaQuery.textScalerOf(context).scale(1) > 1.25;
            final title = Text('الرسائل',
                maxLines: 1,
                overflow: TextOverflow.ellipsis,
                style: Theme.of(context).textTheme.titleLarge);
            if (action == null) return title;
            if (stackHeader) {
              return Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  title,
                  const SizedBox(height: AppSpacing.x2),
                  action,
                ],
              );
            }
            return Row(children: [
              Expanded(child: title),
              const SizedBox(width: AppSpacing.x2),
              action,
            ]);
          }),
        ),
        if (offline) const OfflineCacheBanner(),
        if (historical) const StatusChip(label: 'للعرض فقط'),
        if (items.isEmpty)
          SizedBox(
            height: 300,
            child: AppEmptyState(
              message: offline
                  ? 'لا تتوفر رسائل محفوظة دون اتصال'
                  : 'لا توجد محادثات',
            ),
          ),
        ...items.map((item) => Card(
                child: ListTile(
              leading: item.isSchoolSupport
                  ? Badge(
                      isLabelVisible: item.unread > 0,
                      label: Text('${item.unread}'),
                      child: const CircleAvatar(
                          child: Icon(Icons.support_agent_outlined)),
                    )
                  : CircleAvatar(
                      child: item.unread > 0
                          ? Text('${item.unread}')
                          : const Icon(Icons.chat_bubble_outline)),
              title: item.isSchoolSupport
                  ? _SupportConversationContent(item: item)
                  : Text(item.subject,
                      maxLines: 1, overflow: TextOverflow.ellipsis),
              subtitle: item.isSchoolSupport
                  ? null
                  : Text(
                      [
                        if (item.participants.isNotEmpty)
                          item.participants.join('، '),
                        item.preview
                      ].where((value) => value.isNotEmpty).join('\n'),
                      maxLines: 2,
                      overflow: TextOverflow.ellipsis),
              onTap: () => onOpen(item),
            ))),
      ]);
}

class _SupportConversationContent extends StatelessWidget {
  const _SupportConversationContent({required this.item});

  final ConversationSummary item;

  @override
  Widget build(BuildContext context) => Padding(
        padding: const EdgeInsets.symmetric(vertical: AppSpacing.x1),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Expanded(
                  child: Text(
                    'الدعم المدرسي',
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                    style: Theme.of(context).textTheme.titleSmall,
                  ),
                ),
                const SizedBox(width: AppSpacing.x2),
                Flexible(
                  child: _SupportStatusBadge(
                    label: _statusLabel(item.status),
                  ),
                ),
              ],
            ),
            if (item.subject.isNotEmpty) ...[
              const SizedBox(height: AppSpacing.x1),
              Text(
                item.subject,
                maxLines: 1,
                overflow: TextOverflow.ellipsis,
                style: Theme.of(context).textTheme.bodyMedium,
              ),
            ],
            if (item.preview.isNotEmpty) ...[
              const SizedBox(height: AppSpacing.x1),
              Text(
                item.preview,
                maxLines: 1,
                overflow: TextOverflow.ellipsis,
                style: Theme.of(context)
                    .textTheme
                    .bodySmall
                    ?.copyWith(color: AppColors.textSecondary),
              ),
            ],
          ],
        ),
      );
}

class _SupportStatusBadge extends StatelessWidget {
  const _SupportStatusBadge({required this.label});

  final String label;

  @override
  Widget build(BuildContext context) => Container(
        padding: const EdgeInsets.symmetric(
          horizontal: AppSpacing.x2,
          vertical: AppSpacing.x1,
        ),
        decoration: BoxDecoration(
          color: AppColors.primary.withOpacity(0.08),
          borderRadius: BorderRadius.circular(AppRadius.chip),
        ),
        child: Text(
          label,
          maxLines: 1,
          overflow: TextOverflow.ellipsis,
          style: Theme.of(context)
              .textTheme
              .labelSmall
              ?.copyWith(color: AppColors.primary),
        ),
      );
}

class ConversationDetailScreen extends StatefulWidget {
  const ConversationDetailScreen(
      {super.key,
      required this.conversation,
      required this.messages,
      required this.historical,
      required this.offline,
      required this.onBack,
      required this.onSend,
      this.loading = false,
      this.error});
  final ConversationSummary conversation;
  final List<ConversationMessage> messages;
  final bool historical, offline;
  final VoidCallback onBack;
  final Future<void> Function(String, List<XFile>) onSend;
  final bool loading;
  final String? error;
  @override
  State<ConversationDetailScreen> createState() =>
      _ConversationDetailScreenState();
}

class _ConversationDetailScreenState extends State<ConversationDetailScreen> {
  final controller = TextEditingController();
  List<XFile> attachments = const [];
  @override
  void dispose() {
    controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final canSend =
        widget.conversation.canReply && !widget.historical && !widget.offline;
    return Column(children: [
      Padding(
          padding: const EdgeInsets.all(AppSpacing.x3),
          child: Row(children: [
            IconButton(
                onPressed: widget.onBack, icon: const Icon(Icons.arrow_back)),
            Expanded(
                child: Text(widget.conversation.subject,
                    style: Theme.of(context).textTheme.titleMedium)),
            if (widget.conversation.isSchoolSupport)
              StatusChip(label: _statusLabel(widget.conversation.status)),
            if (widget.historical) const Chip(label: Text('للعرض فقط')),
          ])),
      Expanded(
          child: widget.loading
              ? const AppSkeletonCard()
              : widget.error != null
                  ? AppErrorState(message: widget.error!)
                  : widget.messages.isEmpty
                      ? AppEmptyState(
                          message: widget.offline
                              ? 'لا تتوفر رسائل محفوظة دون اتصال'
                              : 'لا توجد رسائل')
                      : ListView(
                          padding: const EdgeInsets.all(AppSpacing.x4),
                          children: widget.messages.map((message) {
                            final isStudent = message.senderRole == 'student';
                            final foreground = isStudent
                                ? Colors.white
                                : AppColors.textPrimary;
                            final secondary = isStudent
                                ? const Color(0xc7ffffff)
                                : AppColors.textSecondary;
                            return Align(
                              alignment: message.senderRole == 'student'
                                  ? AlignmentDirectional.centerEnd
                                  : AlignmentDirectional.centerStart,
                              child: Container(
                                  margin: const EdgeInsets.only(
                                      bottom: AppSpacing.x3),
                                  decoration: BoxDecoration(
                                    color: isStudent ? null : AppColors.surface,
                                    gradient: isStudent
                                        ? const LinearGradient(
                                            colors: [
                                              Color(0xff3157d5),
                                              Color(0xff5f7fe2),
                                            ],
                                            begin: AlignmentDirectional
                                                .centerStart,
                                            end: AlignmentDirectional.centerEnd,
                                          )
                                        : null,
                                    borderRadius: BorderRadius.circular(14),
                                    border: isStudent
                                        ? null
                                        : Border.all(color: AppColors.divider),
                                    boxShadow: const [
                                      BoxShadow(
                                        color: Color(0x12000000),
                                        blurRadius: 8,
                                        offset: Offset(0, 2),
                                      ),
                                    ],
                                  ),
                                  clipBehavior: Clip.antiAlias,
                                  child: Padding(
                                      padding:
                                          const EdgeInsets.all(AppSpacing.x3),
                                      child: ConstrainedBox(
                                        constraints:
                                            const BoxConstraints(maxWidth: 300),
                                        child: Column(
                                            crossAxisAlignment:
                                                CrossAxisAlignment.start,
                                            children: [
                                              Text(message.sender,
                                                  style: Theme.of(context)
                                                      .textTheme
                                                      .labelSmall
                                                      ?.copyWith(
                                                          color: secondary)),
                                              Text(message.body,
                                                  style: TextStyle(
                                                      color: foreground)),
                                              const SizedBox(height: 4),
                                              Text(
                                                  _timeLabel(message.createdAt),
                                                  style: Theme.of(context)
                                                      .textTheme
                                                      .labelSmall
                                                      ?.copyWith(
                                                          color: secondary)),
                                              if (message.attachmentsCount > 0)
                                                Container(
                                                  margin: const EdgeInsets.only(
                                                      top: AppSpacing.x2),
                                                  padding: const EdgeInsets
                                                      .symmetric(
                                                      horizontal: AppSpacing.x2,
                                                      vertical: AppSpacing.x1),
                                                  decoration: BoxDecoration(
                                                    color: isStudent
                                                        ? const Color(
                                                            0x29ffffff)
                                                        : AppColors.background,
                                                    borderRadius:
                                                        BorderRadius.circular(
                                                            8),
                                                  ),
                                                  child: Text(
                                                    '📎 ${message.attachmentsCount}',
                                                    style: TextStyle(
                                                        color: foreground),
                                                  ),
                                                ),
                                            ]),
                                      ))),
                            );
                          }).toList(),
                        )),
      SafeArea(
          top: false,
          child: Padding(
              padding: const EdgeInsets.all(AppSpacing.x3),
              child: Row(children: [
                IconButton(
                    onPressed: canSend
                        ? () async {
                            final selected = await openFiles();
                            if (mounted) {
                              setState(() => attachments = selected);
                            }
                          }
                        : null,
                    icon: Badge(
                        isLabelVisible: attachments.isNotEmpty,
                        label: Text('${attachments.length}'),
                        child: const Icon(Icons.attach_file))),
                Expanded(
                    child: TextField(
                        controller: controller,
                        enabled: canSend,
                        decoration: InputDecoration(
                            hintText: widget.offline
                                ? 'يتطلب الإرسال اتصالاً بالإنترنت'
                                : 'اكتب رسالتك...'))),
                IconButton(
                    onPressed: canSend
                        ? () async {
                            final text = controller.text;
                            if (text.trim().isEmpty) return;
                            final selected = attachments;
                            await widget.onSend(text, selected);
                            if (!mounted) return;
                            controller.clear();
                            setState(() => attachments = const []);
                          }
                        : null,
                    icon: const Icon(Icons.send)),
              ]))),
    ]);
  }
}

String _statusLabel(String value) => switch (value) {
      'open' => 'مفتوح',
      'in_progress' => 'قيد المعالجة',
      'resolved' => 'تم الحل',
      'closed' => 'مغلق',
      _ => value,
    };

String _timeLabel(DateTime value) {
  final local = value.toLocal();
  final hour = local.hour.toString().padLeft(2, '0');
  final minute = local.minute.toString().padLeft(2, '0');
  return '$hour:$minute';
}

class SchoolSupportSheet extends StatefulWidget {
  const SchoolSupportSheet({super.key, required this.onSubmit});
  final Future<bool> Function(String, String, String, List<XFile>) onSubmit;
  @override
  State<SchoolSupportSheet> createState() => _SchoolSupportSheetState();
}

class _SchoolSupportSheetState extends State<SchoolSupportSheet> {
  String category = 'academic_inquiry';
  final subject = TextEditingController(), message = TextEditingController();
  bool busy = false;
  List<XFile> attachments = const [];

  InputDecoration _fieldDecoration(String label, {bool multiline = false}) =>
      InputDecoration(
        labelText: label,
        floatingLabelBehavior: FloatingLabelBehavior.always,
        alignLabelWithHint: multiline,
        contentPadding: EdgeInsetsDirectional.fromSTEB(
          AppSpacing.x3,
          AppSpacing.x6,
          AppSpacing.x3,
          multiline ? AppSpacing.x4 : AppSpacing.x3,
        ),
      );

  @override
  void dispose() {
    subject.dispose();
    message.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) => Padding(
        padding: EdgeInsets.only(
            left: 16,
            right: 16,
            top: 16,
            bottom: MediaQuery.viewInsetsOf(context).bottom + 16),
        child: SingleChildScrollView(
            keyboardDismissBehavior: ScrollViewKeyboardDismissBehavior.onDrag,
            child: Column(mainAxisSize: MainAxisSize.min, children: [
              Text('التواصل مع المدرسة',
                  style: Theme.of(context).textTheme.titleLarge),
              const SizedBox(height: AppSpacing.x4),
              DropdownButtonFormField<String>(
                value: category,
                isExpanded: true,
                items: const {
                  'academic_inquiry': 'استفسار دراسي',
                  'absence_excuse': 'عذر غياب',
                  'profile_update': 'تحديث بيانات',
                  'technical_issue': 'مشكلة تقنية',
                  'complaint': 'شكوى',
                  'other': 'أخرى'
                }
                    .entries
                    .map((e) => DropdownMenuItem(
                          value: e.key,
                          child: Text(
                            e.value,
                            maxLines: 1,
                            overflow: TextOverflow.ellipsis,
                            textAlign: TextAlign.start,
                          ),
                        ))
                    .toList(),
                onChanged: (value) =>
                    setState(() => category = value ?? category),
                decoration: _fieldDecoration('نوع الطلب'),
              ),
              const SizedBox(height: AppSpacing.x3),
              TextField(
                  controller: subject,
                  textAlign: TextAlign.start,
                  decoration: _fieldDecoration('العنوان')),
              const SizedBox(height: AppSpacing.x3),
              TextField(
                  controller: message,
                  textAlign: TextAlign.start,
                  textAlignVertical: TextAlignVertical.top,
                  minLines: 4,
                  maxLines: 4,
                  decoration: _fieldDecoration('وصف الطلب', multiline: true)),
              ListTile(
                  contentPadding: EdgeInsets.zero,
                  leading: const Icon(Icons.attach_file),
                  title: Text(attachments.isEmpty
                      ? 'إرفاق ملف'
                      : 'المرفقات (${attachments.length})'),
                  onTap: busy
                      ? null
                      : () async {
                          final selected = await openFiles();
                          if (mounted) setState(() => attachments = selected);
                        }),
              const SizedBox(height: 12),
              AppPrimaryButton(
                  label: busy ? 'جاري الإرسال...' : 'إرسال الطلب',
                  onPressed: busy
                      ? null
                      : () async {
                          if (subject.text.trim().isEmpty ||
                              message.text.trim().isEmpty) return;
                          final navigator = Navigator.of(context);
                          final messenger = ScaffoldMessenger.of(context);
                          setState(() => busy = true);
                          try {
                            final uploaded = await widget.onSubmit(
                              category,
                              subject.text.trim(),
                              message.text.trim(),
                              attachments,
                            );
                            if (!mounted) return;
                            navigator.pop();
                            if (!uploaded) {
                              messenger.showSnackBar(
                                const SnackBar(
                                  content: Text(
                                    'تم إرسال الطلب، لكن تعذر رفع المرفق. أعد إرساله داخل المحادثة.',
                                  ),
                                ),
                              );
                            }
                          } finally {
                            if (mounted) setState(() => busy = false);
                          }
                        }),
            ])),
      );
}
