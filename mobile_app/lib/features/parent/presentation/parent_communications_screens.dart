import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../../core/design_system/components.dart';
import '../../../../core/local_database/app_database.dart';
import '../data/parent_communications_repository.dart';
import '../domain/parent_communication_models.dart';
import 'parent_communications_controller.dart';

class ParentNotificationsPage extends ConsumerWidget {
  const ParentNotificationsPage({
    super.key,
    required this.scope,
    required this.historical,
  });
  final CacheScope scope;
  final bool historical;

  @override
  Widget build(BuildContext context, WidgetRef ref) => Scaffold(
        appBar: AppBar(title: const Text('الإشعارات')),
        body: ParentNotificationsScreen(
          state: ref.watch(parentNotificationsProvider(scope)),
          historical: historical,
          onRefresh:
              ref.read(parentNotificationsProvider(scope).notifier).refresh,
          onRead: ref.read(parentNotificationsProvider(scope).notifier).read,
          onReadAll:
              ref.read(parentNotificationsProvider(scope).notifier).readAll,
        ),
      );
}

class ParentAnnouncementsPage extends ConsumerWidget {
  const ParentAnnouncementsPage({
    super.key,
    required this.scope,
    required this.historical,
    required this.childId,
  });
  final CacheScope scope;
  final bool historical;
  final int? childId;

  @override
  Widget build(BuildContext context, WidgetRef ref) => Scaffold(
        appBar: AppBar(title: const Text('الإعلانات')),
        body: ParentAnnouncementsScreen(
          state: ref.watch(parentAnnouncementsProvider(scope)),
          historical: historical,
          onRefresh:
              ref.read(parentAnnouncementsProvider(scope).notifier).refresh,
          onRead: ref.read(parentAnnouncementsProvider(scope).notifier).read,
          onOpen: (item) => Navigator.of(context).push(
            MaterialPageRoute<void>(
              builder: (_) => ParentAnnouncementDetailScreen(
                announcement: item,
                historical: historical,
                onInquire: !historical && item.canInquire && childId != null
                    ? () async {
                        final conversation = await ref
                            .read(parentAnnouncementsProvider(scope).notifier)
                            .inquire(item, childId!, historical);
                        if (conversation == null || !context.mounted) return;
                        await Navigator.of(context).push(
                          MaterialPageRoute<void>(
                            builder: (_) => ParentConversationsPage(
                              scope: scope,
                              historical: historical,
                            ),
                          ),
                        );
                      }
                    : null,
              ),
            ),
          ),
        ),
      );
}

class ParentConversationsPage extends ConsumerWidget {
  const ParentConversationsPage({
    super.key,
    required this.scope,
    required this.historical,
  });
  final CacheScope scope;
  final bool historical;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final query = (scope: scope, historical: historical);
    final controller = ref.read(parentConversationsProvider(query).notifier);
    return Scaffold(
      appBar: AppBar(title: const Text('الرسائل')),
      body: ParentConversationsScreen(
        state: ref.watch(parentConversationsProvider(query)),
        historical: historical,
        onRefresh: controller.refresh,
        onCreateSupport: controller.createSupport,
        onOpen: (conversation) async {
          await controller.open(conversation);
          if (context.mounted) {
            await Navigator.of(context).push(
              MaterialPageRoute<void>(
                builder: (_) => ParentConversationPage(query: query),
              ),
            );
          }
        },
      ),
    );
  }
}

class ParentConversationPage extends ConsumerWidget {
  const ParentConversationPage({super.key, required this.query});
  final ParentCommunicationsQuery query;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final state = ref.watch(parentConversationsProvider(query));
    if (state is! ParentConversationsReady || state.selected == null) {
      return const Scaffold(body: Center(child: CircularProgressIndicator()));
    }
    final controller = ref.read(parentConversationsProvider(query).notifier);
    return ParentConversationDetailScreen(
      conversation: state.selected!,
      messages: state.messages,
      historical: query.historical,
      busy: state.busy,
      error: state.detailError,
      draft: state.draft,
      onDraftChanged: controller.setDraft,
      onSend: controller.send,
    );
  }
}

class ParentNotificationsScreen extends StatelessWidget {
  const ParentNotificationsScreen({
    super.key,
    required this.state,
    required this.historical,
    required this.onRefresh,
    required this.onRead,
    required this.onReadAll,
  });
  final ParentNotificationsState state;
  final bool historical;
  final Future<void> Function() onRefresh;
  final Future<void> Function(ParentNotification) onRead;
  final Future<void> Function() onReadAll;

  @override
  Widget build(BuildContext context) {
    if (state is ParentNotificationsLoading) {
      return const Center(child: CircularProgressIndicator());
    }
    if (state case ParentNotificationsFailure(:final message)) {
      return _Failure(message: message, onRetry: onRefresh);
    }
    final ready = state as ParentNotificationsReady;
    return RefreshIndicator(
      onRefresh: onRefresh,
      child: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          _TitleRow(title: 'الإشعارات', historical: historical),
          if (ready.data.offline) const OfflineCacheBanner(),
          if (ready.refreshing) const LinearProgressIndicator(),
          if (ready.data.unreadCount > 0)
            Align(
              alignment: AlignmentDirectional.centerEnd,
              child: TextButton(
                onPressed: onReadAll,
                child: const Text('تعليم الكل كمقروء'),
              ),
            ),
          if (ready.data.items.isEmpty)
            const _Empty(
                icon: Icons.notifications_none, text: 'لا توجد إشعارات')
          else
            for (final item in ready.data.items)
              Card(
                child: ListTile(
                  leading: Icon(item.isRead
                      ? Icons.notifications_none
                      : Icons.notifications_active),
                  title: Text(item.title),
                  subtitle: Text(item.body),
                  trailing: item.isRead
                      ? null
                      : const Icon(Icons.circle, size: 10, color: Colors.blue),
                  onTap: () => onRead(item),
                ),
              ),
        ],
      ),
    );
  }
}

class ParentAnnouncementsScreen extends StatelessWidget {
  const ParentAnnouncementsScreen({
    super.key,
    required this.state,
    required this.historical,
    required this.onRefresh,
    required this.onRead,
    required this.onOpen,
  });
  final ParentAnnouncementsState state;
  final bool historical;
  final Future<void> Function() onRefresh;
  final Future<void> Function(ParentAnnouncement) onRead;
  final ValueChanged<ParentAnnouncement> onOpen;

  @override
  Widget build(BuildContext context) {
    if (state is ParentAnnouncementsLoading) {
      return const Center(child: CircularProgressIndicator());
    }
    if (state case ParentAnnouncementsFailure(:final message)) {
      return _Failure(message: message, onRetry: onRefresh);
    }
    final ready = state as ParentAnnouncementsReady;
    return RefreshIndicator(
      onRefresh: onRefresh,
      child: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          _TitleRow(title: 'الإعلانات', historical: historical),
          if (ready.data.offline) const OfflineCacheBanner(),
          if (ready.refreshing) const LinearProgressIndicator(),
          if (ready.data.items.isEmpty)
            const _Empty(icon: Icons.campaign_outlined, text: 'لا توجد إعلانات')
          else
            for (final item in ready.data.items)
              Card(
                child: ListTile(
                  leading: const Icon(Icons.campaign_outlined),
                  title: Text(item.title),
                  subtitle: Text(item.body,
                      maxLines: 2, overflow: TextOverflow.ellipsis),
                  trailing: item.isRead
                      ? const Icon(Icons.chevron_left)
                      : const Icon(Icons.circle, size: 10, color: Colors.blue),
                  onTap: () {
                    onRead(item);
                    onOpen(item);
                  },
                ),
              ),
        ],
      ),
    );
  }
}

class ParentAnnouncementDetailScreen extends StatelessWidget {
  const ParentAnnouncementDetailScreen({
    super.key,
    required this.announcement,
    required this.historical,
    this.onInquire,
  });
  final ParentAnnouncement announcement;
  final bool historical;
  final Future<void> Function()? onInquire;

  @override
  Widget build(BuildContext context) => Scaffold(
        appBar: AppBar(title: const Text('تفاصيل الإعلان')),
        body: ListView(
          padding: const EdgeInsets.all(16),
          children: [
            _TitleRow(title: announcement.title, historical: historical),
            const SizedBox(height: 16),
            Text(announcement.body),
            if (onInquire != null) ...[
              const SizedBox(height: 20),
              FilledButton.icon(
                onPressed: onInquire,
                icon: const Icon(Icons.forum_outlined),
                label: const Text('استفسار عن الإعلان'),
              ),
            ],
            if (announcement.attachments.isNotEmpty) ...[
              const SizedBox(height: 20),
              Text('المرفقات', style: Theme.of(context).textTheme.titleMedium),
              for (final attachment in announcement.attachments)
                ListTile(
                  leading: const Icon(Icons.attach_file),
                  title: Text(attachment['name']?.toString() ?? 'مرفق'),
                ),
            ],
          ],
        ),
      );
}

class ParentConversationsScreen extends StatelessWidget {
  const ParentConversationsScreen({
    super.key,
    required this.state,
    required this.historical,
    required this.onRefresh,
    required this.onOpen,
    required this.onCreateSupport,
  });
  final ParentConversationsState state;
  final bool historical;
  final Future<void> Function() onRefresh;
  final Future<void> Function(ParentConversation) onOpen;
  final Future<void> Function(String subject, String category) onCreateSupport;

  @override
  Widget build(BuildContext context) {
    if (state is ParentConversationsLoading) {
      return const Center(child: CircularProgressIndicator());
    }
    if (state case ParentConversationsFailure(:final message)) {
      return _Failure(message: message, onRetry: onRefresh);
    }
    final ready = state as ParentConversationsReady;
    return RefreshIndicator(
      onRefresh: onRefresh,
      child: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          _TitleRow(title: 'الرسائل', historical: historical),
          if (ready.data.offline) const OfflineCacheBanner(),
          if (!historical && !ready.data.offline)
            Align(
              alignment: AlignmentDirectional.centerEnd,
              child: OutlinedButton.icon(
                onPressed: () => _supportDialog(context),
                icon: const Icon(Icons.support_agent),
                label: const Text('طلب دعم جديد'),
              ),
            ),
          if (ready.data.items.isEmpty)
            const _Empty(icon: Icons.forum_outlined, text: 'لا توجد محادثات')
          else
            for (final item in ready.data.items)
              Card(
                child: ListTile(
                  leading: const Icon(Icons.forum_outlined),
                  title: Text(item.subject),
                  subtitle: Text(item.preview,
                      maxLines: 1, overflow: TextOverflow.ellipsis),
                  trailing: item.unread > 0
                      ? Badge(label: Text('${item.unread}'))
                      : const Icon(Icons.chevron_left),
                  onTap: () => onOpen(item),
                ),
              ),
        ],
      ),
    );
  }

  Future<void> _supportDialog(BuildContext context) async {
    final controller = TextEditingController();
    final subject = await showDialog<String>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('طلب دعم جديد'),
        content: TextField(
          controller: controller,
          autofocus: true,
          decoration: const InputDecoration(labelText: 'الموضوع'),
        ),
        actions: [
          TextButton(
              onPressed: () => Navigator.pop(context),
              child: const Text('إلغاء')),
          FilledButton(
              onPressed: () => Navigator.pop(context, controller.text),
              child: const Text('إنشاء')),
        ],
      ),
    );
    controller.dispose();
    if (subject != null && subject.trim().isNotEmpty) {
      await onCreateSupport(subject, 'general');
    }
  }
}

class ParentConversationDetailScreen extends StatefulWidget {
  const ParentConversationDetailScreen({
    super.key,
    required this.conversation,
    required this.messages,
    required this.historical,
    required this.busy,
    required this.error,
    required this.draft,
    required this.onDraftChanged,
    required this.onSend,
  });
  final ParentConversation conversation;
  final List<ParentMessage> messages;
  final bool historical;
  final bool busy;
  final String? error;
  final String draft;
  final ValueChanged<String> onDraftChanged;
  final Future<void> Function() onSend;

  @override
  State<ParentConversationDetailScreen> createState() =>
      _ParentConversationDetailScreenState();
}

class _ParentConversationDetailScreenState
    extends State<ParentConversationDetailScreen> {
  late final TextEditingController controller;

  @override
  void initState() {
    super.initState();
    controller = TextEditingController(text: widget.draft);
  }

  @override
  void didUpdateWidget(covariant ParentConversationDetailScreen oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (widget.draft != oldWidget.draft && controller.text != widget.draft) {
      controller.value = TextEditingValue(
        text: widget.draft,
        selection: TextSelection.collapsed(offset: widget.draft.length),
      );
    }
  }

  @override
  void dispose() {
    controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) => Scaffold(
        appBar: AppBar(title: Text(widget.conversation.subject)),
        body: SafeArea(
          child: Column(
            children: [
              if (widget.historical)
                const Padding(
                  padding: EdgeInsets.all(8),
                  child: Chip(label: Text('سياق تاريخي — للقراءة فقط')),
                ),
              if (widget.error != null)
                Padding(
                  padding: const EdgeInsets.all(8),
                  child: Text(widget.error!,
                      style: TextStyle(
                          color: Theme.of(context).colorScheme.error)),
                ),
              Expanded(
                child: ListView.builder(
                  padding: const EdgeInsets.all(16),
                  itemCount: widget.messages.length,
                  itemBuilder: (context, index) {
                    final message = widget.messages[index];
                    return Card(
                      child: ListTile(
                        title: Text(message.sender),
                        subtitle: Text(message.body),
                      ),
                    );
                  },
                ),
              ),
              if (!widget.historical && widget.conversation.canReply)
                Padding(
                  padding: EdgeInsets.fromLTRB(
                    12,
                    8,
                    12,
                    12 + MediaQuery.viewInsetsOf(context).bottom,
                  ),
                  child: Row(
                    children: [
                      Expanded(
                        child: TextField(
                          controller: controller,
                          onChanged: widget.onDraftChanged,
                          minLines: 1,
                          maxLines: 4,
                          decoration:
                              const InputDecoration(hintText: 'اكتب رسالة...'),
                        ),
                      ),
                      IconButton(
                        onPressed: widget.busy ? null : widget.onSend,
                        icon: widget.busy
                            ? const SizedBox.square(
                                dimension: 20,
                                child:
                                    CircularProgressIndicator(strokeWidth: 2),
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

class ParentCommunicationLinks extends StatelessWidget {
  const ParentCommunicationLinks({
    super.key,
    required this.onNotifications,
    required this.onAnnouncements,
    required this.onMessages,
  });
  final VoidCallback onNotifications;
  final VoidCallback onAnnouncements;
  final VoidCallback onMessages;

  @override
  Widget build(BuildContext context) => Column(
        children: [
          ListTile(
              leading: const Icon(Icons.notifications_outlined),
              title: const Text('الإشعارات'),
              onTap: onNotifications),
          ListTile(
              leading: const Icon(Icons.campaign_outlined),
              title: const Text('الإعلانات'),
              onTap: onAnnouncements),
          ListTile(
              leading: const Icon(Icons.forum_outlined),
              title: const Text('الرسائل'),
              onTap: onMessages),
        ],
      );
}

class _TitleRow extends StatelessWidget {
  const _TitleRow({required this.title, required this.historical});
  final String title;
  final bool historical;

  @override
  Widget build(BuildContext context) => Row(
        children: [
          Expanded(
              child: Text(title,
                  style: Theme.of(context).textTheme.headlineSmall)),
          if (historical) const Chip(label: Text('للقراءة فقط')),
        ],
      );
}

class _Empty extends StatelessWidget {
  const _Empty({required this.icon, required this.text});
  final IconData icon;
  final String text;

  @override
  Widget build(BuildContext context) => Padding(
        padding: const EdgeInsets.symmetric(vertical: 40),
        child: Column(
          children: [
            Icon(icon, size: 48),
            const SizedBox(height: 12),
            Text(text)
          ],
        ),
      );
}

class _Failure extends StatelessWidget {
  const _Failure({required this.message, required this.onRetry});
  final String message;
  final Future<void> Function() onRetry;

  @override
  Widget build(BuildContext context) => Center(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Text(message, textAlign: TextAlign.center),
            const SizedBox(height: 12),
            FilledButton(
                onPressed: onRetry, child: const Text('إعادة المحاولة')),
          ],
        ),
      );
}
