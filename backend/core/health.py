from django.db import connection
from django.db.migrations.recorder import MigrationRecorder
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView


class LivenessAPIView(APIView):
    authentication_classes = ()
    permission_classes = (AllowAny,)

    @extend_schema(responses={200: OpenApiTypes.OBJECT})
    def get(self, request):
        return Response({
            'status': 'ok',
            'service': 'school-saas-backend',
        })


class ReadinessAPIView(APIView):
    authentication_classes = ()
    permission_classes = (AllowAny,)

    @extend_schema(responses={200: OpenApiTypes.OBJECT, 503: OpenApiTypes.OBJECT})
    def get(self, request):
        try:
            with connection.cursor() as cursor:
                cursor.execute('SELECT 1')
                cursor.fetchone()
            MigrationRecorder(connection).migration_qs.exists()
        except Exception:
            return Response({
                'status': 'unavailable',
                'service': 'school-saas-backend',
            }, status=503)
        return Response({
            'status': 'ok',
            'service': 'school-saas-backend',
        })