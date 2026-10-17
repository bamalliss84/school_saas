from django.contrib.auth import get_user_model
from django.db.models import Q
from rest_framework import serializers

from .models import Parent, Student, StudentGuardian
from .services import identity

User = get_user_model()


class GuardianAdminSerializer(serializers.ModelSerializer):
    parent_id = serializers.IntegerField(source='parent.id', read_only=True)
    parent_name = serializers.CharField(source='parent.full_name', read_only=True)

    class Meta:
        model = StudentGuardian
        fields = (
            'id', 'parent_id', 'parent_name', 'relationship', 'is_primary',
            'can_receive_notifications', 'can_receive_financial_alerts', 'created_at',
        )
        read_only_fields = ('id', 'parent_id', 'parent_name', 'created_at')


class ParentAdminSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True, default='')
    account_username = serializers.CharField(write_only=True, required=False, allow_blank=True)
    account_password = serializers.CharField(write_only=True, required=False, allow_blank=True)
    student_id = serializers.IntegerField(write_only=True, required=False)
    relationship = serializers.ChoiceField(
        choices=StudentGuardian.RELATION_CHOICES, write_only=True, required=False,
    )
    is_primary = serializers.BooleanField(write_only=True, required=False, default=False)
    can_receive_notifications = serializers.BooleanField(write_only=True, required=False, default=True)
    can_receive_financial_alerts = serializers.BooleanField(write_only=True, required=False, default=True)
    children = serializers.SerializerMethodField()
    can_edit_profile = serializers.SerializerMethodField()

    class Meta:
        model = Parent
        fields = (
            'id', 'parent_code', 'full_name', 'national_id', 'phone', 'email',
            'address', 'occupation', 'workplace', 'is_active', 'created_at',
            'username', 'children', 'can_edit_profile', 'account_username',
            'account_password', 'student_id', 'relationship', 'is_primary',
            'can_receive_notifications', 'can_receive_financial_alerts',
        )
        read_only_fields = ('id', 'parent_code', 'created_at', 'username', 'children', 'can_edit_profile')

    def get_can_edit_profile(self, obj):
        school = getattr(self.context.get('request'), 'active_school', None)
        return bool(school and obj.school_id == school.pk)

    def get_children(self, obj):
        school = getattr(self.context.get('request'), 'active_school', None)
        if not school:
            return []
        links = obj.students.filter(student__enrollments__school=school).select_related('student').distinct().order_by('student__full_name')
        return [{
            'id': link.id,
            'student': {'id': link.student_id, 'student_code': link.student.student_code, 'full_name': link.student.full_name},
            'relationship': link.relationship, 'is_primary': link.is_primary,
            'can_receive_notifications': link.can_receive_notifications,
            'can_receive_financial_alerts': link.can_receive_financial_alerts,
        } for link in links]

    def validate(self, attrs):
        if self.instance:
            for field in ('account_username', 'account_password', 'student_id', 'relationship', 'is_primary', 'can_receive_notifications', 'can_receive_financial_alerts'):
                attrs.pop(field, None)
            return attrs
        username = attrs.get('account_username', '')
        password = attrs.get('account_password', '')
        if bool(username) != bool(password):
            raise serializers.ValidationError({'account_username': 'Username and password must be provided together.'})
        if username and User.objects.filter(username=username).exists():
            raise serializers.ValidationError({'account_username': 'A user with this username already exists.'})
        if not attrs.get('student_id'):
            raise serializers.ValidationError({'student_id': 'An initial student relationship is required.'})
        if not attrs.get('relationship'):
            raise serializers.ValidationError({'relationship': 'Relationship is required.'})
        return attrs

    def create(self, validated_data):
        request = self.context['request']
        student_id = validated_data.pop('student_id')
        username = validated_data.pop('account_username', '')
        password = validated_data.pop('account_password', '')
        guardian_values = {
            field: validated_data.pop(field)
            for field in ('relationship', 'is_primary', 'can_receive_notifications', 'can_receive_financial_alerts')
        }
        student = Student.objects.filter(pk=student_id).first()
        if student is None:
            raise serializers.ValidationError({'student_id': 'Student was not found.'})
        return identity.create_parent_with_guardian(
            school=request.active_school, student=student, parent_values=validated_data,
            guardian_values=guardian_values, account_username=username or None,
            account_password=password or None,
        )


class GuardianWriteSerializer(serializers.ModelSerializer):
    parent_id = serializers.IntegerField(write_only=True, required=False)

    class Meta:
        model = StudentGuardian
        fields = (
            'id', 'parent_id', 'relationship', 'is_primary',
            'can_receive_notifications', 'can_receive_financial_alerts',
        )
        read_only_fields = ('id',)

    def validate(self, attrs):
        if not self.instance and not attrs.get('parent_id'):
            raise serializers.ValidationError({'parent_id': 'Parent is required.'})
        return attrs

    def create(self, validated_data):
        parent_id = validated_data.pop('parent_id')
        request = self.context['request']
        # Parents owned elsewhere are visible only through another local child.
        visible = Parent.objects.filter(pk=parent_id).filter(
            Q(school=request.active_school)
            | Q(students__student__enrollments__school=request.active_school)
        ).distinct()
        parent = visible.first()
        if parent is None:
            from rest_framework.exceptions import NotFound
            raise NotFound('Parent was not found.')
        return identity.create_guardian_link(
            parent=parent, student=self.context['student'], school=request.active_school,
            **validated_data,
        )

    def update(self, instance, validated_data):
        validated_data.pop('parent_id', None)
        return identity.update_guardian_link(
            guardian=instance, school=self.context['request'].active_school, **validated_data,
        )
