# Homework V1 — Instructions and Attachment Integration

## Scope

This change is intentionally Flutter-only. The Django schema and homework workflow were not changed.

## Existing backend contract reused

- `Homework.description` is the teacher's assignment instructions/prompt.
- Homework attachments are exposed through `HomeworkSerializer.attachments`.
- Student submission attachments are exposed through `HomeworkSubmissionSerializer.attachments`.
- Existing endpoints are reused:
  - `POST /api/v1/homework-submissions/<id>/attachments/`
  - `DELETE /api/v1/homework-submissions/<id>/attachments/<attachment_id>/`
- Backend service rules remain authoritative: student attachments can change only while the homework is published and the submission is draft/returned.

## Flutter behavior

- Homework detail now labels the description clearly as `المطلوب` before `إجابتي`.
- Teacher files are shown under `مرفقات المعلم` and remain downloadable online.
- Student can pick multiple JPG/JPEG/PNG/PDF files and upload them to the existing submission attachment endpoint.
- Uploading an attachment creates the student's submission draft first when necessary.
- Student attachments are shown under `مرفقات إجابتي`.
- Editable draft/returned submissions can delete their own attachments.
- Submitted/graded attachments remain visible read-only.
- No upload/delete is allowed from the mobile UI while offline or historical/read-only.
- Final submission remains an online-only action.

## Deliberately not added

- No model/migration/schema change.
- No multiple-choice/question engine inside Homework.
- No student-to-student behavior.
- No fake offline upload queue.

## Verification required on Windows

Run `flutter pub get`, `flutter analyze`, and `flutter test`, then perform a real Android smoke test against Django storage.
