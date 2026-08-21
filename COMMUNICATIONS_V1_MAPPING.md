# Student Communications V1 — Backend → Flutter Mapping

**Reviewed:** 2026-08-21  
**Scope:** Student role only.  
**Rule:** هذا الملف Mapping/Contract فقط. لا يحتوي Implementation code ولا يغيّر Backend.

## 1. Executive conclusion

Backend Communications ليس بحاجة إلى إعادة بناء. توجد أربعة Domains صالحة مباشرة لتطبيق الطالب:

1. Notifications
2. Announcements
3. Conversations / Messages
4. School Support (School Inbox)

الـFlutter الحالي لا ينفذ هذه Domains بعد؛ تبويب `الرسائل` ما زال Placeholder، ولا توجد Student features للإشعارات أو الإعلانات أو الدعم المدرسي.

**القرار المعماري المقترح لـV1:**
- Read data: Cache-first / network-refresh مع fallback إلى cache.
- Writes: Online-only، ولا ننفذ Fake mutations أثناء Offline.
- Historical: read-only للبيانات؛ read markers فقط عندما Backend يسمح بها.
- Deep links: whitelist داخل Flutter لroutes التي يصدرها Backend فقط.
- Cache scope: `localUserKey + membershipId + academicYearKey`.

---

# 2. Notifications

## Backend موجود
Endpoints:
- `GET /api/v1/notifications/`
- `GET /api/v1/notifications/<id>/`
- `POST /api/v1/notifications/<id>/read/`
- `POST /api/v1/notifications/read-all/`
- `GET /api/v1/notifications/unread-count/`
- `GET /api/v1/communication/badges/`

Filters supported:
- `is_read`
- `notification_type`
- `date_from/date_to`
- `source_type`
- ordering by `created_at/-created_at`

Notification fields:
- id
- notification_type
- title / body
- is_read / read_at
- created_at
- school
- membership_id
- action
- payload

Supported notification types include:
- homework_published
- homework_graded
- homework_returned
- result_published
- message_received
- school_reply
- school_support_created
- announcement_published
- system

## Design mapping
Design screen: `student_communications_v1.jpg`

V1 Flutter screens:
- Notifications list
- Filter chips: **الكل / غير المقروءة**
- Visual grouping by date (`اليوم`, earlier dates) can be local UI grouping.
- Notification card icon/type/title/body/time/read state.
- `تحديد الكل كمقروء` when online.

## Cache policy
**Cache:** YES.
- Cache list + notification payload/action.
- Offline displays last cached list with Offline banner and last-updated.
- `read` and `read-all`: **Online-only**; update local cache only after server success.
- No fake read mutation while disconnected.

## Deep-link contract
Backend currently emits these action routes across services:
- `homework_detail` → homework_id
- `homework_submission` → submission_id
- `result_detail` → result_id
- `announcement_detail` → announcement_id
- `conversation_detail` → conversation_id (+ optional message_id)
- `school_support_detail` → conversation_id
- teacher broadcast may also emit `school_home` or `conversation_start`

Flutter must whitelist these routes. Unknown route must not crash; open notification detail or show safe message.

**Important:** deep link may open cached target offline only if that feature has the required cached object. Otherwise show a clear internet-required state.

---

# 3. School Announcements

## Backend موجود
Endpoints:
- `GET /api/v1/announcements/`
- `GET /api/v1/announcements/<id>/`
- `POST /api/v1/announcements/<id>/read/`
- `POST /api/v1/announcements/<id>/inquiry/`
- attachments metadata is included in announcement serializer.

Backend also has admin/teacher manage endpoints, but Student Flutter must **not expose** create/publish/close/archive/upload/delete management actions.

Student-visible fields include:
- title/body
- school / academic_year
- priority
- audience_type
- classroom / section / teacher_assignment when applicable
- attachments
- published_at
- receipt `{is_read, read_at}`
- permissions.can_inquire

Visibility is receipt-based and membership-scoped. Historical membership can read delivered announcements. Backend test coverage confirms student sees delivered published items and supports historical read behavior.

## Design mapping
Screens:
- Announcements list
- Announcement detail
- Attachments list
- Read state
- Optional `لدي استفسار` when `permissions.can_inquire == true`

## Cache policy
**Cache:** YES.
- Cache announcement list + detail JSON + attachment metadata.
- Binary attachments are not automatically cached in V1; downloading/opening requires connectivity unless the file was explicitly downloaded by the user later.
- Mark read: Online-only, then persist updated receipt in cache.
- Inquiry: Online-only because it creates/reuses a conversation.

## Historical policy
- List/detail: read-only and cached.
- Mark-read is allowed only according to existing Backend behavior.
- Inquiry should not be shown when `permissions.can_inquire` is false; historical context naturally returns non-writable permissions.

---

# 4. Messages / Conversations

## Backend موجود
Endpoints:
- `GET /api/v1/conversations/`
- `POST /api/v1/conversations/start/`
- `GET /api/v1/conversations/<id>/`
- `GET /api/v1/conversations/<id>/messages/`
- `POST /api/v1/conversations/<id>/messages/`
- `POST /api/v1/conversations/<id>/read/`
- message attachment endpoints
- close/reopen endpoints exist but Student UI should only expose actions allowed by returned permissions/business UX.

Conversation types:
- teacher_student
- teacher_parent
- homework_discussion
- school_support

Student V1 scope:
- Teacher ↔ Student
- Homework discussion ↔ Teacher
- School Support
- **No Student-to-Student**
- **No free groups**

Conversation serializer already provides:
- participants_summary
- last_message_preview
- unread_messages_count
- can_reply
- can_close / can_reopen
- related_type / related_id
- status / category / priority

Messages provide:
- sender
- body
- reply_to
- created_at
- attachments_count

## Design mapping
Screens:
- Conversation list under Bottom tab `الرسائل`
- Conversation detail/chat
- unread badge
- teacher name + subject/context
- text composer
- attachment button
- homework-related conversation must show contextual heading when related_type is homework.

## Cache policy
**Cache:** YES.
- Cache conversation list.
- Cache last loaded page of messages per conversation (at least latest 30; backend cursor page size is 30).
- Offline: conversations/messages read-only from cache.
- Sending text, starting conversation, uploading attachment, mark-read: **Online-only**.
- After successful send/read, update cache from actual server response/refresh.

## Historical policy
Backend supports reading historical conversations while writes are denied by `membership.can_write`. Flutter should:
- show cached/server history
- hide/disable composer
- show `للعرض فقط`
- personal read marker may be sent only when Backend permits and network exists.

---

# 5. School Support

## Backend موجود
Endpoints:
- `GET /api/v1/school-inbox/`
- `POST /api/v1/school-inbox/`
- `GET /api/v1/school-inbox/<id>/`
- `POST /api/v1/school-inbox/<id>/reply/`

Admin-only/management endpoints also exist (`assign`, `status`), but Student Flutter **does not expose school administration controls**.

Create payload supports:
- subject
- category
- priority
- optional initial message

Backend categories:
- academic_inquiry
- absence_excuse
- profile_update
- technical_issue
- complaint
- other

Recommended Arabic labels (do not invent unsupported values):
- `academic_inquiry` → استفسار دراسي
- `absence_excuse` → عذر غياب
- `profile_update` → تحديث بيانات
- `technical_issue` → مشكلة تقنية
- `complaint` → شكوى
- `other` → أخرى

Backend statuses:
- open
- in_progress
- resolved
- closed

Recommended Arabic labels:
- مفتوح
- قيد المعالجة
- تم الحل
- مغلق

## Design mapping
Screens:
- Create school request
- Request type/category
- Subject
- Description/message
- Optional attachment UX
- Request history/list
- Request detail/status timeline
- School replies

## Attachment note — important
`POST /school-inbox/` itself does **not** accept files. Message attachment API exists separately.

V1 without Backend change can use a safe two-step flow:
1. Create support conversation/request online.
2. Create/fetch the initial message.
3. Upload selected attachment to that message using the existing message attachment API.

If attachment upload fails, the request remains created and UI must say that the request succeeded but attachment upload needs retry. Do not roll back locally or pretend the entire request failed.

This is supported without new Backend models. A future atomic multipart endpoint is optional, not required for Student V1.

## Cache policy
**Cache:** YES for list/detail/messages/status.
- Create/reply/attachment: Online-only.
- Offline screen: last cached requests + status + replies.
- No offline draft submission unless explicitly added later; not needed for V1.

---

# 6. Badges and navigation

Use `GET /api/v1/communication/badges/` for:
- notification_unread
- conversation_unread
- total_badge_count

Student Bottom Navigation remains 5 items:
- الرئيسية
- الواجبات
- النتائج
- الرسائل
- المزيد

Recommended structure:
- `الرسائل` tab = Conversations list with unread badge.
- Notifications are accessible from Home/Header bell and/or Communications entry.
- Announcements accessible from Home/More and notification deep links.
- School Support accessible from More → التواصل مع المدرسة.

Do **not** add a sixth bottom tab.

---

# 7. Required Flutter modules

Proposed feature folders:

```text
features/student/communications/
  notifications/
  announcements/
  messaging/
  school_support/
  shared/
```

Each domain should use:
- domain models
- data repository
- presentation controller
- presentation screens
- focused tests

Do not place all Communications logic in `student_shell.dart`.

---

# 8. Cache implementation decision

For Communications V1, use the existing scoped offline foundation.

Recommended approach for speed + safety:
- generic `CachedContexts` resource IDs for small list/detail datasets where practical, OR dedicated Drift tables only when list/detail lookup/pagination needs justify them.
- Never store data without `CacheScope`.
- Never mix Membership or Academic Year caches.
- `purgeUser` must purge every new communications cache if dedicated tables are added.

Before implementation, choose one consistent strategy and add migration/tests in the same commit if schema changes.

Recommended for V1:
- dedicated communications cache tables are preferable for conversations/messages because IDs and per-conversation pages matter.
- notifications/announcements can also use dedicated tables for clean read-state updates and detail lookup.
- if using dedicated tables, increment Drift schema exactly once for the whole Communications phase rather than adding multiple migrations.

---

# 9. Error/offline state contract

Every Communications screen must distinguish:
- Network unavailable + cached data → show cached data + Offline banner + last updated.
- Network unavailable + no cache → dedicated Offline Empty State.
- 401/session expired → existing Session recovery/login flow.
- 403/unavailable school → existing context recovery flow.
- 409/context_required → existing Context UX.
- Server failure with no usable cache → Error State + Retry.
- Empty successful response → Empty State, not generic error.

No generic `حدث خطأ غير متوقع` when a known state is available.

---

# 10. Tests required before Communications V1 closure

## Repository / models
- JSON parsing for every domain.
- cache scope isolation User A/B, Membership A/B, Academic Year A/B.
- cache fallback on offline-eligible errors only.
- server errors do not silently masquerade as offline cache unless policy allows.

## Notifications
- unread filter
- read/read-all update after success
- badge count
- all supported deep-link route parsing
- unknown action route safe fallback

## Announcements
- published recipient visibility rendering
- receipt read state
- attachments metadata
- can_inquire gating
- Historical read-only

## Messaging
- list/unread count
- cursor messages
- send success/failure
- offline composer disabled
- historical composer disabled
- no student-to-student start option
- message attachments

## School Support
- supported categories only
- create + initial message
- status rendering
- replies
- attachment partial-failure UX
- offline cached detail

## UI regression
- RTL
- small device 320×480
- 150% text scaling
- long Arabic school/person/title/message text
- Loading / Empty / Offline Cached / Offline Empty / Error
- Bottom nav badge/no overflow

---

# 11. Mapping decision / implementation gate

**Backend rebuild required? NO.**

Potential Backend changes required for Student Communications V1: **none mandatory**.

The existing APIs are sufficient to implement V1. School Support attachments require a two-step existing-API workflow, which is acceptable for V1 with explicit partial-success UX.

**Implementation can start after this mapping is accepted.**

Recommended implementation order:
1. Shared communication models/cache foundation + badges.
2. Notifications + deep-link dispatcher.
3. Announcements.
4. Conversations / Messages.
5. School Support.
6. Design closure against `design/student_v1/student_communications_v1.jpg`.
7. Full Communications regression + offline test.
