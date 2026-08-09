# API Contract V1

The canonical prefix is `/api/v1/`; `/api/` remains a compatibility alias. Protected school APIs use JWT and `X-School-Membership-ID`. When exactly one active context exists the header may be inferred; multiple eligible contexts without selection return `409 context_required`.

Out-of-scope object identifiers return 404 where practical. Invalid filters return 400. Historical contexts are read-only except documented notification, conversation, and announcement personal read markers.

Responses use the project's standard pagination and error envelopes. Query booleans distinguish omission (no filter), explicit true, explicit false, and invalid input (400). The generated OpenAPI schema is the field/route source of truth and validates with zero warnings/errors.

Implemented domains include auth/context, schools/students/parents/teachers, attendance, exams/results/publication, homework/submissions/completion, notifications, conversations/messages, School Inbox, and announcements/attachments.
