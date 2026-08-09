# Generated for Sprint 4C — Announcements & Targeting

import core.models
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0022_communication_privacy_constraints'),
    ]

    operations = [
        migrations.AlterField(
            model_name='notification',
            name='notification_type',
            field=models.CharField(
                choices=[
                    ('homework_published', 'Homework published'),
                    ('homework_graded', 'Homework graded'),
                    ('homework_returned', 'Homework returned'),
                    ('result_published', 'Result published'),
                    ('message_received', 'Message received'),
                    ('school_reply', 'School reply'),
                    ('school_support_created', 'School support created'),
                    ('announcement_published', 'Announcement published'),
                    ('system', 'System'),
                ],
                max_length=40,
            ),
        ),
        migrations.CreateModel(
            name='Announcement',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=200)),
                ('body', models.TextField()),
                ('status', models.CharField(choices=[('draft', 'Draft'), ('published', 'Published'), ('closed', 'Closed'), ('archived', 'Archived')], default='draft', max_length=20)),
                ('priority', models.CharField(choices=[('normal', 'Normal'), ('high', 'High'), ('urgent', 'Urgent')], default='normal', max_length=20)),
                ('audience_type', models.CharField(choices=[('school', 'Entire school'), ('roles', 'Selected roles'), ('classroom', 'Classroom'), ('section', 'Section'), ('teacher_assignment', 'Teacher assignment'), ('students', 'Selected students')], default='school', max_length=30)),
                ('target_roles', models.JSONField(blank=True, default=list)),
                ('include_parents', models.BooleanField(default=False)),
                ('allow_inquiry', models.BooleanField(default=True)),
                ('published_at', models.DateTimeField(blank=True, null=True)),
                ('closed_at', models.DateTimeField(blank=True, null=True)),
                ('archived_at', models.DateTimeField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('academic_year', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='announcements', to='core.academicyear')),
                ('classroom', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='announcements', to='core.classroom')),
                ('created_by_membership', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='created_announcements', to='core.schoolmembership')),
                ('published_by_membership', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='published_announcements', to='core.schoolmembership')),
                ('school', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='announcements', to='core.school')),
                ('section', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='announcements', to='core.section')),
                ('target_students', models.ManyToManyField(blank=True, related_name='targeted_announcements', to='core.student')),
                ('teacher_assignment', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='announcements', to='core.teacherassignment')),
            ],
            options={
                'ordering': ('-published_at', '-created_at', '-id'),
                'indexes': [
                    models.Index(fields=['school', 'status', '-published_at'], name='ann_school_status_time_idx'),
                    models.Index(fields=['school', 'priority', '-created_at'], name='ann_school_priority_idx'),
                ],
            },
        ),
        migrations.CreateModel(
            name='AnnouncementAttachment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('file', models.FileField(upload_to=core.models.announcement_attachment_upload_to)),
                ('original_name', models.CharField(max_length=255)),
                ('content_type', models.CharField(max_length=150)),
                ('file_size', models.BigIntegerField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('announcement', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='attachments', to='core.announcement')),
                ('uploaded_by_membership', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='uploaded_announcement_attachments', to='core.schoolmembership')),
            ],
            options={'ordering': ('created_at', 'id')},
        ),
        migrations.CreateModel(
            name='AnnouncementReceipt',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('delivered_at', models.DateTimeField(auto_now_add=True)),
                ('read_at', models.DateTimeField(blank=True, null=True)),
                ('announcement', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='receipts', to='core.announcement')),
                ('recipient_membership', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='announcement_receipts', to='core.schoolmembership')),
            ],
            options={
                'ordering': ('-delivered_at', '-id'),
                'indexes': [models.Index(fields=['recipient_membership', 'read_at', '-delivered_at'], name='ann_receipt_member_read_idx')],
            },
        ),
        migrations.AddConstraint(
            model_name='announcement',
            constraint=models.CheckConstraint(
                condition=(
                    models.Q(status='draft', published_at__isnull=True, closed_at__isnull=True, archived_at__isnull=True)
                    | models.Q(status='published', published_at__isnull=False, closed_at__isnull=True, archived_at__isnull=True)
                    | models.Q(status='closed', published_at__isnull=False, closed_at__isnull=False, archived_at__isnull=True)
                    | models.Q(status='archived', archived_at__isnull=False)
                ),
                name='announcement_status_metadata_consistent',
            ),
        ),
        migrations.AddConstraint(
            model_name='announcementattachment',
            constraint=models.CheckConstraint(condition=models.Q(file_size__gt=0), name='announcement_attachment_size_positive'),
        ),
        migrations.AddConstraint(
            model_name='announcementreceipt',
            constraint=models.UniqueConstraint(fields=('announcement', 'recipient_membership'), name='unique_announcement_receipt_membership'),
        ),
    ]
