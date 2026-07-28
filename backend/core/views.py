from rest_framework import generics
from rest_framework.permissions import IsAuthenticated

from .models import School
from .serializers import SchoolSerializer
from .mixins import SchoolQuerySetMixin


class SchoolListAPIView(
    SchoolQuerySetMixin,
    generics.ListAPIView
):
    serializer_class = SchoolSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = School.objects.all()
        return self.get_school_queryset(queryset)