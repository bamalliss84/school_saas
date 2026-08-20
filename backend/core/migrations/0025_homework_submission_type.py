from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0024_timetable_daily_schedule'),
    ]

    operations = [
        migrations.AddField(
            model_name='homework',
            name='submission_type',
            field=models.CharField(
                choices=[
                    ('none', 'No electronic submission'),
                    ('text', 'Text answer'),
                    ('attachment', 'Attachment only'),
                    ('text_and_attachment', 'Text and attachment'),
                ],
                default='text',
                max_length=30,
            ),
        ),
        migrations.AddConstraint(
            model_name='homework',
            constraint=models.CheckConstraint(
                condition=models.Q(submission_type__in=(
                    'none', 'text', 'attachment', 'text_and_attachment',
                )),
                name='homework_submission_type_valid',
            ),
        ),
    ]
