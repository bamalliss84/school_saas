from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver

from core.models import ExamResult, ExamResultLog


@receiver(pre_save, sender=ExamResult)
def cache_old_exam_result(sender, instance, **kwargs):
    if not instance.pk:
        return

    try:
        old = ExamResult.objects.get(pk=instance.pk)
    except ExamResult.DoesNotExist:
        return

    instance._old_score = old.score
    instance._old_status = old.status


@receiver(post_save, sender=ExamResult)
def create_exam_result_log(sender, instance, created, **kwargs):
    if created:
        return

    old_score = getattr(instance, "_old_score", None)
    old_status = getattr(instance, "_old_status", None)

    if (
        old_score != instance.score or
        old_status != instance.status
    ):
        ExamResultLog.objects.create(
            exam_result=instance,
            old_score=old_score,
            new_score=instance.score,
            old_status=old_status,
            new_status=instance.status,
            changed_by=instance.graded_by,
            reason="Automatic change tracking",
        )