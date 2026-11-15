"""Platform subscriptions: plans, the current subscription of each school,
platform invoices and manually recorded payments.

Only the platform owner (super_admin) changes these rows. School admins can
read their own school's status through `school_subscription_status`.
"""

from datetime import timedelta
from decimal import Decimal
from functools import partial

from django.db import transaction
from django.db.models import DecimalField, F, Sum, Value
from django.db.models.functions import Coalesce
from django.utils import timezone
from rest_framework.exceptions import NotFound, ValidationError

from core.models import (
    PlatformInvoice, PlatformPayment, School, SchoolMembership, SchoolSubscription, StudentEnrollment,
)
from core.services.notifications import create_notifications_bulk, run_notification_callback

EXPIRY_WARNING_DAYS = 30
ZERO = Decimal('0.00')


def current_subscription(school):
    return (
        SchoolSubscription.objects.filter(school=school, status__in=SchoolSubscription.CURRENT_STATUSES)
        .select_related('plan').first()
    )


def active_student_count(school):
    return StudentEnrollment.objects.filter(
        school=school, is_current=True, status='active', academic_year__is_active=True,
    ).values('student_id').distinct().count()


def school_subscription_status(school, today=None):
    """Read model used by the school admin banner and the owner dashboard."""
    today = today or timezone.localdate()
    subscription = current_subscription(school)
    students = active_student_count(school)
    outstanding = PlatformInvoice.objects.filter(school=school, status='issued').aggregate(
        total=Coalesce(Sum(F('amount') - F('paid_amount'), output_field=DecimalField(max_digits=14, decimal_places=2)),
                       Value(ZERO, output_field=DecimalField(max_digits=14, decimal_places=2))),
    )['total']
    if subscription is None:
        return {
            'has_subscription': False, 'status': None, 'warning': 'no_subscription',
            'student_count': students, 'outstanding': str(outstanding),
        }
    days_left = (subscription.end_date - today).days
    limit = subscription.effective_student_limit
    warning = None
    if subscription.status in ('past_due', 'suspended'):
        warning = subscription.status
    elif days_left < 0:
        warning = 'expired'
    elif days_left <= EXPIRY_WARNING_DAYS:
        warning = 'trial_ending' if subscription.status == 'trial' else 'expiring'
    elif limit is not None and students > limit:
        warning = 'over_limit'
    return {
        'has_subscription': True,
        'id': subscription.id,
        'status': subscription.status,
        'plan': {
            'id': subscription.plan_id, 'code': subscription.plan.code, 'name': subscription.plan.name,
            'billing_period': subscription.plan.billing_period, 'features': subscription.plan.features,
        },
        'start_date': subscription.start_date.isoformat(),
        'end_date': subscription.end_date.isoformat(),
        'days_left': days_left,
        'student_count': students,
        'student_limit': limit,
        'price_per_student': str(subscription.effective_price_per_student),
        'currency': subscription.plan.currency,
        'outstanding': str(outstanding),
        'warning': warning,
    }


# --- Owner actions -----------------------------------------------------------

@transaction.atomic
def create_subscription(*, school, plan, start_date, end_date, actor, status='trial', student_limit=None,
                        custom_price_per_student=None, notes=''):
    if not school.is_active:
        raise ValidationError({'school': ['المدرسة غير مفعّلة.']})
    if not plan.is_active:
        raise ValidationError({'plan': ['الباقة غير متاحة.']})
    if status not in SchoolSubscription.CURRENT_STATUSES:
        raise ValidationError({'status': ['الاشتراك الجديد يبدأ تجريبيًا أو نشطًا.']})
    School.objects.select_for_update().only('id').get(pk=school.pk)
    previous = current_subscription(school)
    if previous is not None:
        # Renewal or plan change: the old subscription ends, history is kept.
        previous.status = 'expired' if previous.end_date < timezone.localdate() else 'cancelled'
        previous.save(update_fields=('status', 'updated_at'))
    subscription = SchoolSubscription(
        school=school, plan=plan, status=status, start_date=start_date, end_date=end_date,
        student_limit=student_limit, custom_price_per_student=custom_price_per_student,
        notes=notes or '', created_by=actor,
    )
    subscription.full_clean()
    subscription.save()
    return subscription


ALLOWED_TRANSITIONS = {
    'trial': {'active', 'cancelled', 'suspended'},
    'active': {'past_due', 'suspended', 'cancelled', 'expired'},
    'past_due': {'active', 'suspended', 'cancelled'},
    'suspended': {'active', 'cancelled'},
    'cancelled': set(),
    'expired': set(),
}


@transaction.atomic
def update_subscription(*, subscription_id, data):
    try:
        subscription = SchoolSubscription.objects.select_for_update().get(pk=subscription_id)
    except SchoolSubscription.DoesNotExist as exc:
        raise NotFound('Subscription not found.') from exc
    new_status = data.get('status')
    if new_status and new_status != subscription.status:
        if new_status not in ALLOWED_TRANSITIONS[subscription.status]:
            raise ValidationError({'status': [f'لا يمكن الانتقال من {subscription.status} إلى {new_status}.']})
        subscription.status = new_status
    for field in ('end_date', 'student_limit', 'custom_price_per_student', 'notes'):
        if field in data:
            setattr(subscription, field, data[field])
    subscription.full_clean()
    subscription.save()
    return subscription


def _next_invoice_number(issued_on):
    prefix = f'INV{issued_on.year}-'
    last = (
        PlatformInvoice.objects.select_for_update().filter(number__startswith=prefix)
        .order_by('-number').values_list('number', flat=True).first()
    )
    sequence = int(last.split('-')[-1]) + 1 if last else 1
    return f'{prefix}{sequence:05d}'


@transaction.atomic
def issue_invoice(*, subscription_id, period_start, period_end, due_date, notes='', student_count=None):
    try:
        subscription = SchoolSubscription.objects.select_for_update().select_related('plan', 'school').get(
            pk=subscription_id, status__in=SchoolSubscription.CURRENT_STATUSES,
        )
    except SchoolSubscription.DoesNotExist as exc:
        raise NotFound('Current subscription not found.') from exc
    if period_start > period_end:
        raise ValidationError({'period_end': ['نهاية الفترة قبل بدايتها.']})
    issued_on = timezone.localdate()
    if due_date < issued_on:
        raise ValidationError({'due_date': ['تاريخ الاستحقاق في الماضي.']})
    count = active_student_count(subscription.school) if student_count is None else int(student_count)
    amount = subscription.plan.base_price + subscription.effective_price_per_student * count
    invoice = PlatformInvoice.objects.create(
        school=subscription.school, subscription=subscription, number=_next_invoice_number(issued_on),
        period_start=period_start, period_end=period_end, student_count=count,
        amount=amount.quantize(Decimal('0.01')), currency=subscription.plan.currency,
        issued_on=issued_on, due_date=due_date, notes=notes or '',
    )
    transaction.on_commit(partial(run_notification_callback, notify_invoice_issued, invoice_id=invoice.pk))
    return invoice


@transaction.atomic
def record_platform_payment(*, invoice_id, actor, amount, method, paid_on, reference=''):
    try:
        invoice = PlatformInvoice.objects.select_for_update().select_related('subscription').get(pk=invoice_id)
    except PlatformInvoice.DoesNotExist as exc:
        raise NotFound('Invoice not found.') from exc
    if invoice.status != 'issued':
        raise ValidationError({'status': ['الفاتورة ليست مفتوحة للدفع.']})
    amount = Decimal(str(amount)).quantize(Decimal('0.01'))
    if amount <= 0 or amount > invoice.balance:
        raise ValidationError({'amount': [f'المبلغ يجب أن يكون بين 0.01 و{invoice.balance}.']})
    payment = PlatformPayment.objects.create(
        invoice=invoice, amount=amount, method=method, reference=(reference or '')[:120],
        paid_on=paid_on, recorded_by=actor,
    )
    invoice.paid_amount += amount
    fields = ['paid_amount']
    if invoice.paid_amount >= invoice.amount:
        invoice.status = 'paid'
        invoice.paid_at = timezone.now()
        fields += ['status', 'paid_at']
        subscription = invoice.subscription
        if subscription.status == 'past_due' and not subscription.invoices.filter(
            status='issued', due_date__lt=timezone.localdate(),
        ).exclude(pk=invoice.pk).exists():
            subscription.status = 'active'
            subscription.save(update_fields=('status', 'updated_at'))
    invoice.save(update_fields=fields)
    return payment


@transaction.atomic
def void_invoice(*, invoice_id, reason):
    try:
        invoice = PlatformInvoice.objects.select_for_update().get(pk=invoice_id)
    except PlatformInvoice.DoesNotExist as exc:
        raise NotFound('Invoice not found.') from exc
    if invoice.status != 'issued' or invoice.paid_amount > 0:
        raise ValidationError({'status': ['يمكن إلغاء فاتورة مفتوحة بلا دفعات فقط.']})
    invoice.status = 'void'
    invoice.notes = f'{invoice.notes}\nVoid: {(reason or "").strip()[:300]}'.strip()
    invoice.save(update_fields=('status', 'notes'))
    return invoice


def mark_overdue_subscriptions(today=None):
    """Move active subscriptions with overdue invoices to past_due and notify admins."""
    today = today or timezone.localdate()
    ids = set(PlatformInvoice.objects.filter(
        status='issued', due_date__lt=today, subscription__status='active',
    ).values_list('subscription_id', flat=True))
    for subscription in SchoolSubscription.objects.filter(pk__in=ids):
        subscription.status = 'past_due'
        subscription.save(update_fields=('status', 'updated_at'))
        _notify_school_admins(
            school_id=subscription.school_id, title='فاتورة اشتراك متأخرة',
            body='لدى المدرسة فاتورة اشتراك متأخرة. سدّدها لتجنب إيقاف الخدمة.',
            dedup=f'subscription-past-due:{subscription.pk}:{today.isoformat()}',
        )
    return len(ids)


def platform_summary(today=None):
    today = today or timezone.localdate()
    money = DecimalField(max_digits=14, decimal_places=2)
    zero = Value(ZERO, output_field=money)
    current = SchoolSubscription.objects.filter(status__in=SchoolSubscription.CURRENT_STATUSES)
    month_start = today.replace(day=1)
    invoices = PlatformInvoice.objects.exclude(status='void')
    return {
        'schools_total': School.objects.count(),
        'schools_active': School.objects.filter(is_active=True).count(),
        'subscriptions': {status: current.filter(status=status).count() for status in SchoolSubscription.CURRENT_STATUSES},
        'schools_without_subscription': School.objects.filter(is_active=True).exclude(
            subscriptions__status__in=SchoolSubscription.CURRENT_STATUSES,
        ).count(),
        'expiring_soon': current.filter(end_date__gte=today, end_date__lte=today + timedelta(days=EXPIRY_WARNING_DAYS)).count(),
        'outstanding': str(invoices.filter(status='issued').aggregate(
            v=Coalesce(Sum(F('amount') - F('paid_amount'), output_field=money), zero))['v']),
        'overdue': str(invoices.filter(status='issued', due_date__lt=today).aggregate(
            v=Coalesce(Sum(F('amount') - F('paid_amount'), output_field=money), zero))['v']),
        'collected_this_month': str(PlatformPayment.objects.filter(paid_on__gte=month_start).aggregate(
            v=Coalesce(Sum('amount', output_field=money), zero))['v']),
        'invoiced_this_year': str(invoices.filter(issued_on__year=today.year).aggregate(
            v=Coalesce(Sum('amount', output_field=money), zero))['v']),
    }


def _notify_school_admins(*, school_id, title, body, dedup):
    memberships = SchoolMembership.objects.filter(
        school_id=school_id, role='school_admin', status='active', school__is_active=True,
    )
    create_notifications_bulk(
        memberships=memberships, notification_type='subscription', title=title, body=body,
        action_url='/subscription', source_type='platform_subscription',
        deduplication_key_factory=lambda membership_id: f'{dedup}:{membership_id}',
    )


def notify_invoice_issued(*, invoice_id):
    invoice = PlatformInvoice.objects.get(pk=invoice_id)
    _notify_school_admins(
        school_id=invoice.school_id, title='فاتورة اشتراك جديدة',
        body=f'صدرت فاتورة {invoice.number} بمبلغ {invoice.amount} {invoice.currency}، تستحق في {invoice.due_date.isoformat()}.',
        dedup=f'platform-invoice:{invoice.pk}',
    )

