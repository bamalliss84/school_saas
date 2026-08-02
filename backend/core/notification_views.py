from drf_spectacular.utils import extend_schema
from rest_framework import generics
from rest_framework.response import Response
from rest_framework.views import APIView

from .context import get_active_membership
from .notification_serializers import NotificationQuerySerializer, NotificationReadAllSerializer, NotificationSerializer, NotificationUnreadSerializer
from .pagination import StandardResultsSetPagination
from .permissions import IsActiveSchoolUser
from .services.notifications import get_unread_notification_count, mark_all_notifications_read, mark_notification_read, notifications_for_membership


class NotificationListAPIView(generics.ListAPIView):
    serializer_class = NotificationSerializer
    permission_classes = (IsActiveSchoolUser,)
    pagination_class = StandardResultsSetPagination
    throttle_scope = 'notification_list'

    @extend_schema(parameters=[NotificationQuerySerializer])
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        query = NotificationQuerySerializer(data=self.request.query_params)
        query.is_valid(raise_exception=True)
        params = query.validated_data
        queryset = notifications_for_membership(get_active_membership(self.request))
        for key in ('is_read', 'notification_type', 'source_type'):
            if key in params:
                queryset = queryset.filter(**{key: params[key]})
        if params.get('date_from'):
            queryset = queryset.filter(created_at__gte=params['date_from'])
        if params.get('date_to'):
            queryset = queryset.filter(created_at__lte=params['date_to'])
        return queryset.order_by(params['ordering'], '-id')


class NotificationDetailAPIView(generics.RetrieveAPIView):
    serializer_class = NotificationSerializer
    permission_classes = (IsActiveSchoolUser,)
    def get_queryset(self):
        return notifications_for_membership(get_active_membership(self.request))


class NotificationReadAPIView(NotificationDetailAPIView):
    throttle_scope = 'notification_read'
    @extend_schema(request=None, responses={200: NotificationSerializer})
    def post(self, request, *args, **kwargs):
        return Response(NotificationSerializer(mark_notification_read(notification=self.get_object())).data)


class NotificationReadAllAPIView(APIView):
    permission_classes = (IsActiveSchoolUser,)
    throttle_scope = 'notification_read_all'
    @extend_schema(request=None, responses={200: NotificationReadAllSerializer})
    def post(self, request):
        return Response({'updated_count': mark_all_notifications_read(membership=get_active_membership(request))})


class NotificationUnreadCountAPIView(APIView):
    permission_classes = (IsActiveSchoolUser,)
    throttle_scope = 'notification_list'
    @extend_schema(responses={200: NotificationUnreadSerializer})
    def get(self, request):
        membership = get_active_membership(request)
        return Response({'membership_id': membership.pk, 'unread_count': get_unread_notification_count(membership)})