from django.test import SimpleTestCase
from rest_framework.fields import empty

from .announcement_serializers import AnnouncementQuerySerializer
from .homework_serializers import HomeworkQuerySerializer, SubmissionQuerySerializer
from .messaging_serializers import ConversationQuerySerializer
from .notification_serializers import NotificationQuerySerializer
from .query_serializers import (
    StudentListQuerySerializer,
    TeacherAssignmentQuerySerializer,
)
from .serializer_fields import OptionalBooleanField


class OptionalBooleanQueryFieldTests(SimpleTestCase):
    def assert_omitted(self, serializer_class, *field_names):
        serializer = serializer_class(data={})
        self.assertTrue(serializer.is_valid(), serializer.errors)
        for field_name in field_names:
            self.assertNotIn(field_name, serializer.validated_data)

    def test_field_uses_non_html_empty_sentinel(self):
        self.assertIs(OptionalBooleanField.default_empty_html, empty)

    def test_announcement_unread_is_omitted(self):
        self.assert_omitted(AnnouncementQuerySerializer, 'unread')

    def test_notification_is_read_is_omitted(self):
        self.assert_omitted(NotificationQuerySerializer, 'is_read')

    def test_student_boolean_filters_are_omitted(self):
        self.assert_omitted(StudentListQuerySerializer, 'is_active', 'is_current')

    def test_teacher_current_filter_is_omitted(self):
        self.assert_omitted(TeacherAssignmentQuerySerializer, 'current')

    def test_homework_boolean_filters_are_omitted(self):
        self.assert_omitted(
            HomeworkQuerySerializer,
            'overdue',
            'has_submission',
            'graded',
            'pending_grading',
        )

    def test_submission_boolean_filters_are_omitted(self):
        self.assert_omitted(SubmissionQuerySerializer, 'graded', 'late')

    def test_conversation_boolean_filters_are_omitted(self):
        self.assert_omitted(ConversationQuerySerializer, 'unread_only', 'assigned_to_me')

    def test_explicit_false_is_preserved(self):
        serializer = AnnouncementQuerySerializer(data={'unread': 'false'})
        self.assertTrue(serializer.is_valid(), serializer.errors)
        self.assertIs(serializer.validated_data['unread'], False)
