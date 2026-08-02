from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema
from rest_framework import generics, serializers, status
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from rest_framework.views import APIView

from .messaging_serializers import ConversationSerializer, ConversationStartSerializer, MessageCreateSerializer, MessageSerializer
from .messaging_views import _conversation_queryset
from .models import Conversation, SchoolMembership, TeacherAssignment
from .permissions import IsActiveSchoolUser
from .services.messaging import (
    assign_school_support, broadcast_notification, conversations_for_membership,
    get_context_unread_conversation_counts, send_message, set_conversation_status,
    start_school_support_conversation,
)
from .services.notifications import get_unread_notification_count


class SchoolInboxCreateSerializer(serializers.Serializer):
    subject=serializers.CharField(max_length=200); category=serializers.ChoiceField(choices=tuple(choice for choice in Conversation.CATEGORY_CHOICES if choice[0])); priority=serializers.ChoiceField(choices=Conversation.PRIORITY_CHOICES,default='normal'); message=serializers.CharField(max_length=4000,required=False)


class SupportAssignSerializer(serializers.Serializer): membership_id=serializers.IntegerField(required=False,min_value=1)
class SupportStatusSerializer(serializers.Serializer): status=serializers.ChoiceField(choices=Conversation.STATUS_CHOICES); resolution_note=serializers.CharField(required=False,allow_blank=True,max_length=1000)
class BroadcastActionParamsSerializer(serializers.Serializer):
    homework_id = serializers.IntegerField(required=False, min_value=1)
    student_id = serializers.IntegerField(required=False, min_value=1)


class BroadcastActionSerializer(serializers.Serializer):
    route = serializers.ChoiceField(
        choices=('homework_detail', 'conversation_start', 'school_home'),
    )
    params = BroadcastActionParamsSerializer(required=False, default=dict)


class BroadcastSerializer(serializers.Serializer):
    teacher_assignment_id = serializers.IntegerField(min_value=1)
    student_ids = serializers.ListField(
        child=serializers.IntegerField(min_value=1), required=False, default=list,
    )
    audience = serializers.ChoiceField(
        choices=('students', 'parents', 'students_and_parents'),
    )
    title = serializers.CharField(max_length=200)
    body = serializers.CharField(max_length=500)
    action = BroadcastActionSerializer(required=False, default=dict)


class SchoolInboxListCreateAPIView(generics.ListAPIView):
    serializer_class=ConversationSerializer; permission_classes=(IsActiveSchoolUser,); throttle_scope='school_support_create'
    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Conversation.objects.none()
        return _conversation_queryset(self.request).filter(conversation_type='school_support').order_by('-last_message_at','-created_at','-id')
    @extend_schema(request=SchoolInboxCreateSerializer,responses={201:ConversationSerializer})
    def post(self,request):
        if request.active_role not in ('student','parent','teacher'):
            raise PermissionDenied('This role cannot create school support.')
        payload=SchoolInboxCreateSerializer(data=request.data); payload.is_valid(raise_exception=True); data=payload.validated_data
        conversation, _ = start_school_support_conversation(
            creator_membership=request.active_membership, subject=data['subject'],
            category=data['category'], priority=data['priority'], request=request,
        )
        if data.get('message'): send_message(conversation=conversation,sender_membership=request.active_membership,body=data['message'],request=request)
        conversation=_conversation_queryset(request).get(pk=conversation.pk); return Response(ConversationSerializer(conversation,context={'request':request}).data,status=201)


class SchoolInboxDetailAPIView(generics.RetrieveAPIView):
    serializer_class=ConversationSerializer; permission_classes=(IsActiveSchoolUser,)
    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Conversation.objects.none()
        return _conversation_queryset(self.request).filter(conversation_type='school_support').order_by('-last_message_at','-created_at','-id')


class SchoolInboxAssignAPIView(APIView):
    permission_classes=(IsActiveSchoolUser,)
    @extend_schema(request=SupportAssignSerializer,responses={200:ConversationSerializer})
    def post(self,request,pk):
        if request.active_role != 'school_admin':
            raise PermissionDenied('School administrator access is required.')
        conversation=generics.get_object_or_404(conversations_for_membership(request.active_membership).filter(conversation_type='school_support'),pk=pk); payload=SupportAssignSerializer(data=request.data); payload.is_valid(raise_exception=True)
        assignee=SchoolMembership.objects.filter(pk=payload.validated_data.get('membership_id',request.active_membership.pk),school=request.active_school,role='school_admin',status='active').first()
        if assignee is None: raise serializers.ValidationError('Support assignee was not found.')
        item=assign_school_support(conversation=conversation,actor_membership=request.active_membership,assignee_membership=assignee,request=request); return Response(ConversationSerializer(item,context={'request':request}).data)


class SchoolInboxStatusAPIView(APIView):
    permission_classes=(IsActiveSchoolUser,)
    @extend_schema(request=SupportStatusSerializer,responses={200:ConversationSerializer})
    def post(self,request,pk):
        conversation=generics.get_object_or_404(conversations_for_membership(request.active_membership).filter(conversation_type='school_support'),pk=pk); payload=SupportStatusSerializer(data=request.data); payload.is_valid(raise_exception=True)
        item = set_conversation_status(
            conversation=conversation, membership=request.active_membership,
            status=payload.validated_data['status'],
            resolution_note=payload.validated_data.get('resolution_note', ''), request=request,
        )
        return Response(ConversationSerializer(item, context={'request': request}).data)


class SchoolInboxReplyAPIView(APIView):
    permission_classes=(IsActiveSchoolUser,); throttle_scope='school_support_reply'
    @extend_schema(request=MessageCreateSerializer,responses={201:MessageSerializer})
    def post(self,request,pk):
        conversation=generics.get_object_or_404(conversations_for_membership(request.active_membership).filter(conversation_type='school_support'),pk=pk); payload=MessageCreateSerializer(data=request.data); payload.is_valid(raise_exception=True); message=send_message(conversation=conversation,sender_membership=request.active_membership,body=payload.validated_data['body'],request=request); return Response(MessageSerializer(message).data,status=201)


class NotificationBroadcastAPIView(APIView):
    permission_classes=(IsActiveSchoolUser,); throttle_scope='notification_broadcast'
    @extend_schema(request=BroadcastSerializer,responses={200:OpenApiTypes.OBJECT})
    def post(self,request):
        payload=BroadcastSerializer(data=request.data); payload.is_valid(raise_exception=True); data=payload.validated_data
        assignment=generics.get_object_or_404(TeacherAssignment.objects.filter(school=request.active_school),pk=data['teacher_assignment_id'])
        return Response(broadcast_notification(actor_membership=request.active_membership,teacher_assignment=assignment,student_ids=data['student_ids'],audience=data['audience'],title=data['title'],body=data['body'],action=data['action'],request=request))


class CommunicationBadgesAPIView(APIView):
    permission_classes=(IsActiveSchoolUser,); throttle_scope='notification_list'
    @extend_schema(responses={200:OpenApiTypes.OBJECT})
    def get(self,request):
        membership=request.active_membership; notification_count=get_unread_notification_count(membership); conversation_count=get_context_unread_conversation_counts([membership]).get(membership.pk,0); inbox=conversations_for_membership(membership).filter(conversation_type='school_support',status__in=('open','in_progress')).count() if request.active_role=='school_admin' else 0
        return Response({'notification_unread':notification_count,'conversation_unread':conversation_count,'school_inbox_open_count':inbox,'total_badge_count':notification_count+conversation_count})