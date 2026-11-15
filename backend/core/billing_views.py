"""Release 1.1 APIs: school fees (school admin + parent) and platform
subscriptions (platform owner + read-only school admin view).

Authorization uses only request.active_role / active_school /
active_membership / active_academic_year. Records outside the caller's scope
return 404.
"""

from django.db.models import Q
from django.utils import timezone
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema
from rest_framework import serializers, status
from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.views import APIView

from .context import require_writable_context
from .models import (
    PAYMENT_METHOD_CHOICES, FeeCategory, FeePayment, PlatformInvoice, School, SchoolSubscription,
    StudentFee, SubscriptionPlan,
)
from .permissions import IsActiveSchoolUser
from .services import fees as fee_service
from .services import subscriptions as subscription_service

METHODS = [code for code, _ in PAYMENT_METHOD_CHOICES]


# --- Shared helpers ----------------------------------------------------------

def _school_admin(request, write=False):
    if request.active_role not in ('school_admin', 'super_admin') or not request.active_school:
        raise PermissionDenied('School administrator access is required.')
    if write:
        require_writable_context(request)


def _platform_owner(request):
    if request.active_role != 'super_admin' or request.active_membership is not None:
        raise PermissionDenied('Platform owner access is required.')


def _parent(request):
    if request.active_role != 'parent' or request.active_membership is None:
        raise PermissionDenied('Parent access is required.')


def _int(request, name):
    value = request.query_params.get(name)
    if value in (None, ''):
        return None
    try:
        return int(value)
    except (TypeError, ValueError) as exc:
        raise ValidationError({name: f'{name} must be an integer.'}) from exc


def _date(request, name):
    value = request.query_params.get(name)
    if value in (None, ''):
        return None
    field = serializers.DateField()
    try:
        return field.to_internal_value(value)
    except serializers.ValidationError as exc:
        raise ValidationError({name: f'{name} must be a date (YYYY-MM-DD).'}) from exc


class Pagination(PageNumberPagination):
    page_size = 25
    page_size_query_param = 'page_size'
    max_page_size = 200


# --- Serializers -------------------------------------------------------------

class FeeCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = FeeCategory
        fields = ('id', 'name', 'description', 'is_active', 'created_at')
        read_only_fields = ('id', 'created_at')

    def validate_name(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError('أدخل اسم نوع الرسوم.')
        school = self.context['school']
        duplicate = FeeCategory.objects.filter(school=school, name__iexact=value)
        if self.instance is not None:
            duplicate = duplicate.exclude(pk=self.instance.pk)
        if duplicate.exists():
            raise serializers.ValidationError('يوجد نوع رسوم بنفس الاسم.')
        return value


class FeePaymentSerializer(serializers.ModelSerializer):
    student_id = serializers.IntegerField(source='student_fee.student_id', read_only=True)
    student_name = serializers.CharField(source='student_fee.student.full_name', read_only=True)
    fee_title = serializers.CharField(source='student_fee.title', read_only=True)
    currency = serializers.CharField(source='student_fee.currency', read_only=True)

    class Meta:
        model = FeePayment
        fields = (
            'id', 'student_fee', 'student_id', 'student_name', 'fee_title', 'amount', 'currency', 'method',
            'reference', 'paid_on', 'receipt_number', 'is_void', 'void_reason', 'voided_at', 'created_at',
        )


class StudentFeeSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source='student.full_name', read_only=True)
    student_code = serializers.CharField(source='student.student_code', read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True)
    net_amount = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    balance = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    payment_state = serializers.SerializerMethodField()

    class Meta:
        model = StudentFee
        fields = (
            'id', 'student', 'student_name', 'student_code', 'category', 'category_name', 'title', 'amount',
            'discount', 'net_amount', 'paid_amount', 'balance', 'currency', 'due_date', 'status',
            'payment_state', 'cancel_reason', 'installment_number', 'installment_count', 'batch_id', 'created_at',
        )

    def get_payment_state(self, obj):
        return obj.payment_state(self.context.get('today'))


class IssueFeesSerializer(serializers.Serializer):
    category_id = serializers.IntegerField()
    title = serializers.CharField(max_length=180)
    amount = serializers.DecimalField(max_digits=12, decimal_places=2)
    discount = serializers.DecimalField(max_digits=12, decimal_places=2, required=False, default=0)
    due_date = serializers.DateField(required=False)
    installments = serializers.ListField(child=serializers.DictField(), required=False)
    scope = serializers.ChoiceField(choices=fee_service.TARGET_SCOPES, default='school')
    classroom_id = serializers.IntegerField(required=False)
    section_id = serializers.IntegerField(required=False)
    student_ids = serializers.ListField(child=serializers.IntegerField(), required=False, max_length=2000)
    confirm = serializers.BooleanField(default=False)

    def validate(self, attrs):
        installments = attrs.get('installments')
        if not installments and not attrs.get('due_date'):
            raise serializers.ValidationError({'due_date': ['أدخل تاريخ الاستحقاق أو أضف أقساطًا.']})
        parsed = []
        for item in installments or []:
            due = serializers.DateField().to_internal_value(item.get('due_date'))
            parsed.append({'amount': item.get('amount'), 'due_date': due})
        attrs['installments'] = parsed
        return attrs


class RecordPaymentSerializer(serializers.Serializer):
    amount = serializers.DecimalField(max_digits=12, decimal_places=2)
    method = serializers.ChoiceField(choices=METHODS)
    paid_on = serializers.DateField(required=False)
    reference = serializers.CharField(max_length=120, required=False, allow_blank=True, default='')


class ReasonSerializer(serializers.Serializer):
    reason = serializers.CharField(max_length=300)


class SubscriptionPlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubscriptionPlan
        fields = (
            'id', 'code', 'name', 'description', 'base_price', 'price_per_student', 'currency', 'billing_period',
            'max_students', 'features', 'is_active', 'sort_order',
        )

    def validate_features(self, value):
        if not isinstance(value, list) or not all(isinstance(item, str) and len(item) <= 120 for item in value):
            raise serializers.ValidationError('features must be a list of short strings.')
        return value[:30]


class SchoolSubscriptionSerializer(serializers.ModelSerializer):
    plan_name = serializers.CharField(source='plan.name', read_only=True)
    school_name = serializers.CharField(source='school.name', read_only=True)

    class Meta:
        model = SchoolSubscription
        fields = (
            'id', 'school', 'school_name', 'plan', 'plan_name', 'status', 'start_date', 'end_date',
            'student_limit', 'custom_price_per_student', 'notes', 'created_at',
        )
        read_only_fields = ('id', 'school_name', 'plan_name', 'created_at')


class PlatformInvoiceSerializer(serializers.ModelSerializer):
    school_name = serializers.CharField(source='school.name', read_only=True)
    balance = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)

    class Meta:
        model = PlatformInvoice
        fields = (
            'id', 'school', 'school_name', 'subscription', 'number', 'period_start', 'period_end',
            'student_count', 'amount', 'paid_amount', 'balance', 'currency', 'issued_on', 'due_date',
            'status', 'paid_at', 'notes',
        )


class IssueInvoiceSerializer(serializers.Serializer):
    subscription_id = serializers.IntegerField()
    period_start = serializers.DateField()
    period_end = serializers.DateField()
    due_date = serializers.DateField()
    student_count = serializers.IntegerField(required=False, min_value=0)
    notes = serializers.CharField(required=False, allow_blank=True, default='')


# --- School admin: fees ------------------------------------------------------

class FeeCategoryListCreateAPIView(APIView):
    permission_classes = (IsActiveSchoolUser,)

    @extend_schema(responses={200: FeeCategorySerializer(many=True)})
    def get(self, request):
        _school_admin(request)
        rows = FeeCategory.objects.filter(school=request.active_school)
        return Response(FeeCategorySerializer(rows, many=True).data)

    @extend_schema(request=FeeCategorySerializer, responses={201: FeeCategorySerializer})
    def post(self, request):
        _school_admin(request, write=True)
        serializer = FeeCategorySerializer(data=request.data, context={'school': request.active_school})
        serializer.is_valid(raise_exception=True)
        serializer.save(school=request.active_school)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class FeeCategoryDetailAPIView(APIView):
    permission_classes = (IsActiveSchoolUser,)

    @extend_schema(request=FeeCategorySerializer, responses={200: FeeCategorySerializer})
    def patch(self, request, pk):
        _school_admin(request, write=True)
        try:
            category = FeeCategory.objects.get(pk=pk, school=request.active_school)
        except FeeCategory.DoesNotExist as exc:
            raise NotFound('Fee category not found.') from exc
        serializer = FeeCategorySerializer(
            category, data=request.data, partial=True, context={'school': request.active_school},
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class StudentFeeListAPIView(APIView):
    permission_classes = (IsActiveSchoolUser,)

    @extend_schema(responses={200: StudentFeeSerializer(many=True)})
    def get(self, request):
        _school_admin(request)
        today = timezone.localdate()
        rows = fee_service.fees_queryset(request.active_school, request.active_academic_year)
        student_id, category_id = _int(request, 'student_id'), _int(request, 'category_id')
        classroom_id, section_id = _int(request, 'classroom_id'), _int(request, 'section_id')
        if student_id:
            rows = rows.filter(student_id=student_id)
        if category_id:
            rows = rows.filter(category_id=category_id)
        if classroom_id or section_id:
            enrollment = Q(student__enrollments__school=request.active_school,
                           student__enrollments__academic_year=request.active_academic_year,
                           student__enrollments__is_current=True)
            if classroom_id:
                enrollment &= Q(student__enrollments__classroom_id=classroom_id)
            if section_id:
                enrollment &= Q(student__enrollments__section_id=section_id)
            rows = rows.filter(enrollment).distinct()
        due_from, due_to = _date(request, 'due_from'), _date(request, 'due_to')
        if due_from and due_to and due_from > due_to:
            raise ValidationError({'due_from': 'due_from must not be after due_to.'})
        if due_from:
            rows = rows.filter(due_date__gte=due_from)
        if due_to:
            rows = rows.filter(due_date__lte=due_to)
        search = (request.query_params.get('search') or '').strip()
        if search:
            rows = rows.filter(Q(student__full_name__icontains=search) | Q(student__student_code__icontains=search)
                               | Q(title__icontains=search))
        rows = fee_service.filter_by_state(rows, request.query_params.get('state'), today)
        paginator = Pagination()
        page = paginator.paginate_queryset(rows.order_by('due_date', 'student__full_name', 'id'), request, view=self)
        data = StudentFeeSerializer(page, many=True, context={'today': today}).data
        response = paginator.get_paginated_response(data)
        response.data['summary'] = fee_service.summarize(rows, today)
        return response


class IssueFeesAPIView(APIView):
    permission_classes = (IsActiveSchoolUser,)

    @extend_schema(request=IssueFeesSerializer, responses={200: OpenApiTypes.OBJECT, 201: OpenApiTypes.OBJECT})
    def post(self, request):
        _school_admin(request, write=True)
        serializer = IssueFeesSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = dict(serializer.validated_data)
        confirm = data.pop('confirm')
        result = fee_service.issue_fees(
            school=request.active_school, year=request.active_academic_year, actor=request.user,
            data=data, confirm=confirm,
        )
        return Response(result, status=status.HTTP_201_CREATED if confirm else status.HTTP_200_OK)


def _admin_fee(request, pk):
    try:
        return StudentFee.objects.select_related('student', 'category').get(pk=pk, school=request.active_school)
    except StudentFee.DoesNotExist as exc:
        raise NotFound('Fee not found.') from exc


class StudentFeeDetailAPIView(APIView):
    permission_classes = (IsActiveSchoolUser,)

    @extend_schema(responses={200: OpenApiTypes.OBJECT})
    def get(self, request, pk):
        _school_admin(request)
        fee = _admin_fee(request, pk)
        payments = fee.payments.select_related('student_fee__student').order_by('-paid_on', '-id')
        return Response({
            **StudentFeeSerializer(fee, context={'today': timezone.localdate()}).data,
            'payments': FeePaymentSerializer(payments, many=True).data,
        })


class CancelFeeAPIView(APIView):
    permission_classes = (IsActiveSchoolUser,)

    @extend_schema(request=ReasonSerializer, responses={200: StudentFeeSerializer})
    def post(self, request, pk):
        _school_admin(request, write=True)
        serializer = ReasonSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        fee = fee_service.cancel_fee(school=request.active_school, fee_id=pk, reason=serializer.validated_data['reason'])
        return Response(StudentFeeSerializer(fee, context={'today': timezone.localdate()}).data)


class RecordFeePaymentAPIView(APIView):
    permission_classes = (IsActiveSchoolUser,)

    @extend_schema(request=RecordPaymentSerializer, responses={201: FeePaymentSerializer})
    def post(self, request, pk):
        _school_admin(request, write=True)
        serializer = RecordPaymentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        payment = fee_service.record_payment(
            school=request.active_school, fee_id=pk, actor=request.user, amount=data['amount'],
            method=data['method'], paid_on=data.get('paid_on') or timezone.localdate(), reference=data['reference'],
        )
        payment = FeePayment.objects.select_related('student_fee__student').get(pk=payment.pk)
        return Response(FeePaymentSerializer(payment).data, status=status.HTTP_201_CREATED)


class FeePaymentListAPIView(APIView):
    permission_classes = (IsActiveSchoolUser,)

    @extend_schema(responses={200: FeePaymentSerializer(many=True)})
    def get(self, request):
        _school_admin(request)
        rows = FeePayment.objects.filter(school=request.active_school).select_related('student_fee__student')
        if request.active_academic_year is not None:
            rows = rows.filter(student_fee__academic_year=request.active_academic_year)
        date_from, date_to = _date(request, 'date_from'), _date(request, 'date_to')
        if date_from and date_to and date_from > date_to:
            raise ValidationError({'date_from': 'date_from must not be after date_to.'})
        if date_from:
            rows = rows.filter(paid_on__gte=date_from)
        if date_to:
            rows = rows.filter(paid_on__lte=date_to)
        student_id = _int(request, 'student_id')
        if student_id:
            rows = rows.filter(student_fee__student_id=student_id)
        search = (request.query_params.get('search') or '').strip()
        if search:
            rows = rows.filter(Q(receipt_number__icontains=search) | Q(student_fee__student__full_name__icontains=search))
        paginator = Pagination()
        page = paginator.paginate_queryset(rows.order_by('-paid_on', '-id'), request, view=self)
        return paginator.get_paginated_response(FeePaymentSerializer(page, many=True).data)


class VoidFeePaymentAPIView(APIView):
    permission_classes = (IsActiveSchoolUser,)

    @extend_schema(request=ReasonSerializer, responses={200: FeePaymentSerializer})
    def post(self, request, pk):
        _school_admin(request, write=True)
        serializer = ReasonSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        payment = fee_service.void_payment(
            school=request.active_school, payment_id=pk, actor=request.user,
            reason=serializer.validated_data['reason'],
        )
        payment = FeePayment.objects.select_related('student_fee__student').get(pk=payment.pk)
        return Response(FeePaymentSerializer(payment).data)


class FeeSummaryAPIView(APIView):
    permission_classes = (IsActiveSchoolUser,)

    @extend_schema(responses={200: OpenApiTypes.OBJECT})
    def get(self, request):
        _school_admin(request)
        today = timezone.localdate()
        rows = fee_service.fees_queryset(request.active_school, request.active_academic_year)
        by_category = []
        for category in FeeCategory.objects.filter(school=request.active_school, fees__in=rows).distinct():
            by_category.append({'id': category.id, 'name': category.name,
                                **fee_service.summarize(rows.filter(category=category), today)})
        collected = FeePayment.objects.filter(
            school=request.active_school, is_void=False, paid_on__gte=today.replace(day=1),
        ).values_list('amount', flat=True)
        return Response({
            **fee_service.summarize(rows, today),
            'collected_this_month': str(sum(collected, start=fee_service.ZERO)),
            'by_category': by_category,
        })


# --- Parent: fees of own children --------------------------------------------

def _parent_fee_rows(request, student_id):
    _parent(request)
    if student_id not in fee_service.guardian_student_ids(request.active_membership):
        raise NotFound('Child not found.')
    return StudentFee.objects.filter(
        school=request.active_membership.school, student_id=student_id,
    ).select_related('category')


class ParentChildFeesAPIView(APIView):
    """Read-only; available in historical parent contexts for the old school."""

    permission_classes = (IsActiveSchoolUser,)

    @extend_schema(responses={200: OpenApiTypes.OBJECT})
    def get(self, request, student_id):
        rows = _parent_fee_rows(request, student_id)
        today = timezone.localdate()
        visible = rows.exclude(status='cancelled').order_by('due_date', 'id')
        payments = FeePayment.objects.filter(
            student_fee__in=rows, is_void=False,
        ).select_related('student_fee__student').order_by('-paid_on', '-id')
        return Response({
            'student_id': student_id,
            'summary': fee_service.summarize(rows, today),
            'fees': StudentFeeSerializer(visible, many=True, context={'today': today}).data,
            'payments': FeePaymentSerializer(payments, many=True).data,
        })


class ParentFeesOverviewAPIView(APIView):
    """One summary per child for the parent home screen alert."""

    permission_classes = (IsActiveSchoolUser,)

    @extend_schema(responses={200: OpenApiTypes.OBJECT})
    def get(self, request):
        _parent(request)
        today = timezone.localdate()
        children = []
        school = request.active_membership.school
        for student_id in sorted(fee_service.guardian_student_ids(request.active_membership)):
            rows = StudentFee.objects.filter(school=school, student_id=student_id)
            first = rows.select_related('student').first()
            if first is None:
                continue
            children.append({'student_id': student_id, 'student_name': first.student.full_name,
                             **fee_service.summarize(rows, today)})
        return Response({'children': children})


# --- School admin: own subscription (read-only) ------------------------------

class SchoolSubscriptionStatusAPIView(APIView):
    permission_classes = (IsActiveSchoolUser,)

    @extend_schema(responses={200: OpenApiTypes.OBJECT})
    def get(self, request):
        _school_admin(request)
        school = request.active_school
        invoices = PlatformInvoice.objects.filter(school=school).select_related('school')[:24]
        return Response({
            **subscription_service.school_subscription_status(school),
            'invoices': PlatformInvoiceSerializer(invoices, many=True).data,
        })


# --- Platform owner ----------------------------------------------------------

class PlatformSummaryAPIView(APIView):
    permission_classes = (IsActiveSchoolUser,)

    @extend_schema(responses={200: OpenApiTypes.OBJECT})
    def get(self, request):
        _platform_owner(request)
        return Response(subscription_service.platform_summary())


class PlatformPlanListCreateAPIView(APIView):
    permission_classes = (IsActiveSchoolUser,)

    @extend_schema(responses={200: SubscriptionPlanSerializer(many=True)})
    def get(self, request):
        _platform_owner(request)
        return Response(SubscriptionPlanSerializer(SubscriptionPlan.objects.all(), many=True).data)

    @extend_schema(request=SubscriptionPlanSerializer, responses={201: SubscriptionPlanSerializer})
    def post(self, request):
        _platform_owner(request)
        serializer = SubscriptionPlanSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class PlatformPlanDetailAPIView(APIView):
    permission_classes = (IsActiveSchoolUser,)

    @extend_schema(request=SubscriptionPlanSerializer, responses={200: SubscriptionPlanSerializer})
    def patch(self, request, pk):
        _platform_owner(request)
        try:
            plan = SubscriptionPlan.objects.get(pk=pk)
        except SubscriptionPlan.DoesNotExist as exc:
            raise NotFound('Plan not found.') from exc
        serializer = SubscriptionPlanSerializer(plan, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class PlatformSchoolListAPIView(APIView):
    permission_classes = (IsActiveSchoolUser,)

    @extend_schema(responses={200: OpenApiTypes.OBJECT})
    def get(self, request):
        _platform_owner(request)
        warning = request.query_params.get('warning')
        rows = []
        for school in School.objects.order_by('name'):
            item = subscription_service.school_subscription_status(school)
            if warning and item.get('warning') != warning:
                continue
            rows.append({'school_id': school.id, 'school_name': school.name, 'school_code': school.code,
                         'is_active': school.is_active, **item})
        return Response({'count': len(rows), 'results': rows})


class PlatformSubscriptionCreateAPIView(APIView):
    permission_classes = (IsActiveSchoolUser,)

    @extend_schema(request=SchoolSubscriptionSerializer, responses={201: SchoolSubscriptionSerializer})
    def post(self, request):
        _platform_owner(request)
        serializer = SchoolSubscriptionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        subscription = subscription_service.create_subscription(
            school=data['school'], plan=data['plan'], start_date=data['start_date'], end_date=data['end_date'],
            actor=request.user, status=data.get('status', 'trial'), student_limit=data.get('student_limit'),
            custom_price_per_student=data.get('custom_price_per_student'), notes=data.get('notes', ''),
        )
        return Response(SchoolSubscriptionSerializer(subscription).data, status=status.HTTP_201_CREATED)


class PlatformSubscriptionDetailAPIView(APIView):
    permission_classes = (IsActiveSchoolUser,)
    EDITABLE = ('status', 'end_date', 'student_limit', 'custom_price_per_student', 'notes')

    @extend_schema(request=SchoolSubscriptionSerializer, responses={200: SchoolSubscriptionSerializer})
    def patch(self, request, pk):
        _platform_owner(request)
        unknown = set(request.data) - set(self.EDITABLE)
        if unknown:
            raise ValidationError({'detail': f'Fields not editable: {", ".join(sorted(unknown))}.'})
        serializer = SchoolSubscriptionSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        subscription = subscription_service.update_subscription(subscription_id=pk, data=serializer.validated_data)
        return Response(SchoolSubscriptionSerializer(subscription).data)


class PlatformInvoiceListCreateAPIView(APIView):
    permission_classes = (IsActiveSchoolUser,)

    @extend_schema(responses={200: PlatformInvoiceSerializer(many=True)})
    def get(self, request):
        _platform_owner(request)
        rows = PlatformInvoice.objects.select_related('school')
        school_id = _int(request, 'school_id')
        if school_id:
            rows = rows.filter(school_id=school_id)
        invoice_status = request.query_params.get('status')
        if invoice_status:
            rows = rows.filter(status=invoice_status)
        paginator = Pagination()
        page = paginator.paginate_queryset(rows, request, view=self)
        return paginator.get_paginated_response(PlatformInvoiceSerializer(page, many=True).data)

    @extend_schema(request=IssueInvoiceSerializer, responses={201: PlatformInvoiceSerializer})
    def post(self, request):
        _platform_owner(request)
        serializer = IssueInvoiceSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        invoice = subscription_service.issue_invoice(**serializer.validated_data)
        return Response(PlatformInvoiceSerializer(invoice).data, status=status.HTTP_201_CREATED)


class PlatformInvoicePaymentAPIView(APIView):
    permission_classes = (IsActiveSchoolUser,)

    @extend_schema(request=RecordPaymentSerializer, responses={201: PlatformInvoiceSerializer})
    def post(self, request, pk):
        _platform_owner(request)
        serializer = RecordPaymentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        subscription_service.record_platform_payment(
            invoice_id=pk, actor=request.user, amount=data['amount'], method=data['method'],
            paid_on=data.get('paid_on') or timezone.localdate(), reference=data['reference'],
        )
        invoice = PlatformInvoice.objects.select_related('school').get(pk=pk)
        return Response(PlatformInvoiceSerializer(invoice).data, status=status.HTTP_201_CREATED)


class PlatformInvoiceVoidAPIView(APIView):
    permission_classes = (IsActiveSchoolUser,)

    @extend_schema(request=ReasonSerializer, responses={200: PlatformInvoiceSerializer})
    def post(self, request, pk):
        _platform_owner(request)
        serializer = ReasonSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        invoice = subscription_service.void_invoice(invoice_id=pk, reason=serializer.validated_data['reason'])
        return Response(PlatformInvoiceSerializer(invoice).data)
