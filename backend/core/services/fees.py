"""School fees: issuing student fees/installments, recording and voiding payments,
summaries, and guardian notifications.

Every function receives an explicit school (from request.active_school) and
re-checks that all related rows belong to it. Money changes lock the fee row so
paid_amount always equals the sum of non-void payments.
"""

import logging
import uuid
from datetime import timedelta
from decimal import Decimal
from functools import partial

from django.db import transaction
from django.db.models import Count, DecimalField, F, Q, Sum, Value
from django.db.models.functions import Coalesce
from django.utils import timezone
from rest_framework.exceptions import NotFound, ValidationError

from core.models import (
    FeeCategory, FeePayment, School, SchoolMembership, StudentEnrollment, StudentFee, StudentGuardian,
)
from core.services.notifications import create_notifications_bulk, run_notification_callback

logger = logging.getLogger(__name__)

ZERO = Decimal('0.00')
MAX_ISSUE_STUDENTS = 2000
MAX_INSTALLMENTS = 12
TARGET_SCOPES = ('school', 'classroom', 'section', 'students')


def _money(value, field):
    try:
        amount = Decimal(str(value)).quantize(Decimal('0.01'))
    except Exception as exc:  # noqa: BLE001 - any parse error is a validation error
        raise ValidationError({field: ['أدخل مبلغًا صحيحًا.']}) from exc
    if not amount.is_finite():
        raise ValidationError({field: ['أدخل مبلغًا صحيحًا.']})
    return amount


# --- Issuing -----------------------------------------------------------------

def _target_enrollments(*, school, year, scope, classroom_id=None, section_id=None, student_ids=None):
    if scope not in TARGET_SCOPES:
        raise ValidationError({'scope': [f'scope must be one of {", ".join(TARGET_SCOPES)}.']})
    rows = StudentEnrollment.objects.filter(
        school=school, academic_year=year, is_current=True, status='active', student__is_active=True,
    ).select_related('student', 'classroom', 'section')
    if scope == 'classroom':
        if not classroom_id:
            raise ValidationError({'classroom_id': ['اختر الصف.']})
        rows = rows.filter(classroom_id=classroom_id)
    elif scope == 'section':
        if not section_id:
            raise ValidationError({'section_id': ['اختر الشعبة.']})
        rows = rows.filter(section_id=section_id)
    elif scope == 'students':
        ids = {int(item) for item in (student_ids or [])}
        if not ids:
            raise ValidationError({'student_ids': ['اختر طالبًا واحدًا على الأقل.']})
        rows = rows.filter(student_id__in=ids)
        found = set(rows.values_list('student_id', flat=True))
        if found != ids:
            # Students outside the active school/year are reported, never revealed.
            raise ValidationError({'student_ids': ['بعض الطلاب غير مسجلين في هذه المدرسة والسنة الحالية.']})
    return list(rows.order_by('student__full_name'))


def _installments(total, installments):
    if not installments:
        raise ValidationError({'installments': ['أضف قسطًا واحدًا على الأقل.']})
    if len(installments) > MAX_INSTALLMENTS:
        raise ValidationError({'installments': [f'الحد الأقصى {MAX_INSTALLMENTS} قسطًا.']})
    parsed = []
    for index, item in enumerate(installments, start=1):
        amount = _money(item.get('amount'), 'installments')
        due = item.get('due_date')
        if amount <= 0 or not due:
            raise ValidationError({'installments': [f'القسط {index} يحتاج مبلغًا أكبر من صفر وتاريخ استحقاق.']})
        parsed.append((amount, due))
    if sum(a for a, _ in parsed) != total:
        raise ValidationError({'installments': ['مجموع الأقساط يجب أن يساوي المبلغ الإجمالي.']})
    dates = [d for _, d in parsed]
    if dates != sorted(dates):
        raise ValidationError({'installments': ['رتّب الأقساط حسب تاريخ الاستحقاق.']})
    return parsed


def issue_fees(*, school, year, actor, data, confirm):
    """Preview (confirm=False) or create fees for every targeted student."""
    if year is None or year.school_id != school.id:
        raise ValidationError({'academic_year': ['لا توجد سنة دراسية نشطة لهذه المدرسة.']})
    try:
        category = FeeCategory.objects.get(pk=data.get('category_id'), school=school, is_active=True)
    except (FeeCategory.DoesNotExist, ValueError, TypeError) as exc:
        raise ValidationError({'category_id': ['اختر نوع رسوم صالحًا من هذه المدرسة.']}) from exc
    title = (data.get('title') or '').strip()
    if not title:
        raise ValidationError({'title': ['أدخل عنوان الرسوم.']})
    total = _money(data.get('amount'), 'amount')
    discount = _money(data.get('discount') or 0, 'discount')
    if total <= 0:
        raise ValidationError({'amount': ['المبلغ يجب أن يكون أكبر من صفر.']})
    if discount < 0 or discount > total:
        raise ValidationError({'discount': ['الخصم يجب أن يكون بين صفر والمبلغ الإجمالي.']})
    installments = data.get('installments') or [{'amount': str(total), 'due_date': data.get('due_date')}]
    parts = _installments(total, installments)
    enrollments = _target_enrollments(
        school=school, year=year, scope=data.get('scope', 'school'),
        classroom_id=data.get('classroom_id'), section_id=data.get('section_id'),
        student_ids=data.get('student_ids'),
    )
    if not enrollments:
        raise ValidationError({'scope': ['لا يوجد طلاب مسجلون حاليًا في النطاق المختار.']})
    if len(enrollments) > MAX_ISSUE_STUDENTS:
        raise ValidationError({'scope': [f'الحد الأقصى {MAX_ISSUE_STUDENTS} طالب في العملية الواحدة.']})

    preview = {
        'student_count': len(enrollments),
        'installment_count': len(parts),
        'amount_per_student': str(total),
        'discount_per_student': str(discount),
        'total_net': str((total - discount) * len(enrollments)),
        'students': [
            {'id': row.student_id, 'full_name': row.student.full_name,
             'classroom': row.classroom.name, 'section': row.section.name}
            for row in enrollments[:50]
        ],
    }
    if not confirm:
        return {'confirmed': False, **preview}

    batch = uuid.uuid4()
    rows = []
    with transaction.atomic():
        for row in enrollments:
            remaining_discount = discount
            for number, (amount, due) in enumerate(parts, start=1):
                # The discount is taken from the earliest installments first.
                part_discount = min(remaining_discount, amount)
                remaining_discount -= part_discount
                fee = StudentFee(
                    school=school, academic_year=year, student=row.student, category=category,
                    title=title if len(parts) == 1 else f'{title} - القسط {number}',
                    amount=amount, discount=part_discount, due_date=due, batch_id=batch,
                    installment_number=number, installment_count=len(parts), created_by=actor,
                )
                fee.full_clean()
                rows.append(fee)
        StudentFee.objects.bulk_create(rows)
        transaction.on_commit(partial(run_notification_callback, notify_fees_issued, batch_id=str(batch)))
    return {'confirmed': True, 'batch_id': str(batch), 'created': len(rows), **preview}


@transaction.atomic
def cancel_fee(*, school, fee_id, reason):
    fee = _locked_fee(school, fee_id)
    if fee.status == 'cancelled':
        raise ValidationError({'status': ['الرسوم ملغاة مسبقًا.']})
    if fee.paid_amount > 0:
        raise ValidationError({'status': ['لا يمكن إلغاء رسوم عليها دفعات. ألغِ الدفعات أولًا.']})
    reason = (reason or '').strip()
    if not reason:
        raise ValidationError({'reason': ['اكتب سبب الإلغاء.']})
    fee.status = 'cancelled'
    fee.cancel_reason = reason[:300]
    fee.save(update_fields=('status', 'cancel_reason', 'updated_at'))
    return fee


# --- Payments ----------------------------------------------------------------

def _locked_fee(school, fee_id):
    try:
        return StudentFee.objects.select_for_update().select_related('student').get(pk=fee_id, school=school)
    except (StudentFee.DoesNotExist, ValueError, TypeError) as exc:
        raise NotFound('Fee not found.') from exc


def _next_receipt_number(school, paid_on):
    # Locking the school row serializes receipt numbering inside one school.
    School.objects.select_for_update().only('id').get(pk=school.pk)
    prefix = f'R{paid_on.year}-'
    last = (
        FeePayment.objects.filter(school=school, receipt_number__startswith=prefix)
        .order_by('-receipt_number').values_list('receipt_number', flat=True).first()
    )
    sequence = int(last.split('-')[-1]) + 1 if last else 1
    return f'{prefix}{sequence:06d}'


@transaction.atomic
def record_payment(*, school, fee_id, actor, amount, method, paid_on, reference=''):
    fee = _locked_fee(school, fee_id)
    if fee.status != 'open':
        raise ValidationError({'status': ['لا يمكن الدفع على رسوم ملغاة.']})
    amount = _money(amount, 'amount')
    if amount <= 0:
        raise ValidationError({'amount': ['المبلغ يجب أن يكون أكبر من صفر.']})
    if amount > fee.balance:
        raise ValidationError({'amount': [f'المبلغ أكبر من المتبقي ({fee.balance}).']})
    if paid_on > timezone.localdate():
        raise ValidationError({'paid_on': ['تاريخ الدفع لا يمكن أن يكون في المستقبل.']})
    payment = FeePayment(
        school=school, student_fee=fee, amount=amount, method=method, reference=(reference or '')[:120],
        paid_on=paid_on, receipt_number=_next_receipt_number(school, paid_on), recorded_by=actor,
    )
    payment.full_clean()
    payment.save()
    StudentFee.objects.filter(pk=fee.pk).update(paid_amount=F('paid_amount') + amount, updated_at=timezone.now())
    transaction.on_commit(partial(run_notification_callback, notify_payment_received, payment_id=payment.pk))
    return payment


@transaction.atomic
def void_payment(*, school, payment_id, actor, reason):
    try:
        payment = FeePayment.objects.select_for_update().get(pk=payment_id, school=school)
    except (FeePayment.DoesNotExist, ValueError, TypeError) as exc:
        raise NotFound('Payment not found.') from exc
    if payment.is_void:
        raise ValidationError({'status': ['الدفعة ملغاة مسبقًا.']})
    reason = (reason or '').strip()
    if not reason:
        raise ValidationError({'reason': ['اكتب سبب إلغاء الدفعة.']})
    _locked_fee(school, payment.student_fee_id)
    payment.is_void = True
    payment.void_reason = reason[:300]
    payment.voided_by = actor
    payment.voided_at = timezone.now()
    payment.save(update_fields=('is_void', 'void_reason', 'voided_by', 'voided_at'))
    StudentFee.objects.filter(pk=payment.student_fee_id).update(
        paid_amount=F('paid_amount') - payment.amount, updated_at=timezone.now(),
    )
    return payment


# --- Queries and summaries ---------------------------------------------------

def fees_queryset(school, year=None):
    rows = StudentFee.objects.filter(school=school).select_related('student', 'category', 'academic_year')
    return rows.filter(academic_year=year) if year is not None else rows


def filter_by_state(queryset, state, today=None):
    today = today or timezone.localdate()
    open_rows = queryset.filter(status='open')
    unpaid_balance = Q(paid_amount__lt=F('amount') - F('discount'))
    if state == 'paid':
        return open_rows.exclude(unpaid_balance)
    if state == 'overdue':
        return open_rows.filter(unpaid_balance, due_date__lt=today)
    if state == 'unpaid':
        return open_rows.filter(unpaid_balance, paid_amount=0, due_date__gte=today)
    if state == 'partial':
        return open_rows.filter(unpaid_balance, paid_amount__gt=0, due_date__gte=today)
    if state == 'cancelled':
        return queryset.filter(status='cancelled')
    if state in (None, ''):
        return queryset
    raise ValidationError({'state': ['state must be one of unpaid, partial, paid, overdue, cancelled.']})


def summarize(queryset, today=None):
    """Totals over open fees; amounts are returned as strings to keep precision."""
    today = today or timezone.localdate()
    money = DecimalField(max_digits=14, decimal_places=2)
    zero = Value(ZERO, output_field=money)
    open_rows = queryset.filter(status='open')
    balance = F('amount') - F('discount') - F('paid_amount')
    totals = open_rows.aggregate(
        total=Coalesce(Sum(F('amount') - F('discount'), output_field=money), zero),
        paid=Coalesce(Sum('paid_amount', output_field=money), zero),
        overdue=Coalesce(Sum(balance, filter=Q(due_date__lt=today), output_field=money), zero),
        overdue_count=Count('id', filter=Q(due_date__lt=today, paid_amount__lt=F('amount') - F('discount'))),
        fee_count=Count('id'),
    )
    next_due = (
        open_rows.filter(due_date__gte=today, paid_amount__lt=F('amount') - F('discount'))
        .order_by('due_date', 'id').first()
    )
    currency = open_rows.values_list('currency', flat=True).first()
    return {
        'currency': currency,
        'total': str(totals['total']),
        'paid': str(totals['paid']),
        'remaining': str(totals['total'] - totals['paid']),
        'overdue': str(totals['overdue']),
        'overdue_count': totals['overdue_count'],
        'fee_count': totals['fee_count'],
        'next_due': {
            'fee_id': next_due.id, 'title': next_due.title, 'due_date': next_due.due_date.isoformat(),
            'balance': str(next_due.balance),
        } if next_due else None,
    }


# --- Guardians ---------------------------------------------------------------

def financial_guardian_memberships(student_ids, school_id):
    """Active parent memberships of guardians allowed to receive financial alerts."""
    user_ids = set(StudentGuardian.objects.filter(
        student_id__in=student_ids, can_receive_financial_alerts=True, parent__user__isnull=False,
    ).values_list('parent__user_id', flat=True))
    return SchoolMembership.objects.filter(
        user_id__in=user_ids, school_id=school_id, role='parent', status='active', school__is_active=True,
    )


def guardian_student_ids(membership):
    """Students whose fees this parent membership may see (financial-alert guardians only)."""
    if membership is None or membership.role != 'parent':
        return set()
    return set(StudentGuardian.objects.filter(
        parent__user_id=membership.user_id, can_receive_financial_alerts=True,
        student__enrollments__school_id=membership.school_id,
    ).values_list('student_id', flat=True))


def _notify_students(*, school_id, student_ids, notification_type, title, body, source_type, source_id, dedup):
    for student_id in student_ids:
        memberships = financial_guardian_memberships([student_id], school_id)
        create_notifications_bulk(
            memberships=memberships, notification_type=notification_type, title=title, body=body,
            action_url=f'/parent/children/{student_id}/fees', payload={'student_id': student_id},
            source_type=source_type, source_id=source_id,
            deduplication_key_factory=(lambda membership_id, sid=student_id: f'{dedup}:{sid}:{membership_id}'),
        )


def notify_fees_issued(*, batch_id):
    fees = list(StudentFee.objects.filter(batch_id=batch_id, installment_number=1).select_related('student'))
    if not fees:
        return
    by_student = {fee.student_id: fee for fee in fees}
    sample = fees[0]
    title_base = sample.title.split(' - القسط')[0]
    _notify_students(
        school_id=sample.school_id, student_ids=by_student.keys(), notification_type='fee_issued',
        title='رسوم جديدة', body=f'أُضيفت رسوم "{title_base}". افتح تفاصيل الرسوم لمعرفة المبالغ ومواعيد الاستحقاق.',
        source_type='fee_batch', source_id=None, dedup=f'fee-issued:{batch_id}',
    )


def notify_payment_received(*, payment_id):
    payment = FeePayment.objects.select_related('student_fee', 'student_fee__student').get(pk=payment_id)
    fee = payment.student_fee
    _notify_students(
        school_id=payment.school_id, student_ids=[fee.student_id], notification_type='payment_received',
        title='تم استلام دفعة',
        body=f'استلمنا {payment.amount} {fee.currency} لـ "{fee.title}". رقم الإيصال {payment.receipt_number}.',
        source_type='fee_payment', source_id=payment.pk, dedup=f'payment:{payment.pk}',
    )


def send_due_reminders(today=None, days_before=3):
    """Due-soon (once per fee) and overdue (once per week) reminders. Idempotent."""
    today = today or timezone.localdate()
    week = today.isocalendar()
    open_unpaid = StudentFee.objects.filter(
        status='open', paid_amount__lt=F('amount') - F('discount'), school__is_active=True,
    ).select_related('student')
    sent = 0
    for fee in open_unpaid.filter(due_date=today + timedelta(days=days_before)):
        _notify_students(
            school_id=fee.school_id, student_ids=[fee.student_id], notification_type='fee_due',
            title='قسط مستحق قريبًا',
            body=f'"{fee.title}" مستحق في {fee.due_date.isoformat()}. المتبقي {fee.balance} {fee.currency}.',
            source_type='student_fee', source_id=fee.pk, dedup=f'fee-due:{fee.pk}',
        )
        sent += 1
    for fee in open_unpaid.filter(due_date__lt=today):
        _notify_students(
            school_id=fee.school_id, student_ids=[fee.student_id], notification_type='fee_overdue',
            title='قسط متأخر',
            body=f'"{fee.title}" تأخر عن موعده ({fee.due_date.isoformat()}). المتبقي {fee.balance} {fee.currency}.',
            source_type='student_fee', source_id=fee.pk, dedup=f'fee-overdue:{fee.pk}:{week.year}-{week.week}',
        )
        sent += 1
    return sent
