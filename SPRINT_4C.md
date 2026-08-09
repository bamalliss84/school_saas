# Sprint 4C — Announcements & Targeting

## Status

Implemented in the working tree. Final Windows/PostgreSQL verification is still required before Commit.

## Architecture

New request-scoped code uses only:

- `request.active_membership`
- `request.active_school`
- `request.active_role`
- `request.active_academic_year`

The legacy `request.user.school`, `request.user.role`, and `request.user.academic_year` values remain compatibility-only and are not authorization sources.

## Models

- `Announcement`
- `AnnouncementAttachment`
- `AnnouncementReceipt`

Migration: `0023_announcements_targeting.py`.

## Workflow

- Draft
- Published
- Closed
- Archived

Only Draft announcements can be edited or receive attachment changes. Publishing resolves all eligible active membership recipients in one school, creates immutable receipt rows, writes audit metadata, and schedules in-app notifications after the database Commit. Closing stops the active lifecycle without deleting history. Archiving preserves receipts and read state.

## Targeting

One explicit audience mode is used per announcement:

- Entire school
- Selected roles
- Classroom
- Section
- Teacher assignment
- Selected students

Classroom, section, assignment, academic year, and student targets are validated against the active school context. Teachers can publish only to their own current teacher assignment. School administrators can target their active school. Student and parent recipients are resolved from current active enrollments and guardian links; no cross-school recipients are allowed.

## Notifications and read receipts

Publishing creates `AnnouncementReceipt` rows and `announcement_published` notifications scoped to each `recipient_membership`. Retries are deduplicated. Historical contexts retain read-only access to delivered announcements and can update only their personal read marker.

## Inquiry flow

An announcement is not itself a chat. When inquiry is enabled, an eligible recipient may open a separate authorized conversation:

- Assignment announcement: Student/Parent ↔ assigned Teacher.
- Other announcements: School Support academic inquiry.

All existing messaging privacy and active-context rules remain enforced.

## API

- `GET, POST /api/v1/announcements/`
- `GET, PUT, PATCH /api/v1/announcements/{id}/`
- `POST /api/v1/announcements/{id}/publish/`
- `POST /api/v1/announcements/{id}/close/`
- `POST /api/v1/announcements/{id}/archive/`
- `POST /api/v1/announcements/{id}/read/`
- `POST /api/v1/announcements/{id}/inquiry/`
- `GET /api/v1/announcements/{id}/summary/`
- `GET /api/v1/announcements/{id}/target-preview/`
- `GET, POST /api/v1/announcements/{id}/attachments/`
- `DELETE /api/v1/announcements/{id}/attachments/{attachment_id}/`

Compatibility routes remain available under `/api/` through the existing versioning configuration.

## Filters

- Status
- Priority
- Audience type
- Academic year
- Read/unread
- Published date range
- Search
- Ordering

Filters are applied after active membership scope and cannot widen tenant access.

## Flutter contract

Announcement responses include:

- Workflow and priority
- Audience summary
- Attachment metadata and file URL
- Read receipt state
- Context-safe action permissions
- `can_inquire`

Notification route: `announcement_detail` with `announcement_id`.

## Deferred

- Scheduled publication
- Expiry scheduling
- External push delivery
- Email/WhatsApp distribution
- Rich text/HTML bodies
- Organization-wide cross-school announcements
- Recipient preference and quiet-hour policies

## Stabilization fix

The recipient-list failure was caused by DRF optional BooleanField HTML semantics: an omitted `unread` query parameter was interpreted as `False`. Query filters now use `OptionalBooleanField`, preserving omitted/true/false as distinct states. The same preventive fix was applied to all optional boolean query filters.
