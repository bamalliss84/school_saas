from django.db import transaction

from core.models import ExamResult, ExamResultLog


@transaction.atomic
def update_exam_result(*, exam_result, changed_by, reason, **changes):
    """Update an exam result and create an audit record for score/status changes."""
    if not isinstance(exam_result, ExamResult):
        raise TypeError('exam_result must be an ExamResult instance.')

    old_score = exam_result.score
    old_status = exam_result.status

    allowed_fields = {
        'score', 'status', 'remarks', 'graded_by', 'approved_by'
    }
    unknown_fields = set(changes) - allowed_fields
    if unknown_fields:
        raise ValueError(f'Unsupported fields: {sorted(unknown_fields)}')

    for field, value in changes.items():
        setattr(exam_result, field, value)

    exam_result.save()

    if old_score != exam_result.score or old_status != exam_result.status:
        ExamResultLog.objects.create(
            exam_result=exam_result,
            old_score=old_score,
            new_score=exam_result.score,
            old_status=old_status,
            new_status=exam_result.status,
            changed_by=changed_by,
            reason=reason or 'Result updated',
        )

    return exam_result
