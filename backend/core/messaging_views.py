from django.db.models import Count, DateTimeField, F, OuterRef, Prefetch, Q, Subquery
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema
from rest_framework import generics, status
from rest_framework.pagination import CursorPagination
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from .messaging_serializers import ConversationQuerySerializer, ConversationSerializer, ConversationStartSerializer, MessageAttachmentSerializer, MessageCreateSerializer, MessageSerializer
from .models import Conversation, ConversationParticipant, Message, MessageAttachment
from .permissions import IsActiveSchoolUser
from .services.messaging import (
    add_message_attachments, conversations_for_membership, delete_message_attachment,
    mark_conversation_read, send_message, set_conversation_status,
    start_homework_conversation, start_school_support_conversation,
    start_teacher_parent_conversation, start_teacher_student_conversation,
)


class MessageCursorPagination(CursorPagination):
    page_size=30; ordering=('created_at','id'); cursor_query_param='cursor'


def _conversation_queryset(request):
    membership=request.active_membership
    last_read=ConversationParticipant.objects.filter(conversation_id=OuterRef('pk'),membership=membership,is_active=True).values('last_read_at')[:1]
    queryset=conversations_for_membership(membership).annotate(
        _current_last_read=Subquery(last_read,output_field=DateTimeField()),
    ).annotate(unread_messages_count=Count(
        'messages',filter=(~Q(messages__sender_membership=membership) & (Q(_current_last_read__isnull=True)|Q(messages__created_at__gt=F('_current_last_read')))),distinct=True,
    )).prefetch_related(Prefetch('messages',queryset=Message.objects.select_related('sender_membership__user').order_by('-created_at')[:1],to_attr='_last_messages'))
    return queryset


class ConversationListAPIView(generics.ListAPIView):
    serializer_class=ConversationSerializer; permission_classes=(IsActiveSchoolUser,); throttle_scope='conversation_list'
    @extend_schema(parameters=[ConversationQuerySerializer])
    def get(self,request,*args,**kwargs): return super().get(request,*args,**kwargs)
    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Conversation.objects.none()
        query=ConversationQuerySerializer(data=self.request.query_params); query.is_valid(raise_exception=True); p=query.validated_data
        qs=_conversation_queryset(self.request)
        for key in ('conversation_type','status','category'):
            if key in p: qs=qs.filter(**{key:p[key]})
        if p.get('related_homework_id'): qs=qs.filter(related_type='homework',related_id=p['related_homework_id'])
        if p.get('student_id'): qs=qs.filter(related_type='student',related_id=p['student_id'])
        if p.get('assigned_to_me'): qs=qs.filter(assigned_to_membership=self.request.active_membership)
        if p.get('updated_from'): qs=qs.filter(updated_at__gte=p['updated_from'])
        if p.get('updated_to'): qs=qs.filter(updated_at__lte=p['updated_to'])
        if p.get('search'): qs=qs.filter(subject__icontains=p['search'])
        if p.get('unread_only'): qs=qs.filter(unread_messages_count__gt=0)
        return qs.order_by(p['ordering'],'-id')


class ConversationStartAPIView(APIView):
    permission_classes=(IsActiveSchoolUser,); throttle_scope='message_send'
    @extend_schema(request=ConversationStartSerializer,responses={201:ConversationSerializer,200:ConversationSerializer})
    def post(self,request):
        payload = ConversationStartSerializer(data=request.data, context={'request': request})
        payload.is_valid(raise_exception=True)
        data = payload.validated_data
        common = {
            'creator_membership': request.active_membership, 'subject': data['subject'],
            'academic_year_id': getattr(request.active_academic_year, 'pk', None),
            'request': request,
        }
        kind = data['conversation_type']
        if kind == 'teacher_student':
            conversation, created = start_teacher_student_conversation(
                assignment_id=data.get('teacher_assignment_id'),
                student_id=data.get('student_id'), **common,
            )
        elif kind == 'teacher_parent':
            conversation, created = start_teacher_parent_conversation(
                assignment_id=data.get('teacher_assignment_id'), student_id=data.get('student_id'),
                parent_membership_id=data.get('parent_membership_id'),
                parent_id=data.get('parent_id'), **common,
            )
        elif kind == 'homework_discussion':
            conversation, created = start_homework_conversation(
                homework_id=data.get('homework_id'), student_id=data.get('student_id'),
                parent_membership_id=data.get('parent_membership_id'), **common,
            )
        else:
            common.pop('academic_year_id')
            conversation, created = start_school_support_conversation(
                category=data.get('category', 'other'), priority=data['priority'], **common,
            )
        conversation=_conversation_queryset(request).get(pk=conversation.pk)
        return Response(ConversationSerializer(conversation,context={'request':request}).data,status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)


class ConversationDetailAPIView(generics.RetrieveAPIView):
    serializer_class=ConversationSerializer; permission_classes=(IsActiveSchoolUser,)
    def get_queryset(self): return _conversation_queryset(self.request)


class ConversationMessagesAPIView(generics.ListAPIView):
    serializer_class=MessageSerializer; permission_classes=(IsActiveSchoolUser,); pagination_class=MessageCursorPagination; throttle_scope='conversation_list'
    def conversation(self): return generics.get_object_or_404(conversations_for_membership(self.request.active_membership),pk=self.kwargs['pk'])
    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Message.objects.none()
        return self.conversation().messages.select_related('sender_membership__user').prefetch_related('attachments').order_by('created_at','id')
    @extend_schema(request=MessageCreateSerializer,responses={201:MessageSerializer})
    def post(self,request,pk):
        conversation=self.conversation(); payload=MessageCreateSerializer(data=request.data); payload.is_valid(raise_exception=True)
        reply=None
        if payload.validated_data.get('reply_to_id'): reply=generics.get_object_or_404(Message.objects.filter(conversation=conversation),pk=payload.validated_data['reply_to_id'])
        message=send_message(conversation=conversation,sender_membership=request.active_membership,body=payload.validated_data['body'],reply_to=reply,request=request)
        return Response(MessageSerializer(message,context={'request':request}).data,status=201)


class ConversationReadAPIView(APIView):
    permission_classes=(IsActiveSchoolUser,)
    @extend_schema(request=None,responses={200:OpenApiTypes.OBJECT})
    def post(self,request,pk):
        conversation=generics.get_object_or_404(conversations_for_membership(request.active_membership),pk=pk); participant=mark_conversation_read(conversation=conversation,membership=request.active_membership); return Response({'last_read_at':participant.last_read_at})


class ConversationStatusAPIView(APIView):
    permission_classes=(IsActiveSchoolUser,); target='closed'
    @extend_schema(request=None,responses={200:ConversationSerializer})
    def post(self,request,pk):
        conversation=generics.get_object_or_404(conversations_for_membership(request.active_membership),pk=pk); item=set_conversation_status(conversation=conversation,membership=request.active_membership,status=self.target,request=request); return Response(ConversationSerializer(item,context={'request':request}).data)
class ConversationCloseAPIView(ConversationStatusAPIView): target='closed'
class ConversationReopenAPIView(ConversationStatusAPIView): target='open'


class MessageAttachmentAPIView(APIView):
    permission_classes=(IsActiveSchoolUser,); parser_classes=(MultiPartParser,FormParser); throttle_scope='message_attachment_upload'
    def message(self,request,pk):
        conversations=conversations_for_membership(request.active_membership).values('pk'); return generics.get_object_or_404(Message.objects.filter(conversation_id__in=conversations).select_related('sender_membership'),pk=pk)
    @extend_schema(responses={200:MessageAttachmentSerializer(many=True)})
    def get(self,request,pk): return Response(MessageAttachmentSerializer(self.message(request,pk).attachments.all(),many=True).data)
    @extend_schema(request={'multipart/form-data':OpenApiTypes.BINARY},responses={201:MessageAttachmentSerializer(many=True)})
    def post(self,request,pk):
        created=add_message_attachments(message=self.message(request,pk),membership=request.active_membership,files=request.FILES.getlist('files')); return Response(MessageAttachmentSerializer(created,many=True).data,status=201)


class MessageAttachmentDeleteAPIView(MessageAttachmentAPIView):
    http_method_names=('delete','options')
    @extend_schema(request=None,responses={204:None})
    def delete(self,request,pk,attachment_id):
        message=self.message(request,pk); attachment=generics.get_object_or_404(MessageAttachment.objects.filter(message=message),pk=attachment_id); delete_message_attachment(attachment=attachment,membership=request.active_membership); return Response(status=204)