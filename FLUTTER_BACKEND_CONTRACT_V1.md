# Flutter Backend Contract V1

Flutter work has not started. A client must first authenticate, load `/api/v1/auth/contexts/`, choose a membership when required, and send `X-School-Membership-ID` on school APIs. A context switch invalidates tenant-scoped cached lists and detail objects.

The client must treat 401 as authentication failure, 403 as forbidden/inactive/read-only context, 404 as unavailable or out of scope, 409 `context_required` as a context-selection prompt, and 400 as validated input/filter failure.

Historical context must render as read-only. Personal mark-read actions remain available only where the backend documents them. The client must never infer authorization from legacy user school/role fields or construct cross-school recipient lists.

OpenAPI is authoritative for DTO fields, multipart upload shapes, pagination, workflow actions, and announcement optional-boolean filters.
