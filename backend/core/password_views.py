"""Password reset (anonymous) and password change (signed-in) endpoints."""

from drf_spectacular.utils import extend_schema
from rest_framework import serializers, status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .permissions import IsActiveSchoolUser
from .services import password_reset

GENERIC_RESET_MESSAGE = (
    'إذا كان الحساب موجودًا ومرتبطًا ببريد إلكتروني، فستصلك رسالة فيها رابط إعادة التعيين. '
    'إذا لم يكن لحسابك بريد، فاطلب من إدارة المدرسة إعادة تعيين كلمة المرور.'
)


class PasswordResetRequestSerializer(serializers.Serializer):
    identifier = serializers.CharField(max_length=254)


class PasswordResetConfirmSerializer(serializers.Serializer):
    uid = serializers.CharField(max_length=64)
    token = serializers.CharField(max_length=128)
    new_password = serializers.CharField(max_length=128, trim_whitespace=False)


class PasswordChangeSerializer(serializers.Serializer):
    current_password = serializers.CharField(max_length=128, trim_whitespace=False)
    new_password = serializers.CharField(max_length=128, trim_whitespace=False)


class PasswordResetRequestAPIView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []
    throttle_scope = 'password_reset'

    @extend_schema(request=PasswordResetRequestSerializer, responses={200: None})
    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        password_reset.request_password_reset(serializer.validated_data['identifier'])
        return Response({'detail': GENERIC_RESET_MESSAGE})


class PasswordResetConfirmAPIView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []
    throttle_scope = 'password_reset'

    @extend_schema(request=PasswordResetConfirmSerializer, responses={200: None})
    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        password_reset.confirm_password_reset(**serializer.validated_data)
        return Response({'detail': 'تم تغيير كلمة المرور. سجّل الدخول بكلمة المرور الجديدة.'})


class PasswordChangeAPIView(APIView):
    """Personal account action; allowed in historical contexts like logout."""

    permission_classes = [IsActiveSchoolUser]
    throttle_scope = 'password_change'

    @extend_schema(request=PasswordChangeSerializer, responses={200: None})
    def post(self, request):
        serializer = PasswordChangeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        password_reset.change_password(request.user, **serializer.validated_data)
        return Response(
            {'detail': 'تم تغيير كلمة المرور. سجّل الدخول من جديد على أجهزتك الأخرى.'},
            status=status.HTTP_200_OK,
        )
