# Service Boundaries

- Views resolve HTTP input, active context, pagination, and response serialization.
- Query serializers validate query shape; selectors construct read scope beginning with tenant/role restrictions.
- Domain services enforce workflow transitions, cross-relation school/year consistency, atomicity, locking where needed, audit writes, and after-commit side effects.
- Serializers may validate input shape but are not the sole security boundary for announcements, messaging, homework, attendance, or exam-result workflows.
- Identity membership state changes use `core.services.identity`; no workflow signals are used.
- Exam result mutation uses `core.services.exam_results` so `ExamResultLog` remains authoritative.
- Attachment services validate complete batches, preserve transaction boundaries, and clean only files created by a failed batch.
