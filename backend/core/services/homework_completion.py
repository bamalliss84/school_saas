from django.utils import timezone


def completion_status(homework, submission=None, *, now=None):
    """Derive completion state: graded > returned > submitted > draft > closed missing > overdue > not started."""
    now = now or timezone.now()
    if getattr(homework, 'submission_type', 'text') == 'none':
        return 'view_only'
    if submission:
        if submission.status == 'graded': return 'graded'
        if submission.status == 'returned': return 'returned'
        if submission.status == 'submitted': return 'submitted'
        if submission.status == 'draft': return 'overdue' if homework.due_date < now else 'draft'
    if homework.status == 'closed': return 'closed_without_submission'
    if homework.due_date < now: return 'overdue'
    return 'not_started'


def completion_flags(homework, submission=None, *, writable=True, now=None):
    status = completion_status(homework, submission, now=now)
    if getattr(homework, 'submission_type', 'text') == 'none':
        return {
            'completion_status': 'view_only', 'is_overdue': False,
            'can_create_draft': False, 'can_edit': False,
            'can_final_submit': False,
        }
    is_overdue = status == 'overdue'
    editable = bool(writable and homework.status == 'published' and (submission is None or submission.status in ('draft', 'returned')))
    return {
        'completion_status': status, 'is_overdue': is_overdue,
        'can_create_draft': editable and submission is None,
        'can_edit': editable and submission is not None,
        'can_final_submit': editable,
    }