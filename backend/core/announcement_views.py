from django.db.models import Count, Prefetch, Q
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema
from rest_framework import generics, status
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from .announcement_serializers import (
    AnnouncementAttachmentSerializer, AnnouncementInquirySerializer, AnnouncementQuerySerializer,
    AnnouncementReceiptSerializer, AnnouncementSerializer,
    AnnouncementSummarySerializer, AnnouncementTargetPreviewSerializer, AnnouncementWriteSerializer,
)
from .models import Announcement, AnnouncementAttachment, AnnouncementReceipt
from .messaging_serializers import ConversationSerializer
from .services.messaging import (
    start_school_support_conversation, start_teacher_parent_conversation,
    start_teacher_student_conversation,
)
from .pagination import StandardResultsSetPagination
from .permissions import IsActiveSchoolUser
from .services.announcements import (
    add_announcement_attachments, announcements_for_context,
    archive_announcement, close_announcement, delete_announcement_attachment,
    mark_announcement_read, publish_announcement,
)


class AnnouncementListCreateAPIView(generics.ListCreateAPIView):
    queryset = Announcement.objects.none()
    # All announcement filters are validated and applied explicitly below.
    # Disable global DRF filter backends to prevent a second implicit filtering
    # pass from changing the membership-scoped queryset.
    filter_backends = ()
    permission_classes = (IsActiveSchoolUser,)
    pagination_class = StandardResultsSetPagination
    throttle_scope = 'announcement_list'

    def get_serializer_class(self):
        return AnnouncementWriteSerializer if self.request.method == 'POST' else AnnouncementSerializer

    @extend_schema(parameters=[AnnouncementQuerySerializer], responses={200: AnnouncementSerializer(many=True)})
    def get(self, request, *args, **kwargs):
        # Keep the list pipeline explicit because the project has global filter
        # backends enabled. The queryset is already fully validated and filtered
        # in get_queryset(), so a second backend pass is neither needed nor safe.
        queryset = self.get_queryset()
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = AnnouncementSerializer(page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)
        serializer = AnnouncementSerializer(queryset, many=True, context={'request': request})
        return Response(serializer.data)

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Announcement.objects.none()
        query = AnnouncementQuerySerializer(data=self.request.query_params)
        query.is_valid(raise_exception=True)
        params = query.validated_data
        membership = self.request.active_membership
        queryset = announcements_for_context(membership).prefetch_related(
            Prefetch(
                'receipts',
                queryset=AnnouncementReceipt.objects.filter(recipient_membership=membership),
                to_attr='_context_receipts',
            ),
            'target_students',
        )
        for field in ('status', 'priority', 'audience_type', 'academic_year_id'):
            if field in params:
                queryset = queryset.filter(**{field: params[field]})
        if 'unread' in params:
            if params['unread']:
                queryset = queryset.filter(receipts__recipient_membership=membership, receipts__read_at__isnull=True)
            else:
                queryset = queryset.filter(receipts__recipient_membership=membership, receipts__read_at__isnull=False)
        if params.get('published_from'):
            queryset = queryset.filter(published_at__gte=params['published_from'])
        if params.get('published_to'):
            queryset = queryset.filter(published_at__lte=params['published_to'])
        if params.get('search'):
            queryset = queryset.filter(Q(title__icontains=params['search']) | Q(body__icontains=params['search']))
        return queryset.distinct().order_by(params['ordering'], '-id')

    @extend_schema(request=AnnouncementWriteSerializer, responses={201: AnnouncementSerializer})
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        item = serializer.save()
        return Response(
            AnnouncementSerializer(item, context={'request': request}).data,
            status=status.HTTP_201_CREATED,
        )


class AnnouncementDetailAPIView(generics.RetrieveUpdateAPIView):
    queryset = Announcement.objects.none()
    permission_classes = (IsActiveSchoolUser,)
    throttle_scope = 'announcement_list'

    def get_serializer_class(self):
        return AnnouncementWriteSerializer if self.request.method in ('PUT', 'PATCH') else AnnouncementSerializer

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Announcement.objects.none()
        membership = self.request.active_membership
        return announcements_for_context(membership).prefetch_related(
            Prefetch(
                'receipts',
                queryset=AnnouncementReceipt.objects.filter(recipient_membership=membership),
                to_attr='_context_receipts',
            ),
            'target_students',
        )

    @extend_schema(request=AnnouncementWriteSerializer, responses={200: AnnouncementSerializer})
    def update(self, request, *args, **kwargs):
        super().update(request, *args, **kwargs)
        item = self.get_queryset().get(pk=kwargs['pk'])
        return Response(AnnouncementSerializer(item, context={'request': request}).data)


class AnnouncementPublishAPIView(AnnouncementDetailAPIView):
    throttle_scope = 'announcement_write'
    @extend_schema(request=None, responses={200: AnnouncementSerializer})
    def post(self, request, *args, **kwargs):
        item = publish_announcement(
            announcement=self.get_object(), membership=request.active_membership, request=request,
        )
        return Response(AnnouncementSerializer(item, context={'request': request}).data)


class AnnouncementCloseAPIView(AnnouncementDetailAPIView):
    throttle_scope = 'announcement_write'
    @extend_schema(request=None, responses={200: AnnouncementSerializer})
    def post(self, request, *args, **kwargs):
        item = close_announcement(
            announcement=self.get_object(), membership=request.active_membership, request=request,
        )
        return Response(AnnouncementSerializer(item, context={'request': request}).data)


class AnnouncementArchiveAPIView(AnnouncementDetailAPIView):
    throttle_scope = 'announcement_write'
    @extend_schema(request=None, responses={200: AnnouncementSerializer})
    def post(self, request, *args, **kwargs):
        item = archive_announcement(
            announcement=self.get_object(), membership=request.active_membership, request=request,
        )
        return Response(AnnouncementSerializer(item, context={'request': request}).data)


class AnnouncementReadAPIView(AnnouncementDetailAPIView):
    throttle_scope = 'announcement_read'
    @extend_schema(request=None, responses={200: AnnouncementReceiptSerializer})
    def post(self, request, *args, **kwargs):
        receipt = mark_announcement_read(
            announcement=self.get_object(), membership=request.active_membership,
        )
        return Response({
            'announcement_id': receipt.announcement_id,
            'is_read': True,
            'read_at': receipt.read_at,
        })


class AnnouncementSummaryAPIView(AnnouncementDetailAPIView):
    throttle_scope = 'reports'
    @extend_schema(responses={200: AnnouncementSummarySerializer})
    def get(self, request, *args, **kwargs):
        announcement = self.get_object()
        membership = request.active_membership
        if membership.role not in ('super_admin', 'school_admin') and announcement.created_by_membership_id != membership.pk:
            return Response(status=status.HTTP_404_NOT_FOUND)
        aggregate = announcement.receipts.aggregate(
            delivered_count=Count('id'),
            read_count=Count('id', filter=Q(read_at__isnull=False)),
            unread_count=Count('id', filter=Q(read_at__isnull=True)),
        )
        delivered = aggregate['delivered_count'] or 0
        aggregate['announcement_id'] = announcement.pk
        aggregate['read_rate'] = round((aggregate['read_count'] / delivered * 100), 2) if delivered else 0.0
        by_role = {}
        for row in announcement.receipts.values('recipient_membership__role').annotate(
            delivered=Count('id'),
            read=Count('id', filter=Q(read_at__isnull=False)),
        ):
            role = row['recipient_membership__role']
            by_role[role] = {
                'delivered_count': row['delivered'],
                'read_count': row['read'],
                'unread_count': row['delivered'] - row['read'],
            }
        aggregate['by_role'] = by_role
        return Response(aggregate)


class AnnouncementAttachmentAPIView(AnnouncementDetailAPIView):
    http_method_names = ('get', 'post', 'head', 'options')
    parser_classes = (MultiPartParser,)
    throttle_scope = 'announcement_attachment_upload'

    @extend_schema(responses={200: AnnouncementAttachmentSerializer(many=True)})
    def get(self, request, *args, **kwargs):
        return Response(AnnouncementAttachmentSerializer(self.get_object().attachments.all(), many=True).data)

    @extend_schema(request={'multipart/form-data': OpenApiTypes.BINARY}, responses={201: AnnouncementAttachmentSerializer(many=True)})
    def post(self, request, *args, **kwargs):
        files = request.FILES.getlist('files') or ([request.FILES['file']] if 'file' in request.FILES else [])
        if not files:
            return Response({'files': ['At least one file is required.']}, status=status.HTTP_400_BAD_REQUEST)
        rows = add_announcement_attachments(
            announcement=self.get_object(), membership=request.active_membership, files=files,
        )
        return Response(AnnouncementAttachmentSerializer(rows, many=True).data, status=status.HTTP_201_CREATED)


class AnnouncementAttachmentDeleteAPIView(AnnouncementDetailAPIView):
    http_method_names = ('delete', 'head', 'options')
    throttle_scope = 'announcement_attachment_upload'
    @extend_schema(request=None, responses={204: None})
    def delete(self, request, *args, **kwargs):
        attachment = AnnouncementAttachment.objects.filter(
            pk=kwargs['attachment_id'], announcement=self.get_object(),
        ).first()
        if attachment is None:
            return Response(status=status.HTTP_404_NOT_FOUND)
        delete_announcement_attachment(attachment=attachment, membership=request.active_membership)
        return Response(status=status.HTTP_204_NO_CONTENT)


class AnnouncementInquiryAPIView(AnnouncementDetailAPIView):
    throttle_scope = 'conversation_list'

    @extend_schema(request=AnnouncementInquirySerializer, responses={200: ConversationSerializer})
    def post(self, request, *args, **kwargs):
        announcement = self.get_object()
        membership = request.active_membership
        if not AnnouncementReceipt.objects.filter(announcement=announcement, recipient_membership=membership).exists():
            return Response(status=status.HTTP_404_NOT_FOUND)
        if not announcement.allow_inquiry or announcement.status not in ('published', 'closed'):
            return Response({'detail': 'Inquiry is not available for this announcement.'}, status=status.HTTP_400_BAD_REQUEST)
        payload = AnnouncementInquirySerializer(data=request.data)
        payload.is_valid(raise_exception=True)
        subject = f'Announcement inquiry: {announcement.title}'[:200]
        if announcement.teacher_assignment_id and membership.role == 'student':
            conversation, _ = start_teacher_student_conversation(
                creator_membership=membership,
                assignment_id=announcement.teacher_assignment_id,
                subject=subject,
                academic_year_id=announcement.academic_year_id,
                request=request,
            )
        elif announcement.teacher_assignment_id and membership.role == 'parent':
            student_id = payload.validated_data.get('student_id')
            if not student_id:
                return Response({'student_id': ['This field is required.']}, status=status.HTTP_400_BAD_REQUEST)
            conversation, _ = start_teacher_parent_conversation(
                creator_membership=membership,
                assignment_id=announcement.teacher_assignment_id,
                student_id=student_id,
                subject=subject,
                academic_year_id=announcement.academic_year_id,
                request=request,
            )
        else:
            conversation, _ = start_school_support_conversation(
                creator_membership=membership,
                subject=subject,
                category='academic_inquiry',
                request=request,
            )
        return Response(ConversationSerializer(conversation, context={'request': request}).data)


class AnnouncementTargetPreviewAPIView(AnnouncementDetailAPIView):
    throttle_scope = 'reports'

    @extend_schema(responses={200: AnnouncementTargetPreviewSerializer})
    def get(self, request, *args, **kwargs):
        announcement = self.get_object()
        membership = request.active_membership
        if membership.role not in ('super_admin', 'school_admin') and announcement.created_by_membership_id != membership.pk:
            return Response(status=status.HTTP_404_NOT_FOUND)
        from .services.announcements import resolve_recipient_memberships
        queryset = resolve_recipient_memberships(announcement)
        by_role = {row['role']: row['total'] for row in queryset.values('role').annotate(total=Count('id'))}
        return Response({
            'announcement_id': announcement.pk,
            'eligible_count': sum(by_role.values()),
            'by_role': by_role,
        })
