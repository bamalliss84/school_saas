from django.db import migrations, models
from django.db.models import Q


def normalize_communication_metadata(apps, schema_editor):
    Conversation = apps.get_model('core', 'Conversation')
    ConversationParticipant = apps.get_model('core', 'ConversationParticipant')
    Message = apps.get_model('core', 'Message')

    # Keep records without a concrete relation free of stale IDs.
    Conversation.objects.filter(related_type__in=('', 'general')).update(related_id=None)
    Conversation.objects.exclude(related_type__in=('', 'general')).filter(
        related_id__isnull=True
    ).update(related_type='')

    # Defensive fallback for pre-hardening support rows without a category.
    Conversation.objects.filter(
        conversation_type='school_support', category=''
    ).update(category='other')

    # Normalize timestamps so the database constraints can be applied safely.
    Conversation.objects.filter(status='resolved').update(closed_at=None)
    Conversation.objects.filter(status='resolved', resolved_at__isnull=True).update(
        resolved_at=models.F('updated_at')
    )
    Conversation.objects.filter(status='closed').update(resolved_at=None)
    Conversation.objects.filter(status='closed', closed_at__isnull=True).update(
        closed_at=models.F('updated_at')
    )
    Conversation.objects.filter(status__in=('open', 'in_progress')).update(
        resolved_at=None, closed_at=None, resolution_note=''
    )

    # A participant with a leave timestamp is no longer active.
    ConversationParticipant.objects.filter(left_at__isnull=False).update(is_active=False)

    # Normalize soft-deletion metadata without deleting message content.
    Message.objects.filter(is_deleted=False).update(deleted_at=None)
    Message.objects.filter(is_deleted=True, deleted_at__isnull=True).update(
        deleted_at=models.F('created_at')
    )


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0021_notifications_messaging'),
    ]

    operations = [
        migrations.RunPython(
            normalize_communication_metadata,
            reverse_code=migrations.RunPython.noop,
        ),
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
                    ('system', 'System'),
                ],
                max_length=40,
            ),
        ),
        migrations.AddConstraint(
            model_name='conversation',
            constraint=models.CheckConstraint(
                condition=(
                    Q(related_type='', related_id__isnull=True)
                    | Q(related_type='general', related_id__isnull=True)
                    | (~Q(related_type__in=('', 'general')) & Q(related_id__isnull=False))
                ),
                name='conversation_related_metadata_consistent',
            ),
        ),
        migrations.AddConstraint(
            model_name='conversation',
            constraint=models.CheckConstraint(
                condition=~Q(conversation_type='school_support') | ~Q(category=''),
                name='school_support_category_required',
            ),
        ),
        migrations.AddConstraint(
            model_name='conversation',
            constraint=models.CheckConstraint(
                condition=(
                    Q(status='resolved', resolved_at__isnull=False, closed_at__isnull=True)
                    | Q(status='closed', resolved_at__isnull=True, closed_at__isnull=False)
                    | Q(
                        status__in=('open', 'in_progress'),
                        resolved_at__isnull=True,
                        closed_at__isnull=True,
                    )
                ),
                name='conversation_status_timestamps_consistent',
            ),
        ),
        migrations.AddConstraint(
            model_name='conversationparticipant',
            constraint=models.CheckConstraint(
                condition=(Q(is_active=True, left_at__isnull=True) | Q(is_active=False)),
                name='active_participant_has_not_left',
            ),
        ),
        migrations.AddConstraint(
            model_name='message',
            constraint=models.CheckConstraint(
                condition=(
                    Q(is_deleted=False, deleted_at__isnull=True)
                    | Q(is_deleted=True, deleted_at__isnull=False)
                ),
                name='message_deleted_metadata_consistent',
            ),
        ),
    ]
