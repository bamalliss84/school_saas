# Sprint 4B - Context-Aware Notifications, Homework Completion, Messaging & School Inbox

**Status:** Complete

## Architecture and context

All Sprint 4B authorization and tenant selection use `request.active_membership`, `request.active_school`, `request.active_role`, and `request.active_academic_year`. Notifications belong to one recipient membership. Conversations contain `ConversationParticipant` rows tied to `SchoolMembership`; messages use the sender membership. Cross-school recipients, free recipient search, and historical writes are rejected. Side effects use immutable IDs with `transaction.on_commit`; no signals or external delivery providers are used.

Migration `0021_notifications_messaging` adds `Notification`, `Conversation`, `ConversationParticipant`, `Message`, and `MessageAttachment`. Constraints protect notification read metadata and deduplication, participant uniqueness, message reply consistency, and attachment size. Indexes cover unread membership feeds, notification type, conversation membership/status recency, and message timelines.

## Notification API and DTO

Routes: `GET /api/v1/notifications/`, detail, read, read-all, and unread-count. Public DTO fields are `id`, `notification_type`, `title`, `body`, `is_read`, `read_at`, `created_at`, safe `action`, school summary, `membership_id`, and safe payload. It never exposes deduplication keys or internal recipient/source data. Deduplication is event- and membership-specific. Homework publish/grade/return, result publish, message, and school reply integrations create notifications only after commit.

Action routes are `homework_detail`, `homework_submission`, `result_detail`, `conversation_detail`, and `school_support_detail`; every destination reauthorizes access server-side.

## Homework completion and dashboard

Completion is derived, not stored, with precedence: graded, returned, submitted, draft/overdue, closed_without_submission, overdue, not_started. Student and guardian-bound parent lists expose completion and safe capability metadata. Teacher summaries use aggregate queries. `/api/v1/homework/dashboard/` returns a role-specific DTO with counts and small recent/action collections while preserving historical read-only behavior.

## Messaging and School Inbox

Conversation types are teacher/student, teacher/parent, homework discussion, and school support. Conversation list/detail DTOs include subject, type, status, context metadata, participants, last-message preview, unread count, and timestamps. Message DTOs include sender membership summary, body, reply reference, attachment metadata, and timestamp. Cursor pagination is used for messages.

Conversation start resolves recipients from academic relationships and the active context; arbitrary recipient search is unavailable. Messages notify other active participants after commit. Read markers are per participant. Attachments are validated by configurable count, size, extension, MIME, and safe storage names.

School Support DTO adds category, priority, assignment, status, and resolution metadata. Students, parents, and teachers may create tickets. School administrators can view their tenant inbox, assign administrators, reply, and manage workflow. Requester privacy is participant-scoped; identifiers outside scope return 404. Teacher broadcasts are limited to the active teacher assignment and its students/guardians.

## Badges and Flutter flow

Badge DTO returns notification unread, conversation unread, school-inbox open, and total counts. Context lists compute grouped counts without per-membership queries.

Flutter flow: login; load contexts; select membership; send `X-School-Membership-ID`; load badges; load notification/conversation feeds. A context switch clears local tenant caches. Historical contexts display a Read Only badge and allow only documented personal read markers.

## Admin, audit, throttling, and deferred work

Django Admin is tenant-scoped for notifications, conversations, participants, messages, and attachments. Operational records are mostly read-only. Support and communication actions use centralized services; audit metadata excludes message bodies and secrets. Dedicated throttles cover feeds, sending, attachments, support, broadcast, and dashboard.

Deferred: Announcements/targeting (Sprint 4C), external push/email/SMS/WhatsApp, WebSockets/presence, groups/channels, preferences, scheduled messages, full-text search, export, encryption, account merge, Legacy-field removal, and Flutter implementation.

## Verification

Final verification passed: 503/503 core tests, 93% coverage, clean Ruff, Django checks and migration checks, applied migration 0021, and validated OpenAPI with zero errors and zero warnings. Live server checks returned 200 for health, schema, Swagger, and ReDoc; protected communication feeds returned 401 without a token; Admin redirected guests; the server stopped with zero remaining runserver processes. `check --deploy` retains only the three documented development warnings for HSTS, HTTPS redirect, and the placeholder secret key.


## Sprint 4B.1 - Communication Privacy & Consistency Hardening

**Verification status:** implementation and static review complete; Windows/PostgreSQL runtime revalidation is still required after applying migration 0022.

Teacher-parent conversations contain exactly one selected active parent membership plus the assigned teacher; guardians are never combined and cannot see one another. Homework discussions are also private pairs: student/teacher or one parent/teacher. Reuse requires the same type, related context, and exact participant set. Broadcast remains one-way Notification delivery.

School Support creation schedules a post-commit `school_support_created` notification for active administrators in the same school. It contains only a short subject preview, uses a membership-specific deduplication key, and never fails the original request. Support status, timestamps, resolution note, and audit event now update atomically under `select_for_update`. Reopening clears resolution metadata. Audit records precise transition names and bounded metadata without message or complaint text.

Message attachment batches lock the message, validate every file and the total count before writing, reject historical/closed contexts, and clean newly stored files if storage or database persistence fails. Existing files are never removed by rollback cleanup.

Broadcast actions use a route whitelist (`homework_detail`, `conversation_start`, `school_home`) with route-specific parameters and server-side academic scope validation. Notification payload validation recursively rejects sensitive keys at any depth, non-JSON values, excessive size, and excessive nesting. Serializers validate shape; specialized messaging services enforce role, school, academic year, assignment, enrollment, guardian, target membership, historical-write, cross-school, and reuse rules. Migration `0021_notifications_messaging` remains the original communication schema applied before hardening. The additional consistency checks and defensive metadata normalization are isolated in `0022_communication_privacy_constraints`, so existing development and future production databases follow the same safe migration path.
