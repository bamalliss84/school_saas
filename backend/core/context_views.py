from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .context import get_active_membership, get_user_memberships
from .context_serializers import (
    ContextListSerializer, DefaultContextSerializer, SchoolMembershipSerializer,
)
from .permissions import IsActiveSchoolUser


class ContextListAPIView(APIView):
    permission_classes = (IsActiveSchoolUser,)

    @extend_schema(responses={200: ContextListSerializer})
    def get(self, request):
        memberships = get_user_memberships(request.user)
        current = get_active_membership(request)
        payload = {
            'current_context': SchoolMembershipSerializer(
                current, context={'request': request},
            ).data if current else None,
            'contexts': SchoolMembershipSerializer(
                memberships, many=True, context={'request': request},
            ).data,
        }
        return Response(payload)


class CurrentContextAPIView(APIView):
    permission_classes = (IsActiveSchoolUser,)

    @extend_schema(responses={200: SchoolMembershipSerializer})
    def get(self, request):
        membership = get_active_membership(request)
        return Response(SchoolMembershipSerializer(
            membership, context={'request': request},
        ).data if membership else None)


class DefaultContextAPIView(APIView):
    permission_classes = (IsActiveSchoolUser,)

    @extend_schema(request=DefaultContextSerializer, responses={200: SchoolMembershipSerializer})
    def post(self, request):
        serializer = DefaultContextSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        membership = serializer.save()
        return Response(
            SchoolMembershipSerializer(membership, context={'request': request}).data,
            status=status.HTTP_200_OK,
        )