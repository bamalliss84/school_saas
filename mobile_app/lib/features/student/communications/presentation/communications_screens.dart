import 'package:flutter/material.dart';

import '../../../../core/design_system/components.dart';
import '../../../../core/design_system/tokens.dart';
import '../data/communications_repository.dart';
import '../domain/communication_models.dart';

class StudentCommunicationsCenter extends StatefulWidget {
  const StudentCommunicationsCenter({super.key, required this.data, required this.historical, required this.onBack, required this.onOpenNotification, required this.onReadAll, required this.onReadAnnouncement});
  final CommunicationsSnapshot data;
  final bool historical;
  final VoidCallback onBack, onReadAll;
  final ValueChanged<CommunicationNotification> onOpenNotification;
  final ValueChanged<int> onReadAnnouncement;
  @override State<StudentCommunicationsCenter> createState() => _StudentCommunicationsCenterState();
}

class _StudentCommunicationsCenterState extends State<StudentCommunicationsCenter> {
  int tab = 0;
  bool unreadOnly = false;
  @override
  Widget build(BuildContext context) {
    final notifications = unreadOnly ? widget.data.notifications.where((e) => !e.isRead).toList() : widget.data.notifications;
    return ListView(padding: const EdgeInsets.all(AppSpacing.x4), children: [
      Row(children: [
        IconButton(onPressed: widget.onBack, icon: const Icon(Icons.arrow_back)),
        Expanded(child: Text(tab == 0 ? 'الإشعارات' : 'الإعلانات', style: Theme.of(context).textTheme.titleLarge)),
      ]),
      SegmentedButton<int>(
        segments: const [ButtonSegment(value: 0, label: Text('الإشعارات')), ButtonSegment(value: 1, label: Text('الإعلانات'))],
        selected: {tab}, onSelectionChanged: (value) => setState(() => tab = value.first),
      ),
      if (widget.data.offline) const OfflineCacheBanner(),
      if (widget.historical) const StatusChip(label: 'للعرض فقط'),
      if (tab == 0) ...[
        Row(children: [
          FilterChip(label: const Text('غير المقروءة'), selected: unreadOnly, onSelected: (v) => setState(() => unreadOnly = v)),
          const Spacer(),
          TextButton(onPressed: widget.historical ? null : widget.onReadAll, child: const Text('تحديد الكل كمقروء')),
        ]),
        if (notifications.isEmpty) const SizedBox(height: 240, child: AppEmptyState(message: 'لا توجد إشعارات')),
        ...notifications.map((item) => Card(child: ListTile(
          leading: Icon(_notificationIcon(item.type)), title: Text(item.title),
          subtitle: Text(item.body, maxLines: 3, overflow: TextOverflow.ellipsis),
          trailing: item.isRead ? null : const Icon(Icons.circle, size: 10),
          onTap: widget.historical ? null : () => widget.onOpenNotification(item),
        ))),
      ],
      if (tab == 1) ...[
        if (widget.data.announcements.isEmpty) const SizedBox(height: 240, child: AppEmptyState(message: 'لا توجد إعلانات')),
        ...widget.data.announcements.map((item) => Card(child: ExpansionTile(
          leading: const Icon(Icons.campaign_outlined), title: Text(item.title),
          subtitle: Text(item.priority == 'high' ? 'مهم' : 'إعلان مدرسي'),
          onExpansionChanged: (open) { if (open && !item.isRead && !widget.historical) widget.onReadAnnouncement(item.id); },
          children: [
            Padding(padding: const EdgeInsets.all(AppSpacing.x4), child: Align(alignment: AlignmentDirectional.centerStart, child: Text(item.body))),
            if (item.attachments.isNotEmpty) ListTile(leading: const Icon(Icons.attach_file), title: Text('المرفقات (${item.attachments.length})')),
          ],
        ))),
      ],
      const SizedBox(height: 20), LastUpdatedLabel(value: widget.data.lastUpdated.toLocal()),
    ]);
  }
}

IconData _notificationIcon(String type) => switch (type) {
  'homework_published' || 'homework_graded' || 'homework_returned' => Icons.assignment_outlined,
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
  });

  final SchoolAnnouncement item;
  final bool historical;
  final VoidCallback onBack;

  @override
  Widget build(BuildContext context) => ListView(
        padding: const EdgeInsets.all(AppSpacing.x4),
        children: [
          Row(children: [
            IconButton(onPressed: onBack, icon: const Icon(Icons.arrow_back)),
            Expanded(
              child: Text('الإعلان', style: Theme.of(context).textTheme.titleLarge),
            ),
            if (historical) const StatusChip(label: 'للعرض فقط'),
          ]),
          Card(
            child: Padding(
              padding: const EdgeInsets.all(AppSpacing.x4),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(item.title, style: Theme.of(context).textTheme.titleMedium),
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
                  ],
                ],
              ),
            ),
          ),
        ],
      );
}

class StudentConversationsScreen extends StatelessWidget {
  const StudentConversationsScreen({super.key, required this.items, required this.offline, required this.historical, required this.onOpen, required this.onSupport});
  final List<ConversationSummary> items;
  final bool offline, historical;
  final ValueChanged<ConversationSummary> onOpen;
  final VoidCallback onSupport;
  @override Widget build(BuildContext context) => ListView(padding: const EdgeInsets.all(AppSpacing.x4), children: [
    Row(children: [
      Expanded(child: Text('الرسائل', style: Theme.of(context).textTheme.titleLarge)),
      OutlinedButton.icon(onPressed: historical || offline ? null : onSupport, icon: const Icon(Icons.school_outlined), label: const Text('التواصل مع المدرسة')),
    ]),
    if (offline) const OfflineCacheBanner(), if (historical) const StatusChip(label: 'للعرض فقط'),
    if (items.isEmpty) const SizedBox(height: 300, child: AppEmptyState(message: 'لا توجد محادثات')),
    ...items.map((item) => Card(child: ListTile(
      leading: CircleAvatar(child: item.unread > 0 ? Text('${item.unread}') : const Icon(Icons.chat_bubble_outline)),
      title: Text(item.subject, maxLines: 1, overflow: TextOverflow.ellipsis),
      subtitle: Text([if (item.participants.isNotEmpty) item.participants.join('، '), item.preview].where((e) => e.isNotEmpty).join('\n'), maxLines: 2, overflow: TextOverflow.ellipsis),
      onTap: () => onOpen(item),
    ))),
  ]);
}

class ConversationDetailScreen extends StatefulWidget {
  const ConversationDetailScreen({super.key, required this.conversation, required this.messages, required this.historical, required this.offline, required this.onBack, required this.onSend});
  final ConversationSummary conversation;
  final List<ConversationMessage> messages;
  final bool historical, offline;
  final VoidCallback onBack;
  final ValueChanged<String> onSend;
  @override State<ConversationDetailScreen> createState() => _ConversationDetailScreenState();
}
class _ConversationDetailScreenState extends State<ConversationDetailScreen> {
  final controller = TextEditingController();
  @override void dispose() { controller.dispose(); super.dispose(); }
  @override Widget build(BuildContext context) {
    final canSend = widget.conversation.canReply && !widget.historical && !widget.offline;
    return Column(children: [
      Padding(padding: const EdgeInsets.all(AppSpacing.x3), child: Row(children: [
        IconButton(onPressed: widget.onBack, icon: const Icon(Icons.arrow_back)),
        Expanded(child: Text(widget.conversation.subject, style: Theme.of(context).textTheme.titleMedium)),
        if (widget.historical) const Chip(label: Text('للعرض فقط')),
      ])),
      Expanded(child: widget.messages.isEmpty ? const AppEmptyState(message: 'لا توجد رسائل') : ListView(
        padding: const EdgeInsets.all(AppSpacing.x4),
        children: widget.messages.map((message) => Align(
          alignment: message.senderRole == 'student' ? AlignmentDirectional.centerEnd : AlignmentDirectional.centerStart,
          child: Card(child: Padding(padding: const EdgeInsets.all(AppSpacing.x3), child: ConstrainedBox(
            constraints: const BoxConstraints(maxWidth: 300),
            child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
              Text(message.sender, style: Theme.of(context).textTheme.labelSmall), Text(message.body),
              if (message.attachmentsCount > 0) Text('📎 ${message.attachmentsCount}'),
            ]),
          ))),
        )).toList(),
      )),
      SafeArea(top: false, child: Padding(padding: const EdgeInsets.all(AppSpacing.x3), child: Row(children: [
        Expanded(child: TextField(controller: controller, enabled: canSend, decoration: InputDecoration(hintText: widget.offline ? 'يتطلب الإرسال اتصالاً بالإنترنت' : 'اكتب رسالتك...'))),
        IconButton(onPressed: canSend ? () { final text = controller.text; controller.clear(); widget.onSend(text); } : null, icon: const Icon(Icons.send)),
      ]))),
    ]);
  }
}

class SchoolSupportSheet extends StatefulWidget {
  const SchoolSupportSheet({super.key, required this.onSubmit});
  final Future<void> Function(String, String, String) onSubmit;
  @override State<SchoolSupportSheet> createState() => _SchoolSupportSheetState();
}
class _SchoolSupportSheetState extends State<SchoolSupportSheet> {
  String category = 'academic_inquiry';
  final subject = TextEditingController(), message = TextEditingController();
  bool busy = false;
  @override void dispose() { subject.dispose(); message.dispose(); super.dispose(); }
  @override Widget build(BuildContext context) => Padding(
    padding: EdgeInsets.only(left: 16, right: 16, top: 16, bottom: MediaQuery.viewInsetsOf(context).bottom + 16),
    child: SingleChildScrollView(child: Column(mainAxisSize: MainAxisSize.min, children: [
      Text('التواصل مع المدرسة', style: Theme.of(context).textTheme.titleLarge),
      DropdownButtonFormField<String>(
        value: category,
        items: const {'academic_inquiry':'استفسار دراسي','absence_excuse':'عذر غياب','profile_update':'تحديث بيانات','technical_issue':'مشكلة تقنية','complaint':'شكوى','other':'أخرى'}.entries.map((e) => DropdownMenuItem(value: e.key, child: Text(e.value))).toList(),
        onChanged: (value) => setState(() => category = value ?? category), decoration: const InputDecoration(labelText: 'نوع الطلب'),
      ),
      TextField(controller: subject, decoration: const InputDecoration(labelText: 'العنوان')),
      TextField(controller: message, maxLines: 4, decoration: const InputDecoration(labelText: 'وصف الطلب')),
      const SizedBox(height: 12),
      AppPrimaryButton(label: busy ? 'جاري الإرسال...' : 'إرسال الطلب', onPressed: busy ? null : () async {
        if (subject.text.trim().isEmpty || message.text.trim().isEmpty) return;
        final navigator = Navigator.of(context);
        setState(() => busy = true);
        try {
          await widget.onSubmit(
            category,
            subject.text.trim(),
            message.text.trim(),
          );
          if (!mounted) return;
          navigator.pop();
        } finally {
          if (mounted) setState(() => busy = false);
        }
      }),
    ])),
  );
}
